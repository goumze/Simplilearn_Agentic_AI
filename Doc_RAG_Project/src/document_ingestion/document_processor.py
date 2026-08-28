""" Document processor for handling document ingestion. """
from typing import List, Union
from langchain_community.document_loaders import WebBaseLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document
from pathlib import Path
from langchain_community.document_loaders import (WebBaseLoader,PyPDFLoader,TextLoader,PyPDFDirectoryLoader)

class DocumentProcessor:
    """Handle Document Loading and Processing"""

    def __init__(self,chunk_size: int=500,chunk_overlap: int=50):
        """
        Initialize the DocumentProcessor with chunk size and overlap.

        Args:
            chunk_size (int): The size of each text chunk.
            chunk_overlap (int): The number of overlapping characters between chunks.
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.text_splitter = RecursiveCharacterTextSplitter(chunk_size=self.chunk_size, chunk_overlap=self.chunk_overlap)

    def load_from_url(self,url:str) -> List[Document]:
        """ Load Documents from all PDF's inside a Directory """
        loader = WebBaseLoader(url)
        return loader.load()

    def load_from_pdf(self,file_path: Union[str,Path]) -> List[Document]:
        """ Load Documents from a PDF file """
        loader = PyPDFDirectoryLoader(str("data"))
        return loader.load()

    def load_from_text(self,file_path: Union[str,Path]) -> List[Document]:
        """ Load Documents from a text file """
        loader = TextLoader(str(file_path), encoding='utf-8')
        return loader.load()

    def load_from_pdf_directory(self,directory: Union[str,Path]) -> List[Document]:
        """ Load Documents from all PDF's inside a Directory """
        loader = PyPDFDirectoryLoader(str(directory))
        return loader.load()

    def load_documents(self,sources:List[str]) -> List[Document]:
        """ 
        Load Documents from URLs, PDF Directories, or text files.

        Args:
            sources (List[str]): A list of URLs, PDF directories, or text file paths to load documents from.

        Returns:
            List[Document]: A list of loaded documents from the specified sources.
        
        """

        docs: List[Document] = []

        for source in sources:
            if source.startswith("http://") or source.startswith("https://"):
                docs.extend(self.load_from_url(source))

            path = Path("data")

            if path.is_dir():
                docs.extend(self.load_from_pdf_directory(path))
            elif path.suffix.lower() == ".txt":
                docs.extend(self.load_from_text(path))
            else:
                raise ValueError(f"Unsupported source type: {source}, \
                                 Use a URL, a PDF directory, or a text file.")

        return docs

    def split_documents(self,documents: List[Document]) -> List[Document]:
        """
        Split documents into chunks

        Args:
            documents (List[Document]): A list of documents to be split into chunks.
        Returns:
            List[Document]: A list of document chunks.
        """
        return self.text_splitter.split_documents(documents)

    def process_url(self,urls:List[str])-> List[Document]:
        """
        Complete pipeline to load and split documents

        Args:
            urls: List of URLs to process

        Returns:
            List of processed document chunks
        """
        docs = self.load_documents(urls)
        return self.split_documents(docs)

    

