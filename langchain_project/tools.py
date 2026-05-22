"""
tools.py — Shared tools used by the LangChain Q&A Agent.

Tools provided:
  - calculator          : Evaluate a math expression safely
  - get_current_date    : Return today's date and time
  - knowledge_base_lookup : Look up a topic from an in-memory knowledge base
  - word_counter        : Count words in a piece of text
"""

import ast
import math
import operator as op
from datetime import datetime

from langchain_core.tools import tool


# ---------------------------------------------------------------------------
# Safe math evaluator (avoids exec/eval with unrestricted builtins)
# ---------------------------------------------------------------------------
_MATH_OPS = {
    ast.Add: op.add,
    ast.Sub: op.sub,
    ast.Mult: op.mul,
    ast.Div: op.truediv,
    ast.Pow: op.pow,
    ast.USub: op.neg,
    ast.UAdd: op.pos,
}

_MATH_FUNCS = {
    "sqrt": math.sqrt,
    "log": math.log,
    "log2": math.log2,
    "log10": math.log10,
    "sin": math.sin,
    "cos": math.cos,
    "tan": math.tan,
    "abs": abs,
    "round": round,
    "pi": math.pi,
    "e": math.e,
}


def _safe_eval(node):
    if isinstance(node, ast.Expression):
        return _safe_eval(node.body)
    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
        return node.value
    if isinstance(node, ast.Name) and node.id in _MATH_FUNCS:
        return _MATH_FUNCS[node.id]
    if isinstance(node, ast.BinOp) and type(node.op) in _MATH_OPS:
        return _MATH_OPS[type(node.op)](_safe_eval(node.left), _safe_eval(node.right))
    if isinstance(node, ast.UnaryOp) and type(node.op) in _MATH_OPS:
        return _MATH_OPS[type(node.op)](_safe_eval(node.operand))
    if isinstance(node, ast.Call):
        func = _safe_eval(node.func)
        args = [_safe_eval(a) for a in node.args]
        return func(*args)
    raise ValueError(f"Unsupported expression element: {ast.dump(node)}")


# ---------------------------------------------------------------------------
# Tool definitions
# ---------------------------------------------------------------------------
@tool
def calculator(expression: str) -> str:
    """Evaluate a mathematical expression and return the numeric result.
    Supports: +, -, *, /, ** (power), sqrt(), log(), sin(), cos(), tan(),
    abs(), round(), pi, e.
    Example input: 'sqrt(144)' or '15 * 23 + 100'
    """
    try:
        tree = ast.parse(expression.strip(), mode="eval")
        result = _safe_eval(tree)
        return str(result)
    except Exception as exc:
        return f"Error evaluating expression: {exc}"


@tool
def get_current_date(query: str) -> str:
    """Return the current date and time. Use this tool when the user asks about
    today's date, the current time, or what day it is. The input can be any
    string (e.g. 'now', 'today').
    """
    now = datetime.now()
    return (
        f"Current date : {now.strftime('%A, %B %d, %Y')}\n"
        f"Current time : {now.strftime('%H:%M:%S')}"
    )


@tool
def knowledge_base_lookup(topic: str) -> str:
    """Look up a topic in the knowledge base and return a short description.
    Use this tool when the user asks 'what is X' or 'tell me about X'.
    Input should be the topic name (e.g. 'LangGraph', 'Python').
    """
    kb = {
        "python": (
            "Python is a high-level, general-purpose programming language renowned for "
            "its clear syntax and readability. It supports multiple programming paradigms "
            "and has a large standard library."
        ),
        "langchain": (
            "LangChain is an open-source framework for building applications powered by "
            "large language models (LLMs). It provides chains, agents, memory, and "
            "retrieval components to compose LLM-based workflows."
        ),
        "langgraph": (
            "LangGraph is a library built on top of LangChain for creating stateful, "
            "multi-actor agentic applications. It models workflows as directed graphs "
            "(nodes + edges), supports cycles, and enables fine-grained control over "
            "agent state and routing."
        ),
        "openai": (
            "OpenAI is an AI research organisation that created the GPT series of large "
            "language models, the DALL-E image-generation models, and the ChatGPT "
            "conversational AI product."
        ),
        "machine learning": (
            "Machine learning is a branch of artificial intelligence in which systems "
            "learn patterns from data and improve their performance without being "
            "explicitly programmed for each task."
        ),
        "deep learning": (
            "Deep learning is a subset of machine learning that uses neural networks with "
            "many layers (deep neural networks) to learn hierarchical representations of "
            "data, excelling at tasks like image recognition and natural language "
            "understanding."
        ),
        "llm": (
            "Large Language Models (LLMs) are AI models trained on vast text corpora "
            "to understand and generate human-like text. Examples include GPT-4, Claude, "
            "Gemini, and Llama."
        ),
        "agentic ai": (
            "Agentic AI refers to AI systems that can autonomously plan, make decisions, "
            "use tools, and take sequences of actions to accomplish complex goals with "
            "minimal human intervention."
        ),
    }
    topic_lower = topic.lower().strip()
    for key, description in kb.items():
        if key in topic_lower or topic_lower in key:
            return description
    return (
        f"No entry found for '{topic}' in the knowledge base. "
        "Try a different keyword such as: python, langchain, langgraph, openai, "
        "machine learning, deep learning, llm, agentic ai."
    )


@tool
def word_counter(text: str) -> str:
    """Count the number of words in a given piece of text.
    Input should be the text whose words you want to count.
    Example input: 'The quick brown fox jumps over the lazy dog'
    """
    count = len(text.split())
    return f"The provided text contains {count} word(s)."
