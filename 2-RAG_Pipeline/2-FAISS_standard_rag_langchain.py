import os
from dotenv import load_dotenv
import numpy as np
import warnings
warnings.filterwarnings("ignore", category=UserWarning)

#Langchain core imports
from langchain_core.documents import Document
from langchain_core.prompts import ChatPromptTemplate, PromptTemplate
from langchain_core.runnables import (
    RunnablePassThrough
)
from langchain_core.output_parsers import StrOutputParser
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage

#Langchain specific imports
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_community.document_loaders import TextLoader,PyPDFLoader
from langchain_classic.chains import create_retrieval_chain
from langchain_classic.chains.combine_documents import create_stuff_documents_chain

sample_documents = [
    Document(page_content="Artificial Intelligence (AI) is the simulation of human intelligence in machines." \
    " These machines are programmed to think like humans and mimic their actions. The term may also be applied to any machine that exhibits traits associated with a human mind such as learning and problem-solving."
             , metadata={"source": "AI Introduction","page": 1,"topic": "Artificial Intelligence"}),
    Document(page_content="Machine Learning (ML) is a subset of AI that focuses on the development of algorithms and statistical models that enable computers to learn from and make predictions or decisions based on data. It allows systems to improve their performance on a specific task over time without being explicitly programmed."
             , metadata={"source": "ML Introduction","page": 2,"topic": "Machine Learning"}),
    Document(page_content="Deep Learning (DL) is a subset of ML that uses neural networks with many layers (hence 'deep') to model complex patterns in data. It has been particularly successful in areas such as image and speech recognition, natural language processing, and autonomous systems."
                , metadata={"source": "DL Introduction","page": 3,"topic": "Deep Learning"})
]

print("Sample Documents:")
for doc in sample_documents:
    print(doc)

#Text Splitter
text_splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=20)    




