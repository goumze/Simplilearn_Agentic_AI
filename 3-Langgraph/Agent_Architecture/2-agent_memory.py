from langchain_openai import ChatOpenAI
from dotenv import load_dotenv
from langchain_core.messages import HumanMessage, ToolMessage
from typing_extensions import TypedDict
from typing import Annotated
from langgraph.graph.message import add_messages
from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import ToolNode
from langgraph.prebuilt import tools_condition
from langgraph.checkpoint.memory import MemorySaver

load_dotenv()


memory = MemorySaver()

class State(TypedDict):
    messages: Annotated[list[HumanMessage | ToolMessage], add_messages]

#custom functions
def multiply(a:int, b:int) -> int:
    """
    Multiplies two integers and returns the result.
    Args:
        a (int): The first integer.
        b (int): The second integer.
    Returns:
        int: The product of a and b.
    """
    return a * b

def add(a:int, b:int) -> int:
    """
    Adds two integers and returns the result.
    Args:
        a (int): The first integer.
        b (int): The second integer.
    Returns:
        int: The sum of a and b.
    """
    return a + b

def subtract(a:int, b:int) -> int:
    """
    Subtracts the second integer from the first and returns the result.
    Args:
        a (int): The first integer.
        b (int): The second integer.
    Returns:
        int: The difference of a and b.
    """
    return a - b

def divide(a:int, b:int) -> float:
    """
    Divides the first integer by the second and returns the result.
    Args:
        a (int): The numerator.
        b (int): The denominator.
    Returns:
        float: The quotient of a and b.
    Raises:
        ValueError: If the denominator is zero.
    """
    if b == 0:
        raise ValueError("Cannot divide by zero.")
    return a / b

tools = [multiply, add, subtract, divide]

llm = ChatOpenAI(model_name="gpt-4o")
llm_with_tools = llm.bind_tools(tools)

###Node Definition
def tool_calling_llm(state: State):
    return {"messages":[llm_with_tools.invoke(state["messages"])]}

#Build Graph
builder = StateGraph(State)
builder.add_node("tool_calling_llm", tool_calling_llm)
builder.add_node("tools", ToolNode(tools, handle_tool_errors=True))

builder.add_edge(START, "tool_calling_llm")
builder.add_conditional_edges(
    "tool_calling_llm",
    tools_condition,
    {
        "tools": "tools",
        "__end__": END,
    }
)
builder.add_edge("tools", "tool_calling_llm")
graph_memory = builder.compile(checkpointer=memory)

#Specify the thread
config = {"configurable": {"thread_id":"1"}}

#Specify an input
if __name__ == "__main__":
    print("\n=== First query: Add 2 and 13 ===")
    result = graph_memory.invoke({"messages": [HumanMessage(content="Add 2 and 13")]}, config=config)
    for m in result["messages"]:
        m.pretty_print()

    print("\n=== Second query: Add that number to 5 ===")
    result = graph_memory.invoke({"messages": [HumanMessage(content="Add that number to 5")]}, config=config)
    for m in result["messages"]:
        m.pretty_print()

