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
from langchain.agents import create_agent
import json
from dotenv import load_dotenv
load_dotenv()
llm=init_chat_model("openai:gpt-4o")

#-------------------------------------- #
# 1. Creat retriever tool
#-------------------------------------- #

#Load content from blog
docs = WebBaseLoader("https://lilianweng.github.io/posts/2023-06-23-agent/").load()
splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
chunks = splitter.split_documents(docs)

embeddings = OpenAIEmbeddings()
vectorstore = FAISS.from_documents(chunks, embeddings)
retriever = vectorstore.as_retriever()

def retriever_tool_func(query:str)->str:
    #print("Using RAG retrieval tool")
    docs = retriever.invoke(query)
    return "\n".join([doc.page_content for doc in docs])

retriever_tool_func("What are autonomous agents?")

retriever_tool = Tool(name="RAGRetriever",
                      description="Use this tool to fetch relevant knowledge base info",
                      func=retriever_tool_func)

#Wikipedia tool
wiki_tool = WikipediaQueryRun(api_wrapper=WikipediaAPIWrapper())

#-------------------------------------- #
# 2. Define the Agent Node
#-------------------------------------- #
tools = [retriever_tool, wiki_tool]

##Create the native Langgraph agent node
react_agent_node = create_agent(
    model=llm,
    tools=tools)

#-------------------------------------- #
# 3. Langgraph Agent State
#-------------------------------------- #
class AgentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], add_messages]

#-------------------------------------- #
# 4. Create the Langgraph State Graph
#-------------------------------------- #
builder = StateGraph(AgentState)
builder.add_node("react_agent", react_agent_node)
builder.set_entry_point("react_agent")
builder.add_edge("react_agent", END)

graph = builder.compile()

#-------------------------------------- #
# 5. Run the Langgraph Agent
#-------------------------------------- #
if __name__ == "__main__":
    user_query = "What is an agent loop and how does Wikipedia describe autonomous agents?"
    state = {"messages":[HumanMessage(content=user_query)]}
    result = graph.invoke(state)
    print("\nFinal Message:\n",result["messages"][-1].content)
    print("\nFull result:\n",result)