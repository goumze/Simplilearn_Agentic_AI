"""
agent.py — LangGraph Q&A Agent

Architecture
------------
This implementation models the agent as a directed StateGraph:

         ┌─────────────────────────────────┐
         │                                 │
  START ──► [ agent node ]                 │
              │         │                  │
        no tool    tool call               │
        calls?     needed?                 │
              │         │                  │
             END   [ tools node ] ─────────┘
                   (executes tool
                    and appends
                    ToolMessage to
                    state)

State: a TypedDict holding the list of messages exchanged so far.
Every node reads the current state and returns a dict of state updates
(which are merged/reduced via operator.add for the messages list).

Key LangGraph concepts shown:
  - StateGraph + TypedDict state
  - Nodes as plain Python functions
  - Conditional edges (should_continue) for dynamic routing
  - Cycles: the agent can loop back through tools multiple times
  - ToolNode from langgraph.prebuilt for automatic tool dispatch
  - graph.compile() to produce a runnable
"""

import os
import sys
import operator
from typing import Annotated, Sequence, TypedDict

from langchain_core.messages import AIMessage, BaseMessage, HumanMessage
from langchain_openai import ChatOpenAI
from langgraph.graph import END, START, StateGraph
from langgraph.prebuilt import ToolNode

from tools import calculator, get_current_date, knowledge_base_lookup, word_counter


# ---------------------------------------------------------------------------
# 1. State definition
#    The Annotated[..., operator.add] reducer means new messages are
#    *appended* to the existing list rather than replacing it.
# ---------------------------------------------------------------------------
class AgentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], operator.add]


# ---------------------------------------------------------------------------
# 2. Nodes
# ---------------------------------------------------------------------------
TOOLS = [calculator, get_current_date, knowledge_base_lookup, word_counter]

_LLM = ChatOpenAI(model="gpt-4o-mini", temperature=0)
_LLM_WITH_TOOLS = _LLM.bind_tools(TOOLS)


def agent_node(state: AgentState) -> dict:
    """Call the LLM (with tools bound) and return the response message."""
    response: AIMessage = _LLM_WITH_TOOLS.invoke(state["messages"])
    return {"messages": [response]}


# ToolNode automatically calls the right tool based on the AIMessage's
# tool_calls field and appends a ToolMessage for each result.
tool_node = ToolNode(TOOLS)


# ---------------------------------------------------------------------------
# 3. Conditional edge — decide whether to execute a tool or stop
# ---------------------------------------------------------------------------
def should_continue(state: AgentState) -> str:
    """Route to 'tools' if the last AI message contains tool calls, else END."""
    last_message = state["messages"][-1]
    if isinstance(last_message, AIMessage) and last_message.tool_calls:
        return "tools"
    return END


# ---------------------------------------------------------------------------
# 4. Build the graph
# ---------------------------------------------------------------------------
def build_graph():
    graph = StateGraph(AgentState)

    graph.add_node("agent", agent_node)
    graph.add_node("tools", tool_node)

    graph.add_edge(START, "agent")

    # After the agent runs, check whether tool calls are needed
    graph.add_conditional_edges(
        "agent",
        should_continue,
        {"tools": "tools", END: END},
    )

    # After tools run, always go back to the agent so it can respond
    graph.add_edge("tools", "agent")

    return graph.compile()


# ---------------------------------------------------------------------------
# Predefined test cases
# ---------------------------------------------------------------------------
TEST_CASES = [
    "What is the square root of 256?",
    "What is today's date?",
    "Tell me about LangGraph.",
    "How many words are in the sentence: 'The quick brown fox jumps over the lazy dog'?",
    "Calculate (15 * 23) + round(sqrt(81))",
    "What is Agentic AI?",
]


def run_test_cases() -> None:
    print("\n" + "=" * 65)
    print("  LangGraph StateGraph Agent — Q&A with Tool Use")
    print("=" * 65)
    print(
        "\n  Graph topology:\n"
        "    START ──► agent ──► (tool calls?) ──► tools ──┐\n"
        "                │                                  │\n"
        "               END ◄─────────────────────────────┘\n"
        "                   (no more tool calls)\n"
    )

    app = build_graph()

    for idx, question in enumerate(TEST_CASES, start=1):
        print(f"{'─' * 65}")
        print(f"  Test {idx}/{len(TEST_CASES)}: {question}")
        print("─" * 65)

        # Print each step as the graph streams through nodes
        step_num = 0
        final_answer = ""
        for step in app.stream(
            {"messages": [HumanMessage(content=question)]},
            stream_mode="values",
        ):
            last_msg = step["messages"][-1]
            step_num += 1

            if isinstance(last_msg, AIMessage):
                if last_msg.tool_calls:
                    calls = ", ".join(tc["name"] for tc in last_msg.tool_calls)
                    print(f"    [Step {step_num}] Agent → calling tool(s): {calls}")
                else:
                    final_answer = last_msg.content
            else:
                # ToolMessage — show which tool returned what
                tool_name = getattr(last_msg, "name", "tool")
                print(f"    [Step {step_num}] Tool '{tool_name}' returned: {last_msg.content[:120]}")

        print(f"\n  ✔  Final Answer: {final_answer}\n")

    print("=" * 65)
    print("  All test cases completed.")
    print("=" * 65 + "\n")


if __name__ == "__main__":
    api_key = os.environ.get("OPENAI_API_KEY", "")
    if not api_key:
        print(
            "[ERROR] OPENAI_API_KEY environment variable is not set.\n"
            "        Export it before running:\n"
            "          export OPENAI_API_KEY='sk-...'\n"
        )
        sys.exit(1)

    run_test_cases()
