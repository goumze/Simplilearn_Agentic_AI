"""
Vectorstore module for handling vector storage and retrieval.

"""

from typing import List
from langchain_community.vectorstores import FAISS
from langchain_core import documents
from langchain_openai import OpenAIEmbeddings
from langchain_core.documents import Document

class Vectorstore:
    """Manages vector store application"""

    def __init__(self):
        self.embeddings = OpenAIEmbeddings()
        self.vectorstore = None
        self.retriever = None

    def create_retriever(self, documents: List[Document]):
        """
        Create vector store from documents

        Args:
        documents (List[Document]): List of documents to create the vector store from.
        """
        self.vectorstore = FAISS.from_documents(documents, self.embeddings)
        self.retriever = self.vectorstore.as_retriever()

    def get_retriever(self):
        """
        Get the retriever for the vector store.

        Returns:
        The retriever for the vector store.
        """
        if self.retriever is None:
            raise ValueError("Retriever has not been created. Call create_retriever() first.")
        return self.retriever

    
