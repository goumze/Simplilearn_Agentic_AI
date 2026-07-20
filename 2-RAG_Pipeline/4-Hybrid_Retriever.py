from langchain.chat_models import init_chat_model
from langchain_classic.chains import create_retrieval_chain
from langchain_classic.chains.combine_documents.stuff import create_stuff_documents_chain
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.retrievers import BM25Retriever
from langchain_classic.retrievers import EnsembleRetriever
from langchain_core.documents import Document
from langchain_core.prompts import PromptTemplate
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv

load_dotenv()  # Load environment variables from .env file

#Step 1: Sample Documents
print("Step 1: Sample Documents")
docs = [
    Document(page_content="LangChain helps build LLM applications"),
    Document(page_content="Pinecone is a vector database for semantic search"),
    Document(page_content="The Eiffel Tower is located in Paris, France"),
    Document(page_content="Langchain can be used to develop agentic ai applications"),
    Document(page_content="Langchain has many types of retrievers.")
]

#Step 2: Dense Retriever using FAISS + HuggingFaceEmbeddings
print("Step 2: Dense Retriever using FAISS + HuggingFaceEmbeddings")
embedding_model=HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
dense_vectorstore = FAISS.from_documents(docs, embedding_model)
dense_retriever = dense_vectorstore.as_retriever()

#Step 3: Sparse Retriever using BM25
print("Step 3: Sparse Retriever using BM25")
sparse_retriever = BM25Retriever.from_documents(docs)
sparse_retriever.k = 5  # Set the number of top documents to retrieve

#Step 4: Combine with EnsembleRetriever
print("Step 4: Combine with EnsembleRetriever")
hybrid_retriever = EnsembleRetriever(retrievers=[dense_retriever, sparse_retriever], weights=[0.7, 0.3])

#Step 5: Query and get results
print("Step 5: Query and get results")
query = "How can I build an application using LLMs ?"
results = hybrid_retriever.invoke(query)

#Step 6: Print Results
print("Step 6: Print Results")
for i,doc in enumerate(results):
    print(f"\n Document {i+1}: {doc.page_content}\n")

#Step 7: Prompt Template
print("Step 7: Prompt Template")
prompt = PromptTemplate.from_template("You are a helpful assistant. Use the following context to answer the question: {context}\n\nQuestion: {input}\nAnswer:")

#Step 8: LLM
print("Step 8: LLM")
llm = init_chat_model("gpt-3.5-turbo", temperature=0.2)

#Step 9: 
print("Step 9: Generate Answer")
document_chain=create_stuff_documents_chain(llm=llm, prompt=prompt)

#Step 10: Create RAG chain
rag_chain = create_retrieval_chain(retriever=hybrid_retriever, combine_docs_chain=document_chain)

#Step 11: Ask a question
print("Step 11: Ask a question")
query = {"input":"How can I build an application using LLMs ?"}
response = rag_chain.invoke(query)
print(f"\nAnswer: {response['answer']}\n")

#Step 12: Output
print("\nSource Documents Used for Answering the Question:")
for i, doc in enumerate(response['context']):
    print(f"\n Document {i+1}: {doc.page_content}\n")



