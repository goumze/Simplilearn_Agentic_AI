import os
from dotenv import load_dotenv
from typing import List, Dict, Any
from langchain_community.vectorstores import FAISS
import numpy as np
import warnings
warnings.filterwarnings("ignore", category=UserWarning)

#Langchain core imports
from langchain_core.documents import Document
from langchain_core.prompts import ChatPromptTemplate, PromptTemplate
from langchain_core.runnables import (
    RunnablePassthrough,
    RunnableWithMessageHistory
)
from langchain_core.output_parsers import StrOutputParser
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage

#Langchain specific imports
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_community.document_loaders import TextLoader,PyPDFLoader
from langchain_classic.chains import create_retrieval_chain
from langchain_classic.chains.combine_documents import create_stuff_documents_chain
from langchain_classic.chains import create_history_aware_retriever
from langchain_community.chat_message_histories import ChatMessageHistory


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
    
llm=ChatOpenAI(model="gpt-3.5-turbo")
simple_prompt_template = """You are a helpful assistant. Use the following context to answer the question at the end. If you don't know the answer, just say that you don't know, don't try to make up an answer.
{context}
Question: {question}
Answer:"""

simple_prompt = PromptTemplate(template=simple_prompt_template, input_variables=["context", "question"])

vectorstore_retriever = loaded_vector_store.as_retriever(search_type="similarity", search_kwargs={"k": 3})

def format_doc(docs: List[Document]) -> str:
    """Format a list of documents into a single string."""
    formatted = []
    for i,doc in enumerate(docs):
        print(f"Document {i + 1}:")
        print(f"Source: {doc.metadata.get('source', 'Unknown')}")
        print(f"Content: {doc.page_content}\n")
        source = doc.metadata.get('source', 'Unknown')
        formatted.append(f"Document {i + 1}:\nSource: {source}\nContent: {doc.page_content}")
    return "\n\n".join(formatted)

simple_rag_chain = ({"context": (lambda x: x["question"]) | vectorstore_retriever | format_doc, "question": RunnablePassthrough()} 
                    | simple_prompt
                    | llm
                    | StrOutputParser()
                    )
print("\nSimple RAG Chain:")
print(simple_rag_chain)

#Conversational RAG Chain Example
print("\nConversational RAG Chain Example")
conversational_prompt_template = """You are a helpful assistant with deep knowledge of AI, Machine Learning, and Deep Learning. 
Use the provided context and previous conversation history to answer questions effectively.
- Reference previous answers when relevant
- Provide detailed explanations based on the context
- Connect concepts together if the user asks follow-up questions
- If you don't know something, say so clearly

Context: {context}"""

conversational_prompt = ChatPromptTemplate.from_messages([
    ("system", conversational_prompt_template),
    ("placeholder", "{chat_history}"),
    ("human", "{input}")
])

def create_conversational_rag():
    """Create a conversational RAG chain with memory"""
    return (
        RunnablePassthrough().assign(
            context=lambda x: format_doc(vectorstore_retriever.invoke(x.get("input", "")))
        )
        | conversational_prompt
        | llm
        | StrOutputParser()
    )
print("\nConversational RAG Chain:")
print(create_conversational_rag())
# Session history storage (in-memory)
store = {}

def get_session_history(session_id: str):
    """Retrieve or create session history"""
    if session_id not in store:
        store[session_id] = ChatMessageHistory()
    return store[session_id]

conversational_rag_chain = RunnableWithMessageHistory(create_conversational_rag(),get_session_history,
                                                      input_messages_key="input",
                                                      history_messages_key="chat_history",
                                                      output_messages_key="output")



#Streaming RAG Chain Example
streaming_rag_chain = (
    {"context": (lambda x: x["question"]) | vectorstore_retriever | format_doc, "question": RunnablePassthrough()}
    | simple_prompt
    | llm
)

