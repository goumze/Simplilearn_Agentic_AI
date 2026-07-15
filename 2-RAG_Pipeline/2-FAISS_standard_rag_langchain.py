import os
from dotenv import load_dotenv
from langchain_community.vectorstores import FAISS
import numpy as np
import warnings
warnings.filterwarnings("ignore", category=UserWarning)

#Langchain core imports
from langchain_core.documents import Document
from langchain_core.prompts import ChatPromptTemplate, PromptTemplate
from langchain_core.runnables import (
    RunnablePassthrough
)
from langchain_core.output_parsers import StrOutputParser
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage

#Langchain specific imports
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_community.document_loaders import TextLoader,PyPDFLoader
from langchain_classic.chains import create_retrieval_chain
from langchain_classic.chains.combine_documents import create_stuff_documents_chain


load_dotenv()


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
text_splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=20, length_function=len, separators=["\n"," ", ""])

#Split documents into chunks
chunks = text_splitter.split_documents(sample_documents)
print("Document Chunks:")
for chunk_number, chunk in enumerate(chunks):
    print(f"Chunk {chunk_number + 1}: {chunk}")
    print(f"Metadata: {chunk.metadata}")

embeddings = OpenAIEmbeddings(model="text-embedding-3-small")

#Example: Create a embedding for a single text
sample_text = "What is machine learning ?"

sample_embedding = embeddings.embed_query(sample_text)
print(f"Sample Text: {sample_text}")
print(f"Sample Embedding: {sample_embedding}")

texts=["AI","Machine Learning","Deep Learning","Neural Network"]
batch_embeddings = embeddings.embed_documents(texts)
print(f"Batch Texts: {texts}")
print(f"Batch Embeddings: {batch_embeddings}")

#Compare Embeddings using cosine similarity

def cosine_similarity(vec1, vec2):
    """Compute the cosine similarity between two vectors."""
    dot_product = np.dot(vec1, vec2)
    norm_vec1 = np.linalg.norm(vec1)
    norm_vec2 = np.linalg.norm(vec2)
    return dot_product / (norm_vec1 * norm_vec2)

#Text Semantic Similarity
print("\nText Semantic Similarity Examples:")
print(f"'AI vs Artifical Intelligence': {cosine_similarity(batch_embeddings[0], batch_embeddings[0]):.4f}")
print(f"'Machine Learning vs Deep Learning': {cosine_similarity(batch_embeddings[1], batch_embeddings[2]):.4f}")

#Create FAISS Vector Store
vector_store = FAISS.from_documents(chunks, embeddings)

print(f"\nFAISS Vector Store Created with total of {vector_store.index.ntotal} vectors")

#Save vector store to later use    
vector_store.save_local("faiss_index")
print("Vector Store saved to 'faiss_index' directory")

#Load vector store from local directory
loaded_vector_store = FAISS.load_local("faiss_index", embeddings, allow_dangerous_deserialization=True)
print(f"Loaded Vector Store with total of {loaded_vector_store.index.ntotal} vectors")

#Similarity Search Example
print("\nSimilarity Search Example")
query = "Explain deep learning"
retrieved_docs = loaded_vector_store.similarity_search(query, k=3)

print(f"Query: {query}")
print("\nTop 3 similar chunks")
for i, doc in enumerate(retrieved_docs):
    print(f"Chunk {i + 1}: {doc.page_content}")
    print(f"Metadata: {doc.metadata['source']}")

#Similarity Search with Score Example
print("\nSimilarity Search with Score Example")
query = "Explain deep learning"
retrieved_docs_with_scores = loaded_vector_store.similarity_search_with_score(query, k=3)
print(f"\nQuery: {query}")
print("\nTop 3 similar chunks with scores")
for i, (doc, score) in enumerate(retrieved_docs_with_scores):
    print(f"Chunk {i + 1}: {doc.page_content}")
    print(f"Metadata: {doc.metadata['source']}")
    print(f"Score: {score:.4f}")

#Search with Metadata Filter Example
print("\nSearch with Metadata Filter Example")
query = "Explain deep learning"
metadata_filter = {"topic": "Deep Learning"}
retrieved_docs_with_filter = loaded_vector_store.similarity_search(query, k=3, filter=metadata_filter)
print(f"\nQuery: {query}")
print(f"Metadata Filter: {metadata_filter}")
print("\nTop 3 similar chunks with metadata filter")
for i, doc in enumerate(retrieved_docs_with_filter):
    print(f"Chunk {i + 1}: {doc.page_content}")
    print(f"Metadata: {doc.metadata['source']}")

#Build RAG chain with LCEL
    
