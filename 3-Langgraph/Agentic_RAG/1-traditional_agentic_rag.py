import os
from pydoc import doc
from typing import List, Annotated
from pydantic import BaseModel
from langchain_community.vectorstores import FAISS
from langchain_community.document_loaders import WebBaseLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain.chat_models import init_chat_model
from langchain_openai import OpenAIEmbeddings
from langchain_core.documents import Document
from langgraph.graph import StateGraph,END
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

retriever.invoke("What are agents")

#-------------------------------------- #
# 3. Define RAG State
#-------------------------------------- #
class RAGState(BaseModel):
    question: str
    retrieved_docs: List[Document] = []
    answer: str = ""

#-------------------------------------- #
# 4. LangGraph nodes
#-------------------------------------- #
def retrieve_docs(state: RAGState):
    docs = retriever.invoke(state.question)
    return {"question": state.question, "retrieved_docs": docs}

def generate_answer(state: RAGState):
    context = "\n".join([doc.page_content for doc in state.retrieved_docs])
    prompt = f"Answer the question based on the context:\n\nContext:\n{context}\n\nQuestion: {state.question}"
    answer = llm.invoke(prompt)
    return {"answer": answer.content}

#-------------------------------------- #
# 5. Define LangGraph
# -------------------------------------- #
builder = StateGraph(RAGState)
builder.add_node("retriever", retrieve_docs)
builder.add_node("responder", generate_answer)
builder.set_entry_point("retriever")
builder.add_edge("retriever", "responder")
builder.add_edge("responder", END)

graph = builder.compile()

#-------------------------------------- #
# 6. Run the agentic RAG
#-------------------------------------- #
if __name__ == "__main__":
    question = "What are agents?"
    initial_state = RAGState(question=question)
    final_state = graph.invoke(initial_state)
    print(f"Question: {final_state.get('question', 'N/A')}")
    print(f"Answer: {final_state.get('answer', 'N/A')}")
