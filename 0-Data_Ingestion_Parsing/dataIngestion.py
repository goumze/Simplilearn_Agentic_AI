import os
from typing import List, Dict, Any
import pandas as pd
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter, CharacterTextSplitter, TokenTextSplitter
from langchain_community.document_loaders import TextLoader
from langchain_community.document_loaders import DirectoryLoader

if __name__ == "__main__":
    doc = Document(page_content="This is the main text content that will be embedded and searched.", 
                    metadata={
                        "source": "example.txt", 
                        "page": 1,
                        "author": "John Doe", 
                        "date": "2024-06-01"
                    }
                )

    print("Document Structure")
    print(f"Content: {doc.page_content}")
    print(f"Metadata: {doc.metadata}")

    os.makedirs("data/text_files", exist_ok=True)

    sample_text = {"data/text_files/sample.txt": """Python Programming Introduction
Python is a versatile programming language that is widely used for various applications, including web development, data analysis, artificial intelligence, and more. It was created by Guido van Rossum and first released in 1991. Python's design philosophy emphasizes code readability and simplicity, making it an excellent choice for both beginners and experienced developers.    
Key Features of Python
1. Easy to Learn and Use: Python's syntax is clear and straightforward, which makes it
   easy for beginners to learn and use. It allows developers to express concepts in fewer lines of code compared to other programming languages.
2. Extensive Libraries: Python has a vast standard library and a rich ecosystem of third-party libraries that provide functionality for various tasks, such as data manipulation (Pandas), machine learning (Scikit-learn), and web development (Django).
3. Cross-Platform Compatibility: Python is a cross-platform language, meaning it can run on various operating systems, including Windows, macOS, and Linux, without requiring significant changes to the code.
4. Community Support: Python has a large and active community of developers who contribute to its growth and provide support through forums, tutorials, and documentation.
5. Versatility: Python can be used for a wide range of applications, from simple scripting to complex web applications and scientific computing. It is also popular in fields like data science, artificial intelligence, and automation.
In conclusion, Python's simplicity, extensive libraries, cross-platform compatibility, strong community support, and versatility make it a powerful programming language that continues to grow in popularity across various industries."""}

    for filepath, content in sample_text.items():
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)

    print("Sample text file created at: data/text_files/sample.txt")

    loader = TextLoader("data/text_files/sample.txt", encoding="utf-8")
    documents = loader.load()
    print(f"Loaded {len(documents)} document(s) from the text file.")
    print(type(documents[0]))
    print(f"Document content: {documents[0].page_content[:100]}...")  # Print the first 100 characters of the document content
    print(f"Document metadata: {documents[0].metadata}")

    dir_loader = DirectoryLoader("data/text_files", glob="*.txt",
      loader_cls=TextLoader,
      show_progress=True,
      loader_kwargs={"encoding": "utf-8"})

    documents = dir_loader.load()
    print(f"Loaded {len(documents)} document(s) from the directory.")
    for i, doc in enumerate(documents):
        print(f"\nDocument {i+1}:")
        print(f"Content: {doc.page_content[:100]}...")  # Print the first 100 characters of the document content
        print(f"Metadata: {doc.metadata}")



