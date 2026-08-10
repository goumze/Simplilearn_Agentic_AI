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
        self.sample_docs = self._get_sample_documents()
        self.retriever = self._build_retriever()
    
    def _get_sample_documents(self):
        """Fallback: Sample documents about LangGraph if URLs fail"""
        from langchain_core.documents import Document
        
        return [
            Document(
                page_content="LangGraph is a library for building stateful, multi-actor applications with large language models (LLMs), built on top of LangChain. It extends LangChain's capabilities by providing a way to coordinate multiple chains and tools through a graph-based approach. LangGraph allows you to define complex workflows where different components can pass messages and state to each other, enabling more sophisticated agent behaviors and multi-step reasoning.",
                metadata={"source": "langgraph-docs-overview"}
            ),
            
            Document(
                page_content="LangGraph vs LangChain: LangChain is focused on chaining LLM calls and managing prompts, while LangGraph adds state management and cyclical workflows on top of LangChain. LangChain is best for simple sequential chains, whereas LangGraph excels at building agents that need to loop, make decisions, and maintain state across multiple steps. LangGraph provides built-in support for agentic patterns and human-in-the-loop workflows.",
                metadata={"source": "langgraph-docs-comparison"}
            ),
            
            Document(
                page_content="Key features of LangGraph include: 1) State management - persistent state across graph executions, 2) Cyclical workflows - support for loops and conditional routing, 3) Tool integration - seamless integration with external tools and APIs, 4) Human-in-the-loop - ability to pause execution and get human input, 5) Streaming - support for real-time output streaming, 6) Persistence - ability to save and load graph states.",
                metadata={"source": "langgraph-docs-features"}
            ),
            
            Document(
                page_content="LangGraph vs LangFlow: LangFlow is a UI-based visual builder for LangChain workflows, while LangGraph is a programmatic library for building complex agent systems. LangGraph provides more control and flexibility for developers, while LangFlow provides a visual interface for non-technical users. LangGraph is better for production systems requiring complex logic and customization.",
                metadata={"source": "langgraph-docs-langflow-comparison"}
            ),
            
            Document(
                page_content="LangGraph vs LangServe: LangServe is a library for deploying LangChain applications as REST APIs, while LangGraph is for building the application logic itself. They complement each other - you build your application logic with LangGraph and then deploy it with LangServe. LangServe handles the server infrastructure, while LangGraph handles the AI logic and workflows.",
                metadata={"source": "langgraph-docs-langserve-comparison"}
            ),
        ]
    
    def _load_url_safe(self, url: str) -> list:
        """Safely load a URL with error handling"""
        try:
            loader = WebBaseLoader(url, header_template={"User-Agent": "Mozilla/5.0"})
            docs = loader.load()
            # Filter documents with meaningful content
            valid_docs = [doc for doc in docs if len(doc.page_content.strip()) > 100]
            if valid_docs:
                print(f"✓ Loaded {url}: {len(valid_docs)} document(s), {sum(len(d.page_content) for d in valid_docs)} chars")
            return valid_docs
        except Exception as e:
            print(f"✗ Failed to load {url}: {type(e).__name__}")
            return []
    
    def _build_retriever(self):
        """Load documents and build FAISS retriever"""
        os.environ.setdefault('USER_AGENT', 'CoT-RAG-Agent/1.0')
        
        print("\n[RAG] Loading documents...")
        # Load documents with error handling
        doc_list = []
        for url in self.urls:
            docs = self._load_url_safe(url)
            doc_list.extend(docs)
        
        # Fallback to sample documents if URLs fail
        if not doc_list:
            print("[RAG] URLs failed to load. Using sample documents.")
            doc_list = self.sample_docs
            print(f"[RAG] Loaded {len(doc_list)} sample documents")
        else:
            print(f"[RAG] Total documents loaded from URLs: {len(doc_list)}")
        
        # Split documents with better chunking
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,  # Larger chunks to preserve context
            chunk_overlap=200,  # More overlap for continuity
            separators=["\n\n", "\n", ".", " "]
        )
        doc_splits = splitter.split_documents(doc_list)
        print(f"[RAG] Total chunks created: {len(doc_splits)}")
        
        if not doc_splits:
            print("[RAG] ERROR: No chunks created!")
            return None
        
        # Create vector store
        vectorstore = FAISS.from_documents(doc_splits, OpenAIEmbeddings())
        print(f"[RAG] Vector store ready with {len(doc_splits)} chunks\n")
        return vectorstore.as_retriever(search_kwargs={"k": 3})
    
    def retrieve(self, query: str, k: int = 3) -> list:
        """Retrieve documents for a query"""
        if not self.retriever:
            return []
        docs = self.retriever.invoke(query)
        print(f"[Retrieval] Query: '{query}' -> {len(docs)} documents found")
        return docs

