"""Graph builder for LangGraph Workflow"""

from langgraph import StateGraph, END
from src.state.rag_state import RAGState


class GraphBuilder:
    """Builds and manages the LangGraph workflow"""

    def __init__(self,retriever,llm):

        """
        Initialize graph builder
        
        Args:
         retriever: The document retriever to use for fetching relevant documents.
         llm: The language model to use for generating answers.
        
        """
        self.nodes=None
        self.graph=None

    def build(self):
        """
        Build the LangGraph workflow.

        Returns:
         Compiled Graph Instance.
        """
        builder = StateGraph(RAGState)

        builder.add_node("retriever",self.nodes.retrieve_docs)
        builder.add_node("responder",self.nodes.generate_answer)

        builder.set_entry_point("retriever")

        builder.add_edge("retriever","responder")
        builder.add_edge("responder", END)

        self.graph = builder.compile()
        return self.graph