# print("Modern RAG Chains created successfully.")
# print("Available Chains")
# print("- simple_rag_chain: Basic Q&A")
# print("- conversational_rag_chain: Maintains Conversation History")
# print("- streaming_rag_chain: Supports token streamin g")

#Test Function for different chain types
def test_rag_chain(question:str):
    """Test all RAG chain variants"""
    print(f"Question: {question}\n")
    print("="*80)

    #1. Simple RAG Chain Test
    print("1. Simple RAG Chain Test")
    simple_rag_answer = simple_rag_chain.invoke({"question": question})
    print(f"Answer: {simple_rag_answer}\n")

   #2. Conversational RAG Chain Test
    print("2. Conversational RAG Chain Test")
    conversational_rag_answer = conversational_rag_chain.invoke({"input": question}, config={"configurable": {"session_id": "default_session"}})
    print(f"Answer: {conversational_rag_answer}\n")
    
    #3. Streaming RAG Chain Test
    print("3. Streaming RAG Chain Test")
    streaming_rag_answer = streaming_rag_chain.stream({"question": question})
    print(f"Answer: {streaming_rag_answer}\n")
    for chunk in streaming_rag_answer:
        print("Streaming Chunk: ")
        print(chunk, end="", flush=True)    
    print("\n\n")

def test_conversational_rag_multiquery():
    """Test conversational RAG with multiple related queries to demonstrate conversation history"""
    print("\n" + "="*80)
    print("COMPREHENSIVE CONVERSATIONAL RAG TEST - Multi-Query Conversation")
    print("="*80 + "\n")
    
    session_id = "conversation_session"
    questions = [
        "What is Artificial Intelligence?",
        "Tell me about its subset called Machine Learning",
        "How is Deep Learning different from what you mentioned?",
        "Which of these has been most successful in image recognition?"
    ]
    
    print("Note: The same session_id is used to maintain conversation history across queries.")
    print("Watch how the model references previous answers to provide contextually aware responses.\n")
    
    for i, question in enumerate(questions, 1):
        print(f"\n{'='*80}")
        print(f"QUERY {i}: {question}")
        print(f"{'='*80}")
        
        # Get the current history before this query
        current_history = get_session_history(session_id)
        history_messages = current_history.messages
        
        print(f"\n📋 CONVERSATION HISTORY BEFORE QUERY {i}:")
        print(f"   Number of messages in history: {len(history_messages)}")
        if len(history_messages) > 0:
            print(f"   Previous exchanges:")
            for msg_idx, msg in enumerate(history_messages):
                msg_type = "Human" if msg.__class__.__name__ == "HumanMessage" else "Assistant"
                msg_preview = msg.content[:100] + "..." if len(msg.content) > 100 else msg.content
                print(f"   [{msg_idx + 1}] {msg_type}: {msg_preview}")
        else:
            print(f"   [No history yet - this is the first query]")
        
        print(f"\n🔍 RETRIEVING CONTEXT FROM KNOWLEDGE BASE...")
        
        # Invoke conversational chain with same session to maintain history
        answer = conversational_rag_chain.invoke(
            {"input": question}, 
            config={"configurable": {"session_id": session_id}}
        )
        
        # Get the history after this query
        updated_history = get_session_history(session_id)
        updated_messages = updated_history.messages
        
        print(f"\n💬 RESPONSE:")
        print(f"{answer}\n")
        
        print(f"📊 CONVERSATION HISTORY AFTER QUERY {i}:")
        print(f"   Total messages now: {len(updated_messages)}")
        print(f"   Latest exchange added to history")
        
        if i < len(questions):
            print(f"\n⏭️  NEXT QUERY WILL HAVE ACCESS TO:")
            print(f"   - This response: '{answer[:80]}...'")
            print(f"   - Plus all {len(updated_messages)} previous messages")
            print(f"   - This enables contextual reasoning for follow-up questions")


test_rag_chain("What is the difference between AI and Machine Learning ?")

# Run the comprehensive multi-query conversational test
test_conversational_rag_multiquery()  


