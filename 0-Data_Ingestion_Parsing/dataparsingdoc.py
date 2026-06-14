from docx import Document as DocxDocument
import os
from langchain_community.document_loaders import Docx2txtLoader,UnstructuredWordDocumentLoader

if __name__ == "__main__":
    #Method 1: Docx2txtLoader (Basic & Fast)
    print("--------Docx2txtLoader---------------------------")
    file_path = "data/docs/RAG_Implementation_Blueprint.docx"
    try:
        loader = Docx2txtLoader(file_path)
        documents = loader.load()
        print(f"Loaded {len(documents)} pages from {file_path}")
        for page_num, page in enumerate(documents):
            print(f"\nPage {page_num + 1}:")
            print(f"Content: {page.page_content[:100]}...")  # Print the first 100 characters of the document content
            print(f"Metadata: {page.metadata}")
    except Exception as e:
        print(f"Error loading DOCX with Docx2txtLoader: {e}")


     #Method 2: UnstructuredWordDocumentLoader (Fast & Accurate)
    print("--------UnstructuredWordDocumentLoader---------------------------")
    try:
        loader = UnstructuredWordDocumentLoader(file_path,mode="elements")
        documents = loader.load()
        print(f"Loaded {len(documents)} pages from {file_path}")
        for page_num, page in enumerate(documents):
            print(f"\nPage {page_num + 1}:")
            print(f"Content: {page.page_content[:100]}...")  # Print the first 100 characters of the document content
            print(f"Metadata: {page.metadata}")
    except Exception as e:
        print(f"Error loading DOCX with UnstructuredWordDocumentLoader: {e}")   

