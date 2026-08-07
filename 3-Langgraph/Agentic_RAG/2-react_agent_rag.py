import os
from pydoc import doc
from typing import List, Annotated
from langchain_community.tools import WikipediaQueryRun
from langchain_community.utilities import WikipediaAPIWrapper
from langchain_core.tools import Tool
from pydantic import BaseModel
from langchain_community.vectorstores import FAISS
from langchain_community.document_loaders import WebBaseLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain.chat_models import init_chat_model
from langchain_openai import OpenAIEmbeddings
from langchain_core.documents import Document
from langgraph.graph import StateGraph,END, add_messages
from typing import TypedDict, Sequence
from langchain_core.messages import BaseMessage, HumanMessage, ToolMessage
import json
from dotenv import load_dotenv
load_dotenv()
llm=init_chat_model("openai:gpt-4o")

# -------------------------------------- #
# 1. Document Preprocessing 
# -------------------------------------- #
urls = [
    "https://lilianweng.github.io/posts/2023-06-23-agent/",
    "https://lilianweng.github.io/posts/2024-04-12-diffusion-video/",
]

loaders = [WebBaseLoader(url) for url in urls]
docs=[]

for loader in loaders:
    docs.extend(loader.load())

print(f"Loaded {len(docs)} documents from the web.")
print(docs)

#-------------------------------------- #
# 2. Recursive Character Text Splitting
#-------------------------------------- #
text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=500,
    chunk_overlap=50
)

embeddings = OpenAIEmbeddings()
vectorstore = FAISS.from_documents(docs, embeddings)
retriever = vectorstore.as_retriever(search_kwargs={"k": 3})

retriever.invoke("What are autonomous agents")

def retrieval_tool_func(query:str)->str:
    print("Using RAG retrieval tool")
    docs = retriever.invoke(query)
    return "\n".join([doc.page_content for doc in docs])

retrieval_tool = Tool(name="RAGRetriever",
                      description="A tool that retrieves relevant documents from a vector store based on a query.",
                      func=retrieval_tool_func)

print(retrieval_tool.name)

#Wikipedia Tool
wiki_tool = WikipediaQueryRun(api_wrapper=WikipediaAPIWrapper())

#-------------------------------------- #
# 3. Define the Agent Mode
#-------------------------------------- #
tools = [retrieval_tool, wiki_tool]

#-------------------------------------- #
# 4. Define Agent using tool binding
#-------------------------------------- #
# Bind tools to the LLM
llm_with_tools = llm.bind_tools(tools)

# Create a mapping of tool names to tool functions
tool_map = {tool.name: tool for tool in tools}

def agent_node(state: dict):
    """Agent node that handles tool calls and continues until text response"""
    messages = state.get("messages", [])
    
    # Get response from LLM with tools bound
    response = llm_with_tools.invoke(messages)
    new_messages = messages + [response]
    
    # If there are tool calls, execute them and add results
    if response.tool_calls:
        for tool_call in response.tool_calls:
            tool_name = tool_call['name']
            tool_input = tool_call['args']
            tool_id = tool_call['id']
            
            # Execute the tool
            if tool_name in tool_map:
                tool = tool_map[tool_name]
                try:
                    # Handle different input formats
                    if '__arg1' in tool_input:
                        # For single argument tools (like RAGRetriever)
                        result = tool.invoke(tool_input['__arg1'])
                    elif 'query' in tool_input:
                        # For Wikipedia tool which expects 'query' parameter
                        result = tool.invoke(tool_input['query'])
                    elif isinstance(tool_input, dict) and len(tool_input) == 1:
                        # For any other single-parameter tool
                        result = tool.invoke(list(tool_input.values())[0])
                    else:
                        # Try passing the dict directly
                        result = tool.invoke(tool_input)
                    
                    # Add tool result message
                    tool_result_msg = ToolMessage(
                        content=str(result),
                        tool_call_id=tool_id,
                        name=tool_name
                    )
                    new_messages.append(tool_result_msg)
                except Exception as e:
                    print(f"Error executing tool {tool_name}: {str(e)}")
                    import traceback
                    traceback.print_exc()
                    tool_result_msg = ToolMessage(
                        content=f"Error executing {tool_name}: {str(e)}",
                        tool_call_id=tool_id,
                        name=tool_name
                    )
                    new_messages.append(tool_result_msg)
        
        # Get another response from the LLM with tool results
        final_response = llm_with_tools.invoke(new_messages)
        new_messages.append(final_response)
    
    return {"messages": new_messages}

#-------------------------------------- #
# 5. LangGraph State Definition
#-------------------------------------- #
class AgentState(TypedDict):
    messages:Annotated[Sequence[BaseMessage], add_messages]

#-------------------------------------- #
# 6. Define LangGraph
#-------------------------------------- #
builder = StateGraph(AgentState)
builder.add_node("agent", agent_node)
builder.set_entry_point("agent")
builder.add_edge("agent", END)
graph = builder.compile()

#-------------------------------------- #
# 7. Run the agentic RAG
#-------------------------------------- #
if __name__ == "__main__":
    user_query = "What is an agent loop and how does Wikipedia describe autonomous agents?"
    initial_state = AgentState(messages=[HumanMessage(content=user_query)])
    result = graph.invoke(initial_state)
    
    print("\n" + "="*80)
    print("AGENT RAG RESPONSE")
    print("="*80)
    
    if result["messages"]:
        # Get the last message which should be the final response
        last_message = result["messages"][-1]
        
        print(f"\n📝 Query:\n{user_query}")
        print(f"\n🤖 Agent Response:\n")
        print("-" * 80)
        
        if hasattr(last_message, 'content') and last_message.content:
            print(last_message.content)
        else:
            print("No response generated")
        
        print("\n" + "="*80)
        print(f"Total conversation turns: {len(result['messages'])}")
        print("="*80)
    else:
        print("No response generated")







