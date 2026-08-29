""" LangGraph nodes for RAG workflow """

from src.state.rag_state import RagState


class RAGNodes:
    """ Contains node functions for RAG workflow """

    def __init__(self,retriever,llm):
        """
        Initialize RAG Nodes

        Args:
            retriever: The retriever instance for fetching relevant documents.
            llm: The language model instance for processing queries.
        """
        self.retriever = retriever
        self.llm = llm


    def retrieve_documents(self, state:RagState)-> RagState:
        """
        Retrieve relevant documents node

        Args:
            state: Current RAG State

        Returns:
            Updated RAG State with retrieved documents.

        """

        docs = self.retriever.invoke(state.question)
        return RagState(question=state.question, retrieved_documents=docs)

    def generate_answer(self,state:RagState)-> RagState:
        """
        Generate answer node

        Args:
            state: Current RAG State with retrieved documents.

        Returns:
            Updated RAG State with generated answer.

        """

        context = "\n\n".join([doc.page_content for doc in state.retrieved_documents])
        prompt = f"""Answer the question based on the context

                    Context:
                    {context}

                    Question:
                    {state.question}
                """
        
                    
        answer = self.llm.invoke(prompt)
        return RagState(question=state.question, retrieved_documents=state.retrieved_documents, answer=answer)