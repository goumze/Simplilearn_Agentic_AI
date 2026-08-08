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

##Generic function to create a RAG retriever tool from a URL
def make_retrieval_tool_from_url(url:str, chunk_size:int=500, chunk_overlap:int=50)->Tool:
    #Load content from blog
    docs = WebBaseLoader(url).load()
    splitter = RecursiveCharacterTextSplitter(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
    chunks = splitter.split_documents(docs)

    embeddings = OpenAIEmbeddings()
    vectorstore = FAISS.from_documents(chunks, embeddings)
    retriever = vectorstore.as_retriever()

    def retriever_tool_func(query:str)->str:
        docs = retriever.invoke(query)
        return "\n".join([doc.page_content for doc in docs])

    retriever_tool = Tool(name="RAGRetriever",
                          description="Use this tool to fetch relevant knowledge base info",
                          func=retriever_tool_func)
    
    return retriever_tool

#Wikipedia tool
wiki_tool = WikipediaQueryRun(api_wrapper=WikipediaAPIWrapper())

internal_tool_1=make_retrieval_tool_from_url("https://lilianweng.github.io/posts/2023-06-23-agent/")
internal_tool_2=make_retrieval_tool_from_url("https://www.oreilly.com/library/view/architecting-intelligent-agents/9781492055110/ch01.html")

tools=[wiki_tool, internal_tool_1, internal_tool_2]

react_agent_node = create_agent(model=llm,tools=tools)

class AgentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], add_messages]

builder = StateGraph(AgentState)
builder.add_node("react_agent_node", react_agent_node)
builder.set_entry_point("react_agent_node")
builder.add_edge("react_agent_node",END)

graph = builder.compile()

if __name__=="__main__":
    query = "What do our internal research notes say about transformer variants, and what does Wikipedia recently say about transformer variants?"
    state = {"messages":[HumanMessage(content=query)]}
    result = graph.invoke(state)
    print("\nFinal Message:\n",result["messages"][-1].content)