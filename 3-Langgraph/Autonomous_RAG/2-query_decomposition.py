"""
Query Decomposition Example
"""
import os
from typing import Annotated, TypedDict, Sequence
from dotenv import load_dotenv
from langchain_community.vectorstores import FAISS
from langchain_community.document_loaders import WebBaseLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from langgraph.graph import StateGraph, END, add_messages
from pydantic import BaseModel, Field
from langchain.chat_models import ChatOpenAI
from langchain.chat_models import init_chat_model

load_dotenv()


