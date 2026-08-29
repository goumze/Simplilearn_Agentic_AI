"""Graph builder for LangGraph Workflow"""

import uuid
from langgraph.graph import StateGraph, END
from src.nodes.react_node import RAGNodes


class GraphBuilder:
    """Builds and manages the LangGraph workflow"""

    def __init__(self,retriever,llm):
        self.retriever = retriever
        self.llm = llm

        """
        Initialize graph builder
        
        Args:
         retriever: The document retriever to use for fetching relevant documents.
         llm: The language model to use for generating answers.
        
        """
        self.nodes=RAGNodes(retriever=self.retriever,llm=self.llm)
        self.graph=None

    def build(self):
        """
        Build the LangGraph workflow.

        Returns:
         Compiled Graph Instance.
        """
        # Use simple dict annotation instead of RAGState class
        builder = StateGraph(dict)

        builder.add_node("retriever",RAGNodes(retriever=self.retriever,llm=self.llm).retrieve_documents)
        builder.add_node("responder",RAGNodes(retriever=self.retriever,llm=self.llm).generate_answer)

        builder.set_entry_point("retriever")

        builder.add_edge("retriever","responder")
        builder.add_edge("responder", END)

        self.graph = builder.compile()
        return self.graph

    def run(self,question):
        """
        Run the RAG workflow

        Args:
            question: User question

        Returns:
            Final State with answer
        """

        if self.graph is None:
            self.build()

        initial_state = {
            "question": question,
            "retrieved_docs": [],
            "answer": "",
            "tool_calls": []
        }
        final_state = self.graph.invoke(initial_state)
        return final_state