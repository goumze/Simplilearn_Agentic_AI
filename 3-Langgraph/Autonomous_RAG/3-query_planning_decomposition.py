import os
from typing import Annotated, List, TypedDict, Sequence
from weakref import finalize
from dotenv import load_dotenv
from langchain_community.vectorstores import FAISS
from langchain_community.document_loaders import TextLoader, WebBaseLoader
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from langgraph.graph import StateGraph, END, add_messages
from pydantic import BaseModel, Field
from langchain_openai import ChatOpenAI
from langchain.chat_models import init_chat_model

load_dotenv()

#Load LLM Model
llm = init_chat_model("gpt-4")

#----------------------#
# 1. Load and Embed Docs
#----------------------#
urls = [
    "https://lilianweng.github.io/posts/2023-06-23-agent",
    "https://lilianweng.github.io/posts/2023-06-12-diffusion-video/"
]

docs = []

for url in urls:
    docs.extend(WebBaseLoader(url).load())

splitter = RecursiveCharacterTextSplitter(chunk_size=100, chunk_overlap=20)
chunks = splitter.split_documents(docs)

embedding = OpenAIEmbeddings()
vectorstore = FAISS.from_documents(chunks, embedding)
retriever = vectorstore.as_retriever()

#----------------------#
# 2. STATE Defintion
#----------------------#
class RAGState(BaseModel):
    question:str
    sub_questions: List[str] = []
    retrieved_docs: List[Document] = []
    answer: str = ""

#----------------------#
# 3. Nodes
#----------------------#

##a.Query Planner: splits input question

def plan_query(state: RAGState) -> RAGState:    
    prompt = f"""
    Break the following complex question into 2-3 sub-questions:

    Question: {state.question}

    Sub-questions:
    """
    result = llm.invoke(prompt)
    sub_questions = [line.strip() for line in result.content.strip().split("\n") if line.strip()]
    return RAGState(question=state.question, sub_questions=sub_questions)

##b. Retrieve Docs Node: retrieves docs for each sub-question

def retrieve_for_each(state: RAGState) -> RAGState:
    all_docs = []
    for sub_question in state.sub_questions:
        docs = retriever.invoke(sub_question)
        all_docs.extend(docs)
    return RAGState(question=state.question, sub_questions=state.sub_questions, retrieved_docs=all_docs)

##c. Generate final answer

def generate_final_answer(state: RAGState) -> RAGState:
    context = "\n\n".join([doc.page_content for doc in state.retrieved_docs])
    prompt = f"""
    Use the following context to answer the question:

    Context:
    {context}
    Question: {state.question}"""

    answer = llm.invoke(prompt).content.strip()
    return RAGState(question=state.question, sub_questions=state.sub_questions, retrieved_docs=state.retrieved_docs, answer=answer)

#----------------------#
# 4. Graph Definition
#----------------------#
builder = StateGraph(RAGState)
builder.add_node("plan_query", plan_query)
builder.add_node("retriever",retrieve_for_each)
builder.add_node("responder",generate_final_answer)

builder.set_entry_point("plan_query")

builder.add_edge("plan_query","retriever")
builder.add_edge("retriever","responder")
builder.add_edge("responder",END)

graph = builder.compile()

#----------------------#
# 5. Run the Graph
#----------------------#
if __name__ == "__main__":
    user_query="Explain how agent loops work and what are the challenges in the diffusion video generation."
    initial_state = RAGState(question=user_query)
    final_state = graph.invoke(initial_state)
    print(f"Final State: {final_state}")

    print("\nSub-questions generated:")
    for question in final_state['sub_questions']:
        print(f"- {question}")

    print("\nFinal Answer: ", final_state['answer'])

    