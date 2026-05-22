"""
agent.py — LangChain Q&A Agent  (LangChain 1.x / LCEL approach)

Architecture
------------
In LangChain 1.x the legacy AgentExecutor has been removed. This
implementation uses the modern LCEL tool-calling loop:

  User question
       │
       ▼
  HumanMessage ──► ChatOpenAI.bind_tools() ──► AIMessage
                          │
                   tool_calls present?
                    Yes │         │ No
                        ▼         ▼
                   call tools   return
                   (ToolMessage)  answer
                        │
                        └──► ChatOpenAI again … (repeat)

Key LangChain concepts shown:
  - @tool decorator (langchain_core.tools)
  - llm.bind_tools() to register tools with the model
  - Manual tool-calling loop with langchain_core messages
  - No external orchestrator — pure Python + LCEL
"""

import os
import sys
from typing import Sequence

from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, ToolMessage
from langchain_openai import ChatOpenAI

from tools import calculator, get_current_date, knowledge_base_lookup, word_counter

# ---------------------------------------------------------------------------
# Tools & LLM
# ---------------------------------------------------------------------------
TOOLS = [calculator, get_current_date, knowledge_base_lookup, word_counter]
_TOOL_MAP = {t.name: t for t in TOOLS}

_LLM = ChatOpenAI(model="gpt-4o-mini", temperature=0)
_LLM_WITH_TOOLS = _LLM.bind_tools(TOOLS)

MAX_ITERATIONS = 6


# ---------------------------------------------------------------------------
# Core agent loop  (pure LCEL — no AgentExecutor)
# ---------------------------------------------------------------------------
def run_agent(question: str, verbose: bool = True) -> str:
    """
    Run the tool-calling loop for a single question.
    Returns the final text answer from the LLM.
    """
    messages: list[BaseMessage] = [HumanMessage(content=question)]

    for iteration in range(1, MAX_ITERATIONS + 1):
        response: AIMessage = _LLM_WITH_TOOLS.invoke(messages)
        messages.append(response)

        if not response.tool_calls:
            # LLM is done — no more tool calls
            return response.content

        # Execute every requested tool call and append results
        for tc in response.tool_calls:
            tool_name = tc["name"]
            tool_args = tc["args"]
            if verbose:
                print(f"    [iter {iteration}] → tool '{tool_name}'  args={tool_args}")
            try:
                result = _TOOL_MAP[tool_name].invoke(tool_args)
            except Exception as exc:
                result = f"Error: {exc}"
            if verbose:
                print(f"    [iter {iteration}] ← result: {str(result)[:120]}")
            messages.append(
                ToolMessage(content=str(result), tool_call_id=tc["id"])
            )

    return "Max iterations reached without a final answer."


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
    print("  LangChain LCEL Agent — Q&A with Tool Use  (LangChain 1.x)")
    print("=" * 65)

    for idx, question in enumerate(TEST_CASES, start=1):
        print(f"\n{'─' * 65}")
        print(f"  Test {idx}/{len(TEST_CASES)}: {question}")
        print("─" * 65)
        try:
            answer = run_agent(question, verbose=True)
            print(f"\n  ✔  Final Answer: {answer}")
        except Exception as exc:
            print(f"\n  ✘  Error: {exc}")

    print("\n" + "=" * 65)
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

