from typing import Annotated, TypedDict, List, Dict, Any, Optional
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from langchain_community.agent_toolkits import PlayWrightBrowserToolkit
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver
from langgraph.prebuilt import ToolNode
from langgraph.graph.message import add_messages
from playwright.async_api import async_playwright
from pydantic import BaseModel, Field
from flask import Flask, request, jsonify
import asyncio
import threading
import uuid
from dotenv import load_dotenv

load_dotenv(override=True)

# ── Background asyncio event loop ──────────────────────────────────────────
# All async LangGraph/Playwright operations run in this dedicated loop so that
# Flask's synchronous request threads can safely call async code.
_async_loop = asyncio.new_event_loop()
threading.Thread(target=_async_loop.run_forever, daemon=True, name="async-worker").start()


def run_async(coro, timeout: int = 300):
    """Submit a coroutine to the background event loop and block until done."""
    future = asyncio.run_coroutine_threadsafe(coro, _async_loop)
    return future.result(timeout=timeout)


# --- Structured Output Schema ---

class EvaluatorOutput(BaseModel):
    feedback: str = Field(description="Feedback on the assistant's response")
    success_criteria_met: bool = Field(description="Whether the success criteria have been met")
    user_input_needed: bool = Field(
        description="True if more input is needed from the user, or clarifications, or the assistant is stuck"
    )


# --- State ---

class State(TypedDict):
    messages: Annotated[List[Any], add_messages]
    success_criteria: str
    feedback_on_work: Optional[str]
    success_criteria_met: bool
    user_input_needed: bool


# --- Lazy-initialized globals ---

_graph = None
_graph_lock = asyncio.Lock()

# Set once during async initialization
_worker_llm_with_tools = None
_evaluator_llm_with_output = None


async def get_graph():
    global _graph, _worker_llm_with_tools, _evaluator_llm_with_output
    if _graph is not None:
        return _graph
    async with _graph_lock:
        if _graph is not None:
            return _graph

        pw = await async_playwright().start()
        browser = await pw.chromium.launch(
            headless=True,
            args=[
                "--no-sandbox",
                "--disable-dev-shm-usage",
                "--disable-setuid-sandbox",
                "--disable-gpu",
            ],
        )
        toolkit = PlayWrightBrowserToolkit.from_browser(async_browser=browser)
        tools = toolkit.get_tools()

        _worker_llm_with_tools = ChatOpenAI(model="gpt-4o-mini").bind_tools(tools)
        _evaluator_llm_with_output = (
            ChatOpenAI(model="gpt-4o-mini").with_structured_output(EvaluatorOutput)
        )

        _graph = _build_graph(tools)
    return _graph


# --- Graph Nodes ---

def worker(state: State) -> Dict[str, Any]:
    system_message = f"""You are a helpful web research assistant with access to a real browser.
You MUST use your browser tools to complete tasks — never say you "cannot retrieve" or "don't have access" to information.
You have these browser tools available:
- navigate_browser: go to any URL
- extract_text: extract visible text from the current page
- get_elements: find elements on the page
- click_element: click buttons/links
- current_page: check the current URL

For ANY question involving real-time data (weather, flights, prices, news, sports scores, etc.):
1. IMMEDIATELY call navigate_browser to go to a relevant website (e.g. google.com, weather.com, makemytrip.com, etc.)
2. Use extract_text to read the page content
3. Navigate further if needed to find the answer
4. Only reply with your final answer once you have browsed and found the information

NEVER respond with "I cannot access real-time data" or "I don't have the ability to browse" — you DO have a browser. Use it.
NEVER redirect the user to external websites — YOU visit those websites yourself and report back.

This is the success criteria:
{state['success_criteria']}

Reply with a question only if genuinely unclear. Otherwise browse and answer.
"""

    if state.get("feedback_on_work"):
        system_message += f"""
Previously your response was rejected. Feedback:
{state['feedback_on_work']}
You MUST use the browser tools this time. Navigate to a real website and extract the information."""

    found_system_message = False
    messages = state["messages"]
    for message in messages:
        if isinstance(message, SystemMessage):
            message.content = system_message
            found_system_message = True

    if not found_system_message:
        messages = [SystemMessage(content=system_message)] + messages

    response = _worker_llm_with_tools.invoke(messages)
    return {"messages": [response]}


def worker_router(state: State) -> str:
    last_message = state["messages"][-1]
    if hasattr(last_message, "tool_calls") and last_message.tool_calls:
        print(f"[worker_router] Tool calls: {[tc['name'] for tc in last_message.tool_calls]}")
        return "tools"
    print("[worker_router] No tool calls — routing to evaluator")
    return "evaluator"


def format_conversation(messages: List[Any]) -> str:
    conversation = "Conversation history:\n\n"
    for message in messages:
        if isinstance(message, HumanMessage):
            conversation += f"User: {message.content}\n"
        elif isinstance(message, AIMessage):
            text = message.content or "[Tools use]"
            conversation += f"Assistant: {text}\n"
    return conversation


