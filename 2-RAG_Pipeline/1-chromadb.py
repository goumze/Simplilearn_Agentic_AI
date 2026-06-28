## langchain imports
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import TextLoader
from langchain_openai import OpenAIEmbeddings
from langchain_core.documents import Document
from langchain_community.document_loaders import DirectoryLoader,TextLoader
from langchain_openai import ChatOpenAI
from langchain_classic.chains import create_retrieval_chain
from langchain_core.prompts import ChatPromptTemplate
from langchain_classic.chains.combine_documents import create_stuff_documents_chain
from langchain_core.prompts import ChatPromptTemplate

## vectorstores
from langchain_community.vectorstores import Chroma

## utility imports
import numpy as np
from typing import List
from dotenv import load_dotenv
import os

load_dotenv()

if __name__ == "__main__":
    ## create sample documents
    sample_docs = [
        """
    Machine Learning Fundamentals
    
    Machine learning is a subset of artificial intelligence that enables systems to learn 
    and improve from experience without being explicitly programmed. There are three main 
    types of machine learning: supervised learning, unsupervised learning, and reinforcement 
    learning. Supervised learning uses labeled data to train models, while unsupervised 
    learning finds patterns in unlabeled data. Reinforcement learning learns through 
    interaction with an environment using rewards and penalties.
    """,
        
        """
    Deep Learning and Neural Networks
    
    Deep learning is a subset of machine learning based on artificial neural networks. 
    These networks are inspired by the human brain and consist of layers of interconnected 
    nodes. Deep learning has revolutionized fields like computer vision, natural language 
    processing, and speech recognition. Convolutional Neural Networks (CNNs) are particularly 
    effective for image processing, while Recurrent Neural Networks (RNNs) and Transformers 
    excel at sequential data processing.
    """,
        
        """
    Natural Language Processing (NLP)
    
    NLP is a field of AI that focuses on the interaction between computers and human language. 
    Key tasks in NLP include text classification, named entity recognition, sentiment analysis, 
    machine translation, and question answering. Modern NLP heavily relies on transformer 
    architectures like BERT, GPT, and T5. These models use attention mechanisms to understand 
    context and relationships between words in text.
    """
    ]

    #Save sample_docs to text files
    for i, doc in enumerate(sample_docs):
        with open(f"sample_doc_{i+1}.txt", "w") as f:
            f.write(doc.strip())

    # Load documents from the text files
    loader = DirectoryLoader('.', glob='sample_doc_*.txt', loader_cls=TextLoader)
    documents = loader.load()
    print(f"Loaded {len(documents)} documents.")
    print(f"First document content:\n{documents[0].page_content[:200]}...")  # Print first 200 characters of the first document

    # Split documents into smaller chunks
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
    split_docs = text_splitter.split_documents(documents)
    print(f"Split into {len(split_docs)} chunks.")

    #Print chunks
    for i, chunk in enumerate(split_docs):
        print(f"Chunk {i+1} content:\n{chunk.page_content[:200]}...\n")  # Print first 200 characters of each chunk

    #Embedding example
    sample_text = "Machine learning is a subset of artificial intelligence that enables systems to learn and improve from experience without being explicitly programmed."
    embeddings = OpenAIEmbeddings()
    sample_embedding = embeddings.embed_query(sample_text)
    print(f"Sample embedding vector length: {len(sample_embedding)}")

    # Create a Chroma vector store from the split documents
    persist_directory = "./chroma_db"

    vectorstore = Chroma.from_documents(
        documents=split_docs,
        embedding=OpenAIEmbeddings(),
        persist_directory=persist_directory,
        collection_name="rag_collection"
    )

    print("Chroma vector store created.")
    print(f"Vector store contains {vectorstore._collection.count()} vectors.")
    print(f"Persisted to: {persist_directory}")
    print("Vectors in the vector store:")
    for i, vector in enumerate(vectorstore._collection.get()):
        print(f"Vector {i+1}: {vector}")

    #Sample example query for retrieval
    query = "What is machine learning?"
    query_embedding = embeddings.embed_query(query)
    results = vectorstore.similarity_search(query, k=3)
    print(f"Query: {query}")
    print("Top 3 similar documents:")
    for i, result in enumerate(results):
        print(f"Result {i+1} content:\n{result.page_content[:200]}...\n")  # Print first 200 characters of each result
        #with metadata
        print(f"Result {i+1} metadata: {result.metadata}\n")

    #Similarity search with score
    query = "Explain deep learning and neural networks."
    query_embedding = embeddings.embed_query(query)
    results_with_score = vectorstore.similarity_search_with_score(query, k=3)
    print(f"Query: {query}")
    print("Top 3 similar documents with scores:")
    for i, (result, score) in enumerate(results_with_score):
        print(f"Result {i+1} content:\n{result.page_content[:200]}...\n")  # Print first 200 characters of each result
        print(f"Result {i+1} score: {score}\n")
        #with metadata
        print(f"Result {i+1} metadata: {result.metadata}\n")

    llm = ChatOpenAI(model_name="gpt-3.5-turbo")

    ## Convert vector store to retriever
    retriever=vectorstore.as_retriever(
    search_kwarg={"k":3} ## Retrieve top 3 relevant chunks
    )

    system_prompt = """You are an assistant for question-answering tasks. 
    Use the following pieces of retrieved context to answer the question. 
    If you don't know the answer, just say that you don't know. 
    Use three sentences maximum and keep the answer concise.

    Context: {context}"""

    document_chain = create_stuff_documents_chain(llm=llm, prompt=ChatPromptTemplate.from_template(system_prompt))
    rag_chain = create_retrieval_chain(retriever, document_chain)

    #Invoke LLM with a query
    query = "What is Deep Learning?"
    response=rag_chain.invoke({"input": query})
    print(f"Query: {query}")
    print(f"Response: {response}")
    print("\n")






