"""Streamlit UI for Agentic RAG System - Simplified Version"""

import streamlit as st
from pathlib import Path
import sys
import time
import uuid

# Add src to path
sys.path.append(str(Path(__file__).parent))

from src.config.config import Config
from src.document_ingestion.document_processor import DocumentProcessor
from src.vectorstore.vectorstore import VectorStore
from src.graph_builder.graph_builder import GraphBuilder

# Page configuration
st.set_page_config(
    page_title="🤖 RAG Search",
    page_icon="🔍",
    layout="centered"
)

# Simple CSS
st.markdown("""
    <style>
    .stButton > button {
        width: 100%;
        background-color: #4CAF50;
        color: white;
        font-weight: bold;
    }
    </style>
""", unsafe_allow_html=True)

def init_session_state():
    """Initialize session state variables"""
    if 'rag_system' not in st.session_state:
        st.session_state.rag_system = None
    if 'initialized' not in st.session_state:
        st.session_state.initialized = False
    if 'history' not in st.session_state:
        st.session_state.history = []

@st.cache_resource
def initialize_rag():
    """Initialize the RAG system (cached)"""
    import logging
    logger = logging.getLogger(__name__)
    
    try:
        logger.info("Starting RAG initialization...")
        
        # Initialize components
        logger.info("Getting LLM configuration...")
        llm = Config.get_llm()
        
        logger.info("Creating document processor...")
        doc_processor = DocumentProcessor(
            chunk_size=Config.CHUNK_SIZE,
            chunk_overlap=Config.CHUNK_OVERLAP
        )
        
        logger.info("Creating vector store...")
        vector_store = VectorStore()
        
        # Use default URLs
        urls = Config.DEFAULT_URLS
        logger.info(f"Processing {len(urls)} URLs...")
        
        # Process documents
        logger.info("Loading and processing documents...")
        documents = doc_processor.process_urls(urls)
        logger.info(f"Loaded {len(documents)} document chunks")
        
        # Create vector store
        logger.info("Creating vector store from documents...")
        vector_store.create_vectorstore(documents)
        logger.info("Vector store created successfully")
        
        # Build graph
        logger.info("Building RAG graph...")
        graph_builder = GraphBuilder(
            retriever=vector_store.get_retriever(),
            llm=llm
        )
        graph_builder.build()
        logger.info("RAG graph built successfully")
        
        return graph_builder, len(documents)
    except Exception as e:
        import traceback
        logger.error(f"Failed to initialize RAG: {str(e)}")
        logger.error(traceback.format_exc())
        raise

def main():
    """Main application"""
    init_session_state()
    
    # Title
    st.title("🔍 RAG Document Search")
    st.markdown("Ask questions about the loaded documents")
    
    # Initialize system
    if not st.session_state.initialized:
        with st.spinner("Loading system..."):
            rag_system, num_chunks = initialize_rag()
            if rag_system:
                st.session_state.rag_system = rag_system
                st.session_state.initialized = True
                st.success(f"✅ System ready! ({num_chunks} document chunks loaded)")
    
    st.markdown("---")
    
    # Search interface
    with st.form("search_form"):
        question = st.text_input(
            "Enter your question:",
            placeholder="What would you like to know?"
        )
        submit = st.form_submit_button("🔍 Search")
    
    # Process search
    if submit and question:
        if st.session_state.rag_system:
            with st.spinner("Searching..."):
                start_time = time.time()
                
                # Get answer
                result = st.session_state.rag_system.run(question)
                
                elapsed_time = time.time() - start_time
                
                # Handle result as RAGState object or dict
                answer = result.answer if hasattr(result, 'answer') else result.get('answer', 'No answer generated')
                retrieved_docs = result.retrieved_docs if hasattr(result, 'retrieved_docs') else result.get('retrieved_docs', [])
                tool_calls = result.tool_calls if hasattr(result, 'tool_calls') else result.get('tool_calls', [])
                
                # Add to history
                st.session_state.history.append({
                    'question': question,
                    'answer': answer,
                    'time': elapsed_time
                })
                
                # Display answer
                st.markdown("### 💡 Answer")
                st.success(answer)
                
                # Show tool usage and reasoning
                if tool_calls:
                    with st.expander("🔧 Agent Reasoning & Tool Usage"):
                        st.markdown("**The agent used the following tools:**")
                        for i, tool_call in enumerate(tool_calls, 1):
                            tool_type = tool_call.get("type", "unknown")
                            if tool_type == "tool_call":
                                tool_name = tool_call.get("tool_name", "unknown")
                                st.markdown(f"**Step {i}: Tool Called - `{tool_name}`**")
                                tool_input = tool_call.get("tool_input", {})
                                if tool_input:
                                    st.json(tool_input)
                            elif tool_type == "tool_result":
                                tool_name = tool_call.get("tool_name", "unknown")
                                st.markdown(f"**Step {i}: Tool Result from `{tool_name}`**")
                                result_preview = tool_call.get("tool_result", "")
                                if isinstance(result_preview, str) and len(result_preview) > 500:
                                    st.markdown(f"```\n{result_preview[:500]}...\n```")
                                else:
                                    st.markdown(f"```\n{result_preview}\n```")
                else:
                    st.info("ℹ️ No tools were used (answer generated from LLM knowledge)")
                
                # Show retrieved docs in expander
                if retrieved_docs:
                    with st.expander("📄 Source Documents"):
                        for i, doc in enumerate(retrieved_docs, 1):
                            content = doc.page_content if hasattr(doc, 'page_content') else str(doc)
                            st.text_area(
                                f"Document {i}",
                                content[:300] + "...",
                                height=100,
                                disabled=True
                            )
                
                st.caption(f"⏱️ Response time: {elapsed_time:.2f} seconds")
    
    # Show history
    if st.session_state.history:
        st.markdown("---")
        st.markdown("### 📜 Recent Searches")
        
        for item in reversed(st.session_state.history[-3:]):  # Show last 3
            with st.container():
                st.markdown(f"**Q:** {item['question']}")
                st.markdown(f"**A:** {item['answer'][:200]}...")
                st.caption(f"Time: {item['time']:.2f}s")
                st.markdown("")

if __name__ == "__main__":
    main()