# ============================================================================
# MODULE 2: CHAIN OF THOUGHT - Reasoning Engine
# ============================================================================

class ChainOfThought:
    """Implements CoT reasoning strategy"""
    
    def __init__(self, llm_model: str = "gpt-4o", temperature: float = 0.3):
        self.llm = ChatOpenAI(model_name=llm_model, temperature=temperature)
    
    def reason(self, question: str, context: str) -> str:
        """Execute Chain of Thought reasoning"""
        template = """You are a reasoning assistant. IMPORTANT: You MUST ONLY answer from the provided context. If the context does not contain relevant information, refuse to answer.

Follow these steps:

1. STEP 1 - UNDERSTAND: Analyze the user's question
2. STEP 2 - CHECK CONTEXT: Is there relevant information in the provided context?
3. STEP 3 - REASON: If yes, think step-by-step about how context answers the question
4. STEP 4 - ANSWER: Provide a grounded answer OR refuse if context is insufficient

Format your response as:
UNDERSTANDING: [Brief analysis of the question]
REASONING: [Your step-by-step thought process or why context is insufficient]
ANSWER: [Final answer based ONLY on provided context, or "I cannot answer this question based on the provided sources."]

User Question: {question}

Context from sources:
{context}

IMPORTANT: If the context above does NOT contain information to answer the question, you MUST say: "I cannot answer this question based on the provided sources."

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
    
    retrieved_docs = rag_module.retrieve(query, k=3) if rag_module else []
    
    # Debug: Show what was retrieved
    if retrieved_docs:
        print(f"[Debug] Retrieved content preview:")
        for i, doc in enumerate(retrieved_docs[:2], 1):
            preview = doc.page_content[:150].replace("\n", " ")[:150]
            print(f"  Source {i}: {preview}...")
    
    return {
        "retrieved_docs": retrieved_docs,
        "messages": state["messages"]
    }

def reasoning_node(state: CoTRAGState) -> CoTRAGState:
    """LangGraph node: Apply Chain of Thought"""
    query = state["messages"][-1].content if state["messages"] else ""
    retrieved_docs = state["retrieved_docs"]
    
    if not retrieved_docs:
        reasoning_result = "I cannot answer this question based on the provided sources."
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
    print("\n" + "="*80)
    print("TESTING VALID QUERIES (should answer from sources)")
    print("="*80)
    
    for query in test_queries:
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
        print(f"Retrieved Sources: {[doc.metadata['source'] for doc in result['retrieved_docs']]}")
        print(f"\nReasoning & Answer:\n{result['answer']}")
        print("="*80)

    print("\n" + "="*80)
    print("TESTING INVALID QUERIES (should refuse to answer)")
    print("="*80)
    
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
            print(f"Retrieved Sources: {[doc.metadata['source'] for doc in result['retrieved_docs']]}")
            print(f"\nReasoning & Answer:\n{result['answer']}")
            print("="*80)    


if __name__ == "__main__":
    main()
