from IPython.display import Image, display
from dotenv import load_dotenv
from langchain_community.utilities import WikipediaAPIWrapper, ArxivAPIWrapper
from langchain_community.tools import WikipediaQueryRun, ArxivQueryRun
from langchain_openai import ChatOpenAI
from langchain_tavily import TavilySearch
from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import ToolNode
from langgraph.prebuilt import tools_condition
from langchain_core.messages import AnyMessage, HumanMessage, ToolMessage
from typing import TypedDict, Annotated
from langgraph.graph.message import add_messages

load_dotenv()

# Define State Schema
class State(TypedDict):
    messages: Annotated[list[AnyMessage], add_messages]

# Initialize tools at module level for LangGraph
api_wrapper_arxiv = ArxivAPIWrapper(top_k_results=2, doc_content_chars_max=500)
arxiv = ArxivQueryRun(api_wrapper=api_wrapper_arxiv)

api_wrapper_wiki = WikipediaAPIWrapper(top_k_results=2, doc_content_chars_max=500)
wiki = WikipediaQueryRun(api_wrapper=api_wrapper_wiki)

tavily_search = TavilySearch()

# Combine all tools
tools = [arxiv, wiki, tavily_search]

# Node Definition
def tool_calling_llm(state: State):
    llm = ChatOpenAI(model_name="gpt-4")
    llm_with_tools = llm.bind_tools(tools)
    return {"messages": [llm_with_tools.invoke(state["messages"])]}

if __name__ == "__main__":
    # Build Graph
    builder = StateGraph(State)
    builder.add_node("llm", tool_calling_llm)
    builder.add_node("tools", ToolNode(tools))

    builder.add_edge(START, "llm")
    builder.add_conditional_edges("llm", tools_condition)
    builder.add_edge("tools", END)

    graph = builder.compile()

    messages = graph.invoke(
        {
            "messages": HumanMessage(
                content="Use available tools to find recent AI news from the last 7 days. After tool calls, return a concise summary with 5 bullet points and include source URLs."
            )
        }
    )
    for m in messages["messages"]:
        m.pretty_print()


