"""
Query Decomposition Example
"""
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

docs = TextLoader("data/text_files/sample.txt").load()
chunks = RecursiveCharacterTextSplitter(chunk_size=100, chunk_overlap=20).split_documents(docs)
vectorstore = FAISS.from_documents(chunks, OpenAIEmbeddings())
retriever = vectorstore.as_retriever()

#----------------------#
# 2. STATE Defintion
#----------------------#
class RAGReflectionState(BaseModel):
    question:str
    retrieved_docs: List[Document] = []
    answer:str = ""
    reflection:str = ""
    revised: bool = False
    attempts: int = 0

#----------------------#
# 3. Nodes
#----------------------#


#----------------------#
# 3a Retrieve Docs Node
#----------------------#
def retrieve_docs(state: RAGReflectionState) -> RAGReflectionState:
    print(f"Retrieving docs for question: {state.question}")
    docs = retriever.invoke(state.question)
    return state.model_copy(update={"retrieved_docs": docs})

#----------------------#
# 3b Generate Answer Node
#----------------------#

def generate_answer(state: RAGReflectionState) -> RAGReflectionState:
    print(f"Generating answer for question: {state.question}")
    context = "\n\n".join([doc.page_content for doc in state.retrieved_docs])
    prompt = f"""
    Use the following context to answer the question:

    Context:
    {context}
    Question: {state.question}"""

    answer = llm.invoke(prompt).content.strip()
    return state.model_copy(update={"answer": answer, "attempts": state.attempts + 1})

#----------------------#
# 3c Reflection Node
#----------------------#
def reflect_on_answer(state: RAGReflectionState) -> RAGReflectionState:
    print(f"Reflecting on answer: {state.answer}")
    prompt = f"""   
    Reflect on the following answer to see if it fully addresses the question.
    State YES if it is complete and correct, or NO with an explanation
    
    Question: {state.question}

    Answer: {state.answer}

    Respond like:
    Reflection: YES or NO
    Explanation:...
    """
    result = llm.invoke(prompt).content
    print(f"Reflection Result: {result}")
    is_ok = "reflection: yes" in result.lower()
    print(f"Is the answer OK? {is_ok}")
    return state.model_copy(update={"reflection": result, "revised": not is_ok})

#----------------------#
# 4. LANGGRAPH DAG
# ----------------------#
    
builder = StateGraph(RAGReflectionState)
builder.add_node("retriever", retrieve_docs)
builder.add_node("responder", generate_answer)
builder.add_node("reflector", reflect_on_answer)
builder.add_node("done",finalize)

builder.set_entry_point("retriever")
builder.add_edge("retriever","responder")
builder.add_edge("responder","reflector")
builder.add_conditional_edges("reflector",lambda s:"done if s.revised or s.attempts >= 2 else retriever")

builder.add_edge("done",END)
graph = builder.compile()

#----------------------#
# 5. Run DAG
#----------------------#
if __name__ == "__main__":
    #initial_state = RAGReflectionState(question="What is Python and how is it used in production environments ?")
    initial_state = RAGReflectionState(question="What is LangGraph?")
    result = graph.invoke(initial_state)
    # Convert dict result back to Pydantic model
    result = RAGReflectionState.model_validate(result)
    print(f"Final Answer: {result.answer}")
    print(f"Reflection: {result.reflection}")
    print(f"Total Attempts: {result.attempts}")
