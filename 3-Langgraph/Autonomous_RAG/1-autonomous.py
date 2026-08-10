import os
from typing import Annotated, Sequence, Literal
from langchain_community.vectorstores import FAISS
from langchain_community.document_loaders import WebBaseLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langgraph.prebuilt import ToolNode
from langgraph.graph import StateGraph, END, add_messages
from typing import TypedDict
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, ToolMessage
from langchain_core.tools import create_retriever_tool

import json
from dotenv import load_dotenv
load_dotenv()

#-------------------------
# 1. Prepare Vector Store
#-------------------------

# Set USER_AGENT for WebBaseLoader if not already set
if not os.getenv('USER_AGENT'):
    os.environ['USER_AGENT'] = 'SimplilearnRagAgent/1.0'

urls = [
    "https://www.langgraph.com/blog/introducing-langgraph/",
    "https://www.langgraph.com/blog/langgraph-vs-langchain/",
    "https://www.langgraph.com/blog/langgraph-vs-langflow/",
    "https://www.langgraph.com/blog/langgraph-vs-langsmith/",
    "https://www.langgraph.com/blog/langgraph-vs-langserve/",
    "https://www.langgraph.com/blog/langgraph-vs-langchain-2/",
    "https://www.langgraph.com/blog/langgraph-vs-langflow-2/",
    "https://www.langgraph.com/blog/langgraph-vs-langsmith-2/",
    "https://www.langgraph.com/blog/langgraph-vs-langserve-2/"
]

docs = [WebBaseLoader(url).load() for url in urls]
doc_list = [doc for sublist in docs for doc in sublist]

text_splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
doc_splits = text_splitter.split_documents(doc_list)

#Add all texts to VectorDB

vectorstore = FAISS.from_documents(doc_splits, OpenAIEmbeddings())
retriever = vectorstore.as_retriever()

llm = ChatOpenAI(model_name="gpt-4o-mini")

#-------------------------------
# 2. Create Retriever Tool
#-------------------------------
retriever_tool = create_retriever_tool(
    retriever,
    "rag_retriever",
    "Search the vector database for relevant information about LangGraph. "
    "Use this tool when you need specific documentation, comparisons, or technical details about LangGraph. "
    "Returns the most relevant documentation chunks."
)

tools = [retriever_tool]

# Bind tools to LLM
llm_with_tools = llm.bind_tools(tools)

#-------------------------------
# 3. LangGraph State Definition
#-------------------------------
class AgenticRAGState(TypedDict):
    """State for the agentic RAG system"""
    messages: Annotated[Sequence[BaseMessage], add_messages]

#-------------------------------
# 4. Agent Node
#-------------------------------
def agent_node(state: AgenticRAGState) -> AgenticRAGState:
    """
    Agent node that decides whether to use the retriever tool or provide a final answer.
    The LLM will analyze the user query and decide:
    1. If it needs to search the retriever for relevant documentation
    2. If it has enough information to provide a final answer
    """
    messages = state["messages"]
    
    # Invoke LLM with tool-calling capability
    response = llm_with_tools.invoke(messages)
    
    return {"messages": [response]}


#-------------------------------
# 5. Tool Node
#-------------------------------
tool_node = ToolNode(tools)


#-------------------------------
# 6. Conditional Edge Function
#-------------------------------
def should_continue(state: AgenticRAGState) -> Literal["tools", END]:
    """
    Determines if the agent should call tools or end the conversation.
    
    If the last message contains tool calls, route to the tools node.
    Otherwise, the agent has provided the final answer, so end the conversation.
    """
    messages = state["messages"]
    last_message = messages[-1]
    
    # If there are tool calls, we route to the tools node
    if hasattr(last_message, "tool_calls") and last_message.tool_calls:
        return "tools"
    
    # Otherwise, we end (the LLM has provided the final answer)
    return END

#-------------------------------
# 7. Build LangGraph
#-------------------------------
builder = StateGraph(AgenticRAGState)

# Add nodes
builder.add_node("agent", agent_node)
builder.add_node("tools", tool_node)

# Set entry point
builder.set_entry_point("agent")

# Add conditional edges
# From agent node, decide whether to call tools or end
builder.add_conditional_edges(
    "agent",
    should_continue,
    {
        "tools": "tools",
        END: END,
    }
)

# After tools are called, always go back to the agent
builder.add_edge("tools", "agent")

# Compile the graph
graph = builder.compile()

#-------------------------------
# 8. Execute Graph
#-------------------------------
if __name__ == "__main__":
    # Test query
    query = "How do agent loops work and why are they useful in AI Systems?"
    
    # Create initial state with the user's query as a HumanMessage
    initial_state = AgenticRAGState(
        messages=[HumanMessage(content=query)]
    )
    
    print(f"User Query: {query}\n")
    print("=" * 80)
    
    # Execute the graph
    final_state = graph.invoke(initial_state)
    
    print("=" * 80)
    print("\nFinal Response:")
    
    # Extract the final assistant message
    for message in final_state["messages"]:
        if isinstance(message, AIMessage):
            print(f"\n{message.content}")
