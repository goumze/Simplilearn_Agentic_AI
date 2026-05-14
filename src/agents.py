"""
Agents module for Banking Customer Support AI Agent.
Contains: ClassifierAgent, FeedbackHandlerAgent, QueryHandlerAgent.
"""

import os
import re
import logging
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage

from database import generate_ticket_id, create_ticket, get_ticket

logger = logging.getLogger(__name__)

OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")


def _get_llm() -> ChatOpenAI:
    return ChatOpenAI(model=OPENAI_MODEL, temperature=0.3)


# ---------------------------------------------------------------------------
# Classifier Agent
# ---------------------------------------------------------------------------

CLASSIFIER_SYSTEM_PROMPT = """You are a customer support message classifier for a bank.
Classify the user message into exactly one of the following categories:
- positive_feedback: The user is happy and expressing satisfaction.
- negative_feedback: The user is unhappy, complaining, or reporting an issue.
- query: The user is asking for information, such as a ticket status.

If past conversation context is provided below, use it to improve accuracy
(e.g., if a prior similar message was classified as a query, weight that signal).

Respond with only the category name (no punctuation, no explanation):
positive_feedback | negative_feedback | query"""


def classifier_agent(user_message: str, rag_context: str = "") -> str:
    """
    Classify the user message.
    Optionally uses RAG context from similar past conversations.
    Returns one of: 'positive_feedback', 'negative_feedback', 'query'.
    """
    llm = _get_llm()
    system_content = CLASSIFIER_SYSTEM_PROMPT
    if rag_context:
        system_content = f"{CLASSIFIER_SYSTEM_PROMPT}\n\n{rag_context}"
    messages = [
        SystemMessage(content=system_content),
        HumanMessage(content=user_message),
    ]
    response = llm.invoke(messages)
    classification = response.content.strip().lower()

    valid = {"positive_feedback", "negative_feedback", "query"}
    if classification not in valid:
        # Fallback: keyword-based heuristic
        lower = user_message.lower()
        if any(w in lower for w in ["thank", "great", "excellent", "happy", "good", "wonderful", "resolved"]):
            classification = "positive_feedback"
        elif re.search(r"\b\d{6}\b", lower) or any(w in lower for w in ["status", "check", "ticket"]):
            classification = "query"
        else:
            classification = "negative_feedback"

    logger.info("Classifier: '%s' -> %s", user_message[:60], classification)
    return classification


# ---------------------------------------------------------------------------
# Feedback Handler Agent
# ---------------------------------------------------------------------------

POSITIVE_FEEDBACK_SYSTEM_PROMPT = """You are a warm and professional customer support agent for a bank.
The customer has just sent positive feedback. Write a brief, sincere thank-you response (1-2 sentences).
Address the customer personally if their name is provided, otherwise use a generic greeting.
Keep the tone warm, professional, and appreciative.
If past similar interactions are provided below, use them only as style/tone reference."""

NEGATIVE_FEEDBACK_SYSTEM_PROMPT = """You are an empathetic customer support agent for a bank.
A new support ticket has been created for the customer's complaint.
Write a short, empathetic apology message (1-2 sentences) and include the placeholder {{TICKET_ID}}
exactly as shown so it can be replaced with the actual ticket number.
Do not add any other placeholders.
If past similar complaints are provided below, acknowledge the pattern without referencing specific prior customers."""


def feedback_handler_agent(
    user_message: str,
    classification: str,
    customer_name: str = "Valued Customer",
    rag_context: str = "",
) -> dict:
    """
    Handle positive or negative feedback.
    Optionally uses RAG context from similar past conversations.
    Returns dict with keys: response, ticket_id (None for positive feedback).
    """
    llm = _get_llm()

    if classification == "positive_feedback":
        system_content = POSITIVE_FEEDBACK_SYSTEM_PROMPT
        if rag_context:
            system_content = f"{POSITIVE_FEEDBACK_SYSTEM_PROMPT}\n\n{rag_context}"
        messages = [
            SystemMessage(content=system_content),
            HumanMessage(content=f"Customer name: {customer_name}\nFeedback: {user_message}"),
        ]
        response = llm.invoke(messages)
        return {"response": response.content.strip(), "ticket_id": None}

    else:  # negative_feedback
        ticket_id = generate_ticket_id()
        create_ticket(ticket_id, customer_name, user_message)

        system_content = NEGATIVE_FEEDBACK_SYSTEM_PROMPT
        if rag_context:
            system_content = f"{NEGATIVE_FEEDBACK_SYSTEM_PROMPT}\n\n{rag_context}"
        messages = [
            SystemMessage(content=system_content),
            HumanMessage(content=f"Customer complaint: {user_message}"),
        ]
        llm_response = llm.invoke(messages)
        raw = llm_response.content.strip()
        response_text = raw.replace("{{TICKET_ID}}", f"#{ticket_id}")

        # Ensure ticket number appears in message even if LLM ignored placeholder
        if ticket_id not in response_text:
            response_text = (
                f"We apologize for the inconvenience. A new ticket #{ticket_id} has been generated, "
                "and our team will follow up shortly."
            )

        logger.info("Negative feedback handler: created ticket %s", ticket_id)
        return {"response": response_text, "ticket_id": ticket_id}


# ---------------------------------------------------------------------------
# Query Handler Agent
# ---------------------------------------------------------------------------

def _extract_ticket_number(text: str) -> str | None:
    """Extract a 6-digit ticket number from text."""
    match = re.search(r"\b(\d{6})\b", text)
    return match.group(1) if match else None


def query_handler_agent(user_message: str, rag_context: str = "") -> dict:
    """
    Handle a ticket status query.
    Optionally uses RAG context to surface related past ticket interactions.
    Returns dict with keys: response, ticket_id.
    """
    ticket_id = _extract_ticket_number(user_message)

    if not ticket_id:
        return {
            "response": (
                "I'm sorry, I couldn't find a ticket number in your message. "
                "Please provide your 6-digit ticket number so I can check the status for you."
            ),
            "ticket_id": None,
        }

    ticket = get_ticket(ticket_id)

    if ticket is None:
        return {
            "response": (
                f"I'm sorry, ticket #{ticket_id} was not found in our system. "
                "Please verify the ticket number and try again."
            ),
            "ticket_id": ticket_id,
        }

    status = ticket["status"]
    response = f"Your ticket #{ticket_id} is currently marked as: {status}."
    logger.info("Query handler: ticket %s -> %s", ticket_id, status)
    return {"response": response, "ticket_id": ticket_id}
