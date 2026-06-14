from langchain_core.documents import Document
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from typing import List

class SmartPDFProcessor:
    """ Advanced PDF Processing with error handling """
    def __init__(self, chunkSize=1000, chunkOverlap=100):
        self.chunkSize = chunkSize
        self.chunkOverlap = chunkOverlap
        self.text_splitter = RecursiveCharacterTextSplitter(
            separators=[" "],  # Try to split by paragraphs, then lines, then words, then characters
            chunk_size=self.chunkSize,
            chunk_overlap=self.chunkOverlap,
            length_function=len
        )

    def process_pdf(self, pdf_path:str) -> List[Document]:
        """ Load and split PDF into chunks """
        loader = PyPDFLoader(pdf_path)
        pages = loader.load()
        
        processed_chunks = []
        for page_num, page in enumerate(pages):
            cleaned_text = self._clean_text(page.page_content)
            #Skip empty pages
            if len(cleaned_text.strip()) < 50:
                print(f"Skipping empty page {page_num + 1}")
                continue

            chunks = self.text_splitter.create_documents(texts=[cleaned_text], 
                                                         metadatas=[{
                                                          **page.metadata,
                                                          "page_number": page_num + 1,
                                                          "total_pages": len(pages),
                                                          "chunk_method": "smart_pdf_processor",
                                                          "char_count": len(cleaned_text)
                                                         }])
            processed_chunks.extend(chunks)

        return processed_chunks

    def _clean_text(self, text: str) -> str:
        """ Clean extracted PDF text """
        import re
        # Remove extra whitespace and newlines
        text = re.sub(r'\n+', '\n', text)
        text = re.sub(r'[ \t]+', ' ', text)
        # Remove ligatures
        text = text.replace('\ufb01', 'fi').replace('\ufb02', 'fl')
        return text.strip()
