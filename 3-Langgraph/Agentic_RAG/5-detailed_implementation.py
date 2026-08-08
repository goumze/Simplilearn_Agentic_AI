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
from langchain.tools.retriever import create_retriever_tool
import json
from dotenv import load_dotenv
load_dotenv()
llm=init_chat_model("openai:gpt-4o")

urls = [
    "https://langchain-ai.github.io/langgraph/tutorials/introduction/",
    "https://langchain-ai.github.io/langgraph/tutorials/workflows/",
    "https://langchain-ai.github.io/langgraph/how-tos/map-reduce/",
]

docs = [WebBaseLoader(url).load() for url in urls]
doc_list = [doc for sublist in docs for doc in sublist]

text_splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
doc_splits = text_splitter.split_documents(doc_list)

#Add all texts to VectorDB

vectorstore = FAISS.from_documents(doc_splits, OpenAIEmbeddings())
retriever = vectorstore.as_retriever()
