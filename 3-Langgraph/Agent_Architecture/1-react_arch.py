from langchain_community.utilities import WikipediaAPIWrapper, ArxivAPIWrapper
from langchain_community.tools import WikipediaQueryRun, ArxivQueryRun
from langchain_tavily import TavilySearch
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv
from langchain_core.messages import HumanMessage, ToolMessage
from typing_extensions import TypedDict
from typing import Annotated
from langgraph.graph.message import add_messages
from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import ToolNode
from langgraph.prebuilt import tools_condition
load_dotenv()

# Initialize tools at module level for LangGraph
api_wrapper_arxiv = ArxivAPIWrapper(top_k_results=2, doc_content_chars_max=500)
arxiv = ArxivQueryRun(api_wrapper=api_wrapper_arxiv)

api_wrapper_wiki = WikipediaAPIWrapper(top_k_results=2, doc_content_chars_max=500)
wiki = WikipediaQueryRun(api_wrapper=api_wrapper_wiki)

tavily_search = TavilySearch()

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

tools = [arxiv, wiki, tavily_search, multiply, add, subtract, divide]


def run_tools_and_respond(llm_with_tools, user_query: str) -> str:
    messages = [HumanMessage(content=user_query)]
    first_response = llm_with_tools.invoke(messages)
    print("First response:", first_response.content)

    # If the model requests tool calls, execute them and send results back.
    if first_response.tool_calls:
        print("Tool calls requested:", first_response.tool_calls)
        tool_registry = {tool.name: tool for tool in [arxiv, wiki, tavily_search]}
        tool_registry.update(
            {
                "multiply": multiply,
                "add": add,
                "subtract": subtract,
                "divide": divide,
            }
        )

        tool_messages = []
        for call in first_response.tool_calls:
            tool_name = call["name"]
            tool_args = call.get("args", {})
            tool_call_id = call["id"]

            print(f"Invoking tool: {tool_name} with args: {tool_args}")

            selected_tool = tool_registry.get(tool_name)
            if selected_tool is None:
                result = f"Tool '{tool_name}' is not registered."
            else:
                try:
                    if hasattr(selected_tool, "invoke"):
                        result = selected_tool.invoke(tool_args)
                    else:
                        result = selected_tool(**tool_args)
                except Exception as exc:
                    result = f"Tool '{tool_name}' failed with error: {exc}"

            tool_messages.append(
                ToolMessage(
                    content=str(result),
                    tool_call_id=tool_call_id,
                    name=tool_name,
                )
            )

        final_response = llm_with_tools.invoke(messages + [first_response] + tool_messages)
        return final_response.content

    return first_response.content


class State(TypedDict):
    messages: Annotated[list[HumanMessage | ToolMessage], add_messages]

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
graph = builder.compile()


if __name__ == "__main__":
    # llm = ChatOpenAI(model_name="gpt-4o")
    # llm_with_tools = llm.bind_tools(tools)

    # response_text = run_tools_and_respond(llm_with_tools, "What is latest NASDAQ news ?")
    # print("response:", response_text)

    message = graph.invoke({"messages":[HumanMessage(content="What is latest NASDAQ news ?")]})
    for m in message['messages']:
        m.pretty_print()

    message = graph.invoke({"messages":[HumanMessage(content="What is machine learning ?")]})
    for m in message['messages']:
        m.pretty_print()

    message = graph.invoke({"messages":[HumanMessage(content="Provide me the top 10 recent AI news for March 3rd 2026.")]})
    for m in message['messages']:
        m.pretty_print()

    message = graph.invoke({"messages":[HumanMessage(content="Provide me the top 10 recent AI news for March 3rd 2026, add then multiply by 10")]})
    for m in message['messages']:
        m.pretty_print()




