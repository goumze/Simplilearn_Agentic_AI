import os
from pydoc import doc
from typing import List, Annotated, Literal
from langchain_classic.prompts import PromptTemplate
from langchain_community.tools import WikipediaQueryRun
from langchain_community.utilities import WikipediaAPIWrapper
from langchain_core.output_parsers import StrOutputParser
from langchain_core.tools import Tool
from langgraph.prebuilt import ToolNode, tools_condition
from pydantic import BaseModel, Field
from langchain_community.vectorstores import FAISS
from langchain_community.document_loaders import WebBaseLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain.chat_models import init_chat_model
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_core.documents import Document
from langgraph.graph import StateGraph,END, add_messages
from typing import TypedDict, Sequence
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, ToolMessage
from langchain_core.tools import create_retriever_tool

import json
from dotenv import load_dotenv
load_dotenv()

# Set USER_AGENT for WebBaseLoader if not already set
if not os.getenv('USER_AGENT'):
    os.environ['USER_AGENT'] = 'SimplilearnRagAgent/1.0'

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

retriever_tool_langgraph = create_retriever_tool(retriever,"retriever_vector_db_blog","Search and run information about LangGraph.")

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

tools = [retriever_tool_langgraph,retriever_tool_langchain]

#Workflow
class AgentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], add_messages]
    retry_count: int

def agent(state):
    """
    Invokes the agent model to generate a response based on the current state. Given the question,
    it will decide to retrieve using the retriever tool, or simply end if the relevant information is not present in the documents.

    Args:
        state (AgentState): The current state of the agent, including messages.

    Returns:
        dict: The updated state with the agent response to messages    
    """    

    print("--CALL AGENT--")
    messages = state["messages"]

    model = ChatOpenAI(model_name="gpt-4o-mini")
    model = model.bind_tools(tools)
    response = model.invoke(messages)
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
    Generate answer ONLY from provided sources. 
    Strictly enforces that answers must be grounded in retrieved documents.

    Args:
        state (message): The current state

    Returns:
        dict: The updated state with the agent response to messages
    """       
    print("--GENERATE ANSWER FROM SOURCES--")
    messages = state["messages"]
    
    # Find the original question
    question = messages[0].content
    for msg in messages:
        if isinstance(msg, HumanMessage) and msg.content and "?" in msg.content:
            question = msg.content
            break
    
    last_message = messages[-1]

    docs = last_message.content

    #Prompt - Strictly enforce source-based answers
    prompt = PromptTemplate(
        template="""You are a helpful assistant that answers questions ONLY based on the provided source documents.

IMPORTANT RULES:
1. Answer ONLY using information from the provided context
2. Do NOT use any external knowledge or general knowledge
3. If the answer cannot be found in the context, respond with: "I cannot answer this question based on the provided sources."
4. Always cite which source document your answer comes from
5. Be precise and factual

Question: {question}
Context: {context}
Answer:""",
        input_variables=["question", "context"]
    )

    #LLM
    llm = ChatOpenAI(model_name="gpt-4o-mini")

    #Post Processing
    def format_docs(docs):
        return "\n\n".join([doc.page_content for doc in docs])

    #Chain
    rag_chain = prompt | llm | StrOutputParser()

    #Run
    response = rag_chain.invoke({"context":docs,"question":question})
    return {"messages":[response]}

def rewrite(state):
    """
    Transform the query to produce a better question. 
    Tracks retry attempts and stops after max retries.
    
    Args:
        state (message): The current state

    Returns:
        dict: The updated state with re-phrased question and incremented retry count   
    """

    print("--TRANSFORM QUERY--")
    
    # Increment retry counter
    retry_count = state.get("retry_count", 0) + 1
    max_retries = 3
    
    print(f"Retry attempt {retry_count}/{max_retries}")
    
    # If max retries exceeded, return end signal
    if retry_count >= max_retries:
        print(f"---MAX RETRIES ({max_retries}) EXCEEDED---")
        print("---UNABLE TO FIND RELEVANT SOURCES---")
        end_message = HumanMessage(content="MAX_RETRIES_EXCEEDED")
        return {"messages": [end_message], "retry_count": retry_count}

    messages = state["messages"]
    # Find the original question (first user message)
    question = messages[0].content
    
    # Handle case where first message might be a system message
    for msg in messages:
        if isinstance(msg, HumanMessage) and msg.content and "?" in msg.content:
            question = msg.content
            break

    msg = [
        HumanMessage(content=f"""
        \n
        Look at the input and try to reason about the underlying semantic intent / meaning. \n
        Here is the initial question:
        \n-----------\n
        {question}
        \n-----------\n
        Formulate an improved question. In your response, only provide the rewritten question. Do not include any other text or explanation.
        """)
    ]
    model = ChatOpenAI(model_name="gpt-4o-mini")
    response = model.invoke(msg)
    print("Rewritten Question: ",response.content)
    return {"messages": [response], "retry_count": retry_count}

#Function to handle case when max retries exceeded
def cannot_answer_from_sources(state):
    """
    Return a message indicating the query cannot be answered from the provided sources.
    This is called when max retries are exceeded.
    """
    final_message = AIMessage(content="I cannot answer this question based on the provided sources. The information you're looking for is not available in the knowledge bases I have access to.")
    return {"messages": [final_message]}

#Function to route from rewrite based on retry count
def route_after_rewrite(state):
    """
    Route the workflow after rewrite: either continue with agent or end if max retries exceeded.
    """
    retry_count = state.get("retry_count", 0)
    max_retries = 3
    
    # Check if last message indicates max retries
    last_message = state["messages"][-1]
    if isinstance(last_message, HumanMessage) and last_message.content == "MAX_RETRIES_EXCEEDED":
        return "cannot_answer"
    
    if retry_count >= max_retries:
        return "cannot_answer"
    
    return "agent"

#Initialise the state graph
workflow = StateGraph(AgentState)

#add nodes
retrieve = ToolNode([retriever_tool_langgraph, retriever_tool_langchain])
workflow.add_node("agent",agent)
workflow.add_node("retriever", retrieve)
workflow.add_node("rewrite", rewrite)
workflow.add_node("generate", generate)
workflow.add_node("cannot_answer", cannot_answer_from_sources)

workflow.set_entry_point("agent")
workflow.add_conditional_edges("agent",tools_condition,{"tools":"retriever",END: END})
workflow.add_conditional_edges("retriever", grade_documents)
workflow.add_edge("generate",END)
workflow.add_conditional_edges("rewrite", route_after_rewrite, {"agent": "agent", "cannot_answer": "cannot_answer"})
workflow.add_edge("cannot_answer",END)

#Compile
graph = workflow.compile()

if __name__ == "__main__":
    user_query = "What is a Langgraph ?"
    result = graph.invoke({"messages":[HumanMessage(content=user_query)], "retry_count": 0})  
    print("\n" + "="*80)
    print("AGENT RAG RESPONSE")
    print("="*80)
    print(result["messages"][-1].content)





