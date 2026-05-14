"""
LangGraph workflow for Banking Customer Support AI Agent.
Defines state, nodes, and edges for the multi-agent graph.
"""

import logging
from typing import TypedDict, Literal
from langgraph.graph import StateGraph, END

from agents import classifier_agent, feedback_handler_agent, query_handler_agent
from database import log_interaction
from rag import retrieve_similar, store_conversation, format_rag_context

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# State definition
# ---------------------------------------------------------------------------

class SupportState(TypedDict):
    user_message: str
    customer_name: str
    classification: str          # positive_feedback | negative_feedback | query
    response: str
    ticket_id: str | None
    agent_used: str
    success: bool
    rag_context: str             # formatted context block from similar past conversations
    rag_hits: list[dict]         # raw retrieved records (for UI / logging)


# ---------------------------------------------------------------------------
# Node functions
# ---------------------------------------------------------------------------

def rag_retrieve_node(state: SupportState) -> SupportState:
    """
    RAG Retrieval node: embed the incoming message and fetch the most
    semantically similar past conversations from LanceDB (FAISS index).
    The formatted context is stored in state for downstream agents.
    """
    similar = retrieve_similar(state["user_message"])
    context = format_rag_context(similar)
    logger.info("RAG: injecting %d similar conversation(s) as context", len(similar))
    return {**state, "rag_hits": similar, "rag_context": context}


def classify_node(state: SupportState) -> SupportState:
    """Classifier Agent node: classify the incoming message."""
    classification = classifier_agent(state["user_message"], rag_context=state.get("rag_context", ""))
    return {**state, "classification": classification}


def feedback_node(state: SupportState) -> SupportState:
    """Feedback Handler Agent node: handle positive or negative feedback."""
    result = feedback_handler_agent(
        state["user_message"],
        state["classification"],
        state.get("customer_name", "Valued Customer"),
        rag_context=state.get("rag_context", ""),
    )
    return {
        **state,
        "response": result["response"],
        "ticket_id": result["ticket_id"],
        "agent_used": "FeedbackHandlerAgent",
        "success": True,
    }


def query_node(state: SupportState) -> SupportState:
    """Query Handler Agent node: handle ticket status queries."""
    result = query_handler_agent(state["user_message"], rag_context=state.get("rag_context", ""))
    return {
        **state,
        "response": result["response"],
        "ticket_id": result["ticket_id"],
        "agent_used": "QueryHandlerAgent",
        "success": True,
    }


def log_node(state: SupportState) -> SupportState:
    """Logging node: persist the interaction to the SQLite database."""
    log_interaction(
        user_message=state["user_message"],
        classification=state["classification"],
        agent_used=state.get("agent_used", "Unknown"),
        response=state.get("response", ""),
        ticket_id=state.get("ticket_id"),
        success=state.get("success", True),
    )
    return state


def rag_store_node(state: SupportState) -> SupportState:
    """
    RAG Storage node: embed and persist the completed conversation to LanceDB.
    Runs after logging so every successful interaction is retrievable in future.
    Triggers FAISS IVF-PQ index rebuild when the record threshold is crossed.
    """
    store_conversation(state)
    return state


# ---------------------------------------------------------------------------
# Routing function
# ---------------------------------------------------------------------------

def route_after_classification(
    state: SupportState,
) -> Literal["feedback_node", "query_node"]:
    """Route to the appropriate downstream agent based on classification."""
    if state["classification"] in ("positive_feedback", "negative_feedback"):
        return "feedback_node"
    return "query_node"


# ---------------------------------------------------------------------------
# Build the graph
# ---------------------------------------------------------------------------

def build_graph() -> StateGraph:
    graph = StateGraph(SupportState)

    # Add nodes
    graph.add_node("rag_retrieve_node", rag_retrieve_node)
    graph.add_node("classify_node",     classify_node)
    graph.add_node("feedback_node",     feedback_node)
    graph.add_node("query_node",        query_node)
    graph.add_node("log_node",          log_node)
    graph.add_node("rag_store_node",    rag_store_node)

    # Entry point: retrieve context first, then classify
    graph.set_entry_point("rag_retrieve_node")
    graph.add_edge("rag_retrieve_node", "classify_node")

    # Conditional routing after classification
    graph.add_conditional_edges(
        "classify_node",
        route_after_classification,
        {
            "feedback_node": "feedback_node",
            "query_node":    "query_node",
        },
    )

    # Both agents converge → log → store in RAG → END
    graph.add_edge("feedback_node", "log_node")
    graph.add_edge("query_node",    "log_node")
    graph.add_edge("log_node",      "rag_store_node")
    graph.add_edge("rag_store_node", END)

    return graph.compile()


# Compiled graph (singleton)
support_graph = build_graph()


# ---------------------------------------------------------------------------
# Public helper
# ---------------------------------------------------------------------------

def run_support_agent(user_message: str, customer_name: str = "Valued Customer") -> SupportState:
    """
    Run the full multi-agent workflow for a given user message.
    Returns the final state dict.
    """
    initial_state: SupportState = {
        "user_message":  user_message,
        "customer_name": customer_name,
        "classification": "",
        "response":      "",
        "ticket_id":     None,
        "agent_used":    "",
        "success":       False,
        "rag_context":   "",
        "rag_hits":      [],
    }
    final_state = support_graph.invoke(initial_state)
    return final_state