def evaluator(state: State) -> State:
    last_response = state["messages"][-1].content

    system_message = """You are an evaluator that determines if a task has been completed successfully by an Assistant.
Assess the Assistant's last response based on the given criteria. Respond with your feedback, and with your decision on whether the success criteria has been met,
and whether more input is needed from the user."""

    user_message = f"""You are evaluating a conversation between the User and Assistant. You decide what action to take based on the last response from the Assistant.

The entire conversation with the assistant, with the user's original request and all replies, is:
{format_conversation(state['messages'])}

The success criteria for this assignment is:
{state['success_criteria']}

And the final response from the Assistant that you are evaluating is:
{last_response}

Respond with your feedback, and decide if the success criteria is met by this response.
Also, decide if more user input is required, either because the assistant has a question, needs clarification, or seems to be stuck and unable to answer without help.
"""
    if state["feedback_on_work"]:
        user_message += f"Also, note that in a prior attempt from the Assistant, you provided this feedback: {state['feedback_on_work']}\n"
        user_message += "If you're seeing the Assistant repeating the same mistakes, then consider responding that user input is required."

    evaluator_messages = [SystemMessage(content=system_message), HumanMessage(content=user_message)]
    eval_result = _evaluator_llm_with_output.invoke(evaluator_messages)

    return {
        "messages": [{"role": "assistant", "content": f"Evaluator Feedback on this answer: {eval_result.feedback}"}],
        "feedback_on_work": eval_result.feedback,
        "success_criteria_met": eval_result.success_criteria_met,
        "user_input_needed": eval_result.user_input_needed,
    }


def route_based_on_evaluation(state: State) -> str:
    if state["success_criteria_met"] or state["user_input_needed"]:
        return "END"
    return "worker"


# --- Build Graph ---

def _build_graph(tools):
    graph_builder = StateGraph(State)

    graph_builder.add_node("worker", worker)
    graph_builder.add_node("tools", ToolNode(tools=tools))
    graph_builder.add_node("evaluator", evaluator)

    graph_builder.add_conditional_edges("worker", worker_router, {"tools": "tools", "evaluator": "evaluator"})
    graph_builder.add_edge("tools", "worker")
    graph_builder.add_conditional_edges("evaluator", route_based_on_evaluation, {"worker": "worker", "END": END})
    graph_builder.add_edge(START, "worker")

    memory = MemorySaver()
    return graph_builder.compile(checkpointer=memory)


# ── Flask App ──────────────────────────────────────────────────────────────

def make_thread_id() -> str:
    return str(uuid.uuid4())


async def process_message(message: str, success_criteria: str, history: List[Dict], thread: str) -> List[Dict]:
    """Invoke the LangGraph agent and return the updated message history."""
    graph = await get_graph()
    config = {"configurable": {"thread_id": thread}}
    state = {
        "messages": message,
        "success_criteria": success_criteria,
        "feedback_on_work": None,
        "success_criteria_met": False,
        "user_input_needed": False,
    }
    result = await graph.ainvoke(state, config=config)
    user_msg     = {"role": "user",      "content": message}
    reply_msg    = {"role": "assistant", "content": result["messages"][-2].content}
    feedback_msg = {"role": "assistant", "content": result["messages"][-1].content}
    return history + [user_msg, reply_msg, feedback_msg]


app = Flask(__name__)


@app.route("/health", methods=["GET"])
def health():
    """Liveness probe."""
    return jsonify({"status": "ok", "service": "sidekick-agent"})


@app.route("/api/chat", methods=["POST"])
def chat():
    """
    Send a message to the Sidekick agent.

    Request JSON:
        message          (str, required)  – user's request
        success_criteria (str, optional)  – what counts as a good answer
        history          (list, optional) – prior messages from /api/chat responses
        thread_id        (str, optional)  – conversation ID (new one created if omitted)

    Response JSON:
        thread_id (str)   – use this in subsequent requests for multi-turn conversation
        messages  (list)  – full conversation history including the new exchange
    """
    data = request.get_json(force=True) or {}
    message          = (data.get("message") or "").strip()
    success_criteria = (data.get("success_criteria") or "").strip()
    history          = data.get("history") or []
    thread_id        = data.get("thread_id") or make_thread_id()

    if not message:
        return jsonify({"error": "message is required"}), 400

    try:
        messages = run_async(process_message(message, success_criteria, history, thread_id))
        return jsonify({"thread_id": thread_id, "messages": messages})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/reset", methods=["POST"])
def reset_thread():
    """Return a fresh thread ID to start a new conversation."""
    return jsonify({"thread_id": make_thread_id()})


if __name__ == "__main__":
    print("Starting Sidekick Flask server on http://0.0.0.0:7860")
    app.run(host="0.0.0.0", port=7860, debug=False, threaded=True)
