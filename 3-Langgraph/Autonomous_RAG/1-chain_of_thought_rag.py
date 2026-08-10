"""
Simple Chain of Thought RAG System with LangGraph Orchestration
"""
import os
from typing import Annotated, TypedDict, Sequence
from dotenv import load_dotenv
from langchain_community.vectorstores import FAISS
from langchain_community.document_loaders import WebBaseLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from langgraph.graph import StateGraph, END, add_messages

load_dotenv()

# ============================================================================
# STATE DEFINITION
# ============================================================================

class CoTRAGState(TypedDict):
    """State for LangGraph orchestration"""
    messages: Annotated[Sequence[BaseMessage], add_messages]
    retrieved_docs: list
    reasoning: str
    answer: str


# ============================================================================
# MODULE 1: RAG - Document Loading and Retrieval
# ============================================================================

class RAGModule:
    """Handles document loading, chunking, and retrieval"""
    
    def __init__(self, urls: list):
        self.urls = urls
        self.retriever = self._build_retriever()
    
    def _build_retriever(self):
        """Load documents and build FAISS retriever"""
        os.environ.setdefault('USER_AGENT', 'CoT-RAG-Agent/1.0')
        
        # Load documents
        docs = [WebBaseLoader(url).load() for url in self.urls]
        doc_list = [doc for sublist in docs for doc in sublist]
        
        # Split documents
        splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
        doc_splits = splitter.split_documents(doc_list)
        
        # Create vector store
        vectorstore = FAISS.from_documents(doc_splits, OpenAIEmbeddings())
        return vectorstore.as_retriever()
    
    def retrieve(self, query: str, k: int = 3) -> list:
        """Retrieve documents for a query"""
        return self.retriever.invoke(query)

# ============================================================================
# MODULE 2: CHAIN OF THOUGHT - Reasoning Engine
# ============================================================================

class ChainOfThought:
    """Implements CoT reasoning strategy"""
    
    def __init__(self, llm_model: str = "gpt-4o", temperature: float = 0.3):
        self.llm = ChatOpenAI(model_name=llm_model, temperature=temperature)
    
    def reason(self, question: str, context: str) -> str:
        """Execute Chain of Thought reasoning"""
        template = """You are a reasoning assistant. Follow these steps:

1. STEP 1 - UNDERSTAND: Analyze the user's question
2. STEP 2 - RETRIEVE CONTEXT: Use the provided context
3. STEP 3 - REASON: Think step-by-step about how context answers the question
4. STEP 4 - ANSWER: Provide a grounded answer

Format your response as:
UNDERSTANDING: [Brief analysis of the question]
REASONING: [Your step-by-step thought process]
ANSWER: [Final answer based on context]

User Question: {question}

Context from sources:
{context}

Now reason through this step by step."""
        
        prompt = ChatPromptTemplate.from_template(template)
        response = self.llm.invoke(prompt.format(question=question, context=context))
        return response.content


# ============================================================================
# MODULE 3: LANGGRAPH NODES
# ============================================================================

# Initialize modules
rag_module = None
cot_engine = None

def retrieval_node(state: CoTRAGState) -> CoTRAGState:
    """LangGraph node: Retrieve documents"""
    query = state["messages"][-1].content if state["messages"] else ""
    
    retrieved_docs = rag_module.retrieve(query, k=3)
    
    return {
        "retrieved_docs": retrieved_docs,
        "messages": state["messages"]
    }

def reasoning_node(state: CoTRAGState) -> CoTRAGState:
    """LangGraph node: Apply Chain of Thought"""
    query = state["messages"][-1].content if state["messages"] else ""
    retrieved_docs = state["retrieved_docs"]
    
    if not retrieved_docs:
        reasoning_result = "No relevant documents found"
    else:
        context = "\n".join([f"Source {i+1}:\n{doc.page_content}" for i, doc in enumerate(retrieved_docs)])
        reasoning_result = cot_engine.reason(query, context)
    
    return {
        "reasoning": reasoning_result,
        "messages": state["messages"]
    }

def answer_node(state: CoTRAGState) -> CoTRAGState:
    """LangGraph node: Format final answer"""
    reasoning = state["reasoning"]
    answer = reasoning
    
    return {
        "answer": answer,
        "messages": state["messages"] + [AIMessage(content=answer)]
    }


# ============================================================================
# MODULE 4: LANGGRAPH BUILDER
# ============================================================================

def build_graph(urls: list):
    """Build LangGraph workflow"""
    global rag_module, cot_engine
    
    # Initialize modules
    rag_module = RAGModule(urls)
    cot_engine = ChainOfThought()
    
    # Create state graph
    workflow = StateGraph(CoTRAGState)
    
    # Add nodes
    workflow.add_node("retrieve", retrieval_node)
    workflow.add_node("reason", reasoning_node)
    workflow.add_node("answer", answer_node)
    
    # Add edges
    workflow.add_edge("retrieve", "reason")
    workflow.add_edge("reason", "answer")
    workflow.add_edge("answer", END)
    
    # Set entry point
    workflow.set_entry_point("retrieve")
    
    return workflow.compile()


# ============================================================================
# MODULE 5: EXECUTION
# ============================================================================

def main():
    """Main execution function"""
    
    # Initialize URLs
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
    
    # Build LangGraph workflow
    graph = build_graph(urls)
    
    # Test queries
    test_queries = [
        "What is LangGraph?",
        "How does LangGraph compare to LangChain?",
        "What are the key features of LangGraph?"
    ]

    negative_test_queries = [
        "What is the capital of Mars?",
        "How does LangGraph compare to a toaster?",
        "What are the key features of a unicorn?"
    ]
    
    # Process each query through the graph
    # for query in test_queries:
    #     print("\n" + "="*80)
    #     print(f"Query: {query}")
    #     print("="*80)
        
    #     initial_state = {
    #         "messages": [HumanMessage(content=query)],
    #         "retrieved_docs": [],
    #         "reasoning": "",
    #         "answer": ""
    #     }
        
    #     result = graph.invoke(initial_state)
        
    #     print(f"\nRetrieval Count: {len(result['retrieved_docs'])}")
    #     print(f"Retrieved Sources: {len(result['retrieved_docs'])}")
    #     print(f"\nReasoning & Answer:\n{result['answer']}")
    #     print("="*80)

    for query in negative_test_queries:
            print("\n" + "="*80)
            print(f"Query: {query}")
            print("="*80)
            
            initial_state = {
                "messages": [HumanMessage(content=query)],
                "retrieved_docs": [],
                "reasoning": "",
                "answer": ""
            }
            
            result = graph.invoke(initial_state)
            
            print(f"\nRetrieval Count: {len(result['retrieved_docs'])}")
            print(f"Retrieved Sources: {len(result['retrieved_docs'])}")
            print(f"\nReasoning & Answer:\n{result['answer']}")
            print("="*80)    


if __name__ == "__main__":
    main()
