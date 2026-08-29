""" LangGraph nodes for RAG workflow """

from __future__ import annotations

import uuid
from typing import Annotated, Optional
from langchain_core.tools import tool
from langgraph.prebuilt import create_react_agent


class RAGNodes:
    """Contains the node functions for RAG workflow using ReAct pattern"""

    def __init__(self, retriever, llm):
        self.retriever = retriever
        self.llm = llm
        self.agent = None
        self._build_agent()

    def _build_agent(self):
        """Build ReAct agent with tools"""
        
        # Define retrieval tool
        @tool
        def retrieve_documents(question: str) -> str:
            """Retrieve relevant documents for the question"""
            try:
                docs = self.retriever.invoke(question)
                if not docs:
                    return "No documents found"
                
                context = "Retrieved documents:\n"
                for i, doc in enumerate(docs[:5], start=1):
                    meta = getattr(doc, "metadata", {}) if hasattr(doc, "metadata") else {}
                    title = meta.get("title") or meta.get("source") or f"doc_{i}"
                    content = getattr(doc, "page_content", str(doc))
                    context += f"\n[{i}] {title}\n{content}"
                return context
            except Exception as e:
                return f"Error retrieving documents: {str(e)}"
        
        tools = [retrieve_documents]
        
        # Create ReAct agent
        self.agent = create_react_agent(
            self.llm,
            tools
        )
    
    def retrieve_documents(self, state):
        """Retrieve documents for the question"""
        docs = self.retriever.invoke(state["question"])
        state["retrieved_docs"] = docs
        return state

    def generate_answer(self, state):
        """
        Generate Answer using ReAct agent with retrieved documents
        """
        if self.agent is None:
            self._build_agent()
        
        # Prepare messages for the agent
        from langchain_core.messages import HumanMessage, ToolMessage, AIMessage
        
        messages = [HumanMessage(content=state["question"])]
        
        try:
            # Run the agent
            result = self.agent.invoke({"messages": messages})
            
            # Extract full message history to show tool usage
            tool_calls_log = []
            if isinstance(result, dict) and "messages" in result:
                all_messages = result["messages"]
                
                # Extract tool invocations and results
                for i, msg in enumerate(all_messages):
                    if hasattr(msg, "tool_calls") and msg.tool_calls:
                        # This is an AI message with tool calls
                        for tool_call in msg.tool_calls:
                            tool_calls_log.append({
                                "tool_name": tool_call.get("name", "unknown"),
                                "tool_input": tool_call.get("args", {}),
                                "type": "tool_call"
                            })
                    elif isinstance(msg, ToolMessage):
                        # This is a tool result message
                        tool_calls_log.append({
                            "tool_name": msg.tool_name if hasattr(msg, "tool_name") else "unknown",
                            "tool_result": msg.content if hasattr(msg, "content") else str(msg),
                            "type": "tool_result"
                        })
                
                # Get the final answer (last message)
                if all_messages:
                    last_message = all_messages[-1]
                    answer = getattr(last_message, "content", str(last_message))
                else:
                    answer = "No answer generated"
            else:
                answer = str(result)
                tool_calls_log = []
            
            state["answer"] = answer or "Could not generate answer"
            state["tool_calls"] = tool_calls_log
        except Exception as e:
            state["answer"] = f"Error generating answer: {str(e)}"
            state["tool_calls"] = []
        
        return state

