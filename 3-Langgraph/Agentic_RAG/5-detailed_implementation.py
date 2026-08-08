import os
from pydoc import doc
from typing import List, Annotated, Literal
from langchain_classic.prompts import PromptTemplate
from langchain_community.tools import WikipediaQueryRun
from langchain_community.utilities import WikipediaAPIWrapper
from langchain_core.output_parsers import StrOutputParser
from langchain_core.tools import Tool
from pydantic import BaseModel, Field
from langchain_community.vectorstores import FAISS
from langchain_community.document_loaders import WebBaseLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain.chat_models import init_chat_model
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_core.documents import Document
from langgraph.graph import StateGraph,END, add_messages
from typing import TypedDict, Sequence
from langchain_core.messages import BaseMessage, HumanMessage, ToolMessage
from langchain_core.tools import create_retriever_tool
from langchain import hub

import json
from dotenv import load_dotenv
load_dotenv()

urls = [
    "https://www.langgraph.com/blog/introducing-langgraph/",
    "https://www.langgraph.com/blog/langgraph-vs-langchain/",
    "https://www.langgraph.com/blog/langgraph-vs-langflow/",
    "https://www.langgraph.com/blog/langgraph-vs-langsmith/",
    "https://www.langgraph.com/blog/langgraph-vs-langserve/",
    "https://www.langgraph.com/blog/langgraph-vs-langchain-2/",
    "https://www.langgraph.com/blog/langgraph-vs-langflow-2/",
    "https://www.langgraph.com/blog/langgraph-vs-langsmith-2/",
    "https://www.langgraph.com/blog/langgraph-vs-langserve-2/"
]

docs = [WebBaseLoader(url).load() for url in urls]
doc_list = [doc for sublist in docs for doc in sublist]

text_splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
doc_splits = text_splitter.split_documents(doc_list)

#Add all texts to VectorDB

vectorstore = FAISS.from_documents(doc_splits, OpenAIEmbeddings())
retriever = vectorstore.as_retriever()

retriever_tool = create_retriever_tool(retriever,"retriever_vector_db_blog","Search and run information about LangGraph.")

#Langchain blogs- Separate VectorDB 

langchain_urls=[
    "https://python.langchain.com/docs/tutorials/",
    "https://python.langchain.com/docs/tutorials/chatbot/",
    "https://python.langchain.com/docs/tutorials/qa_chat_history/"
]

docs = [WebBaseLoader(url).load() for url in langchain_urls]

doc_list = [doc for sublist in docs for doc in sublist]

text_splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
doc_splits = text_splitter.split_documents(doc_list)

vectorstore_langchain = FAISS.from_documents(doc_splits, OpenAIEmbeddings())
retriever_langchain = vectorstore_langchain.as_retriever()

retriever_tool_langchain=create_retriever_tool(retriever_langchain,
                                               "retriever_vector_db_langchain",
                                               "Search and run information about LangChain.")

tools = [retriever_tool,retriever_tool_langchain]

#Workflow
class AgentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], add_messages]

def agent(state):
    """
    Invokes the agent model to generate a response based on the current state. Given the question,
    it will decide to retrieve using the retriever tool, or simply end.

    Args:
        state (AgentState): The current state of the agent, including messages.

    Returns:
        dict: The updated state with the agent response to messages    
    """    

    print("--CALL AGENT--")
    messages = state["messages"]

    model = ChatOpenAI(model_name="gpt-4o-mini")
    model = model.bind_tools(tools)
    response = model.invoke(messages=messages)
    return {"messages": [response]}

#Edges
def grade_documents(state)->Literal["generate","rewrite"]:
    """
    Determines whether to generate a new document or rewrite an existing one based on the agent's messages.

    Args:
        state (AgentState): The current state of the agent, including messages.
    """
    print("--CHECK RELEVANCE--")

    #Data Model
    class grade_documents(BaseModel):
        """Binary Score for relevance check"""
        binary_score:str=Field(description="Relevance score 'yes' or 'no'")
        
    #LLM
    model = ChatOpenAI(model_name="gpt-4o-mini")

    #LLM with tool and validation
    llm_with_tool = model.with_structured_output(grade_documents)

    #Prompt
    prompt = PromptTemplate(
        template="""You are a grader assessing relevance of a retrieved document to a user question. \n
        Here is the retrieved document: \n\n {context} \n\n
        Here is the question: {question} \n
        If the document contains keyword(s) or semantic meaning related to the user question, grade it's relevant. \n
        Give a binary score 'yes' or 'no' score to indicate whether the document is relevant to the question. \n""",
        input_variables=["context","question"]
        )

    #Chain
    chain = prompt | llm_with_tool

    messages = state["messages"]
    last_message = messages[-1]

    question = messages[0].content
    docs = last_message.content

    scored_result = chain.invoke({"context":docs,"question":question})

    score=scored_result.binary_score

    print(f"---RELEVANCE SCORE: {score}---")
    if score == "yes":
        print("---DECISION: DOCS RELEVANT---")
        return "generate"
    else:
        print("---DECISION: DOCS NOT RELEVANT---")
        return "rewrite"

def generate(state):
    """
    Generate answer

    Args:
        state (message): The current state

    Returns:
        dict: The updated state with the agent response to messages
    """       
    print("--GENERATE ANSWER--")
    messages = state["messages"]
    question = messages[0].content
    last_message = messages[-1]

    docs = last_message.content

    #Prompt
    prompt = hub.pull("rlm/rag-prompt")

    #LLM
    llm = ChatOpenAI(model_name="gpt-4o-mini")

    #Post Processing
    def format_docs(docs):
        return "\n\n".join([doc.page_content for doc in docs])

    #Chain
    rag_chain = prompt | llm | StrOutputParser(format_func=format_docs)

    #Run
    response = rag_chain.invoke({"context":docs,"question":question})
    return {"messages":[response]}

def rewrite(state):
    """
    Transform the query to produce a better question
    
    Args:
        state (message): The current state

    Returns:
        dict: The updated state with re-phrased question    
    """

    print("--TRANSFORM QUERY--")

