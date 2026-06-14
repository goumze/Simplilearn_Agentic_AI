#Load PDF Files 
from langchain_community.document_loaders import PyPDFLoader, PyMuPDFLoader,UnstructuredPDFLoader
#from langchain_community.text_splitter import CharacterTextSplitter, RecursiveCharacterTextSplitter
import SmartPDFProcessor as smart_pdf_processor

if __name__ == "__main__":
##PyPDFLoader (Basic & Fast)
##Method 1: PyPDFLoader (Basic & Fast)
    print("--------PyPDFLoader---------------------------")
    try:
        pypdf_loader = PyPDFLoader("data/pdf_files/attention.pdf")
        pypdf_documents = pypdf_loader.load()
        print(f"Loaded {len(pypdf_documents)} pages")
        print(pypdf_documents)
        print(f"First page content: {pypdf_documents[0].page_content[:100]}...")  # Print the first 100 characters of the first page content
        print(f"First page metadata: {pypdf_documents[0].metadata}")
        for page_num, doc in enumerate(pypdf_documents):
            print(f"\nPage {page_num + 1}:")
            print(f"Content: {doc.page_content[:100]}...")  # Print the first 100 characters of the document content
            print(f"Metadata: {doc.metadata}")
    except Exception as e:
        print(f"Error loading PDF: {e}")

##Method 2: PyMuPDFLoader (Fast & Accurate)
    print("--------PyMuPDFLoader---------------------------")
    try:
        pymupdf_loader = PyMuPDFLoader("data/pdf_files/attention.pdf")
        pymupdf_documents = pymupdf_loader.load()
        print(f"Loaded {len(pymupdf_documents)} pages")
        print(f"First page content: {pymupdf_documents[0].page_content[:100]}...")  # Print the first 100 characters of the first page content
        print(f"First page metadata: {pymupdf_documents[0].metadata}")
        for page_num, doc in enumerate(pymupdf_documents):
            print(f"\nPage {page_num + 1}:")
            print(f"Content: {doc.page_content[:100]}...")  # Print the first 100 characters of the document content
            print(f"Metadata: {doc.metadata}")
    except Exception as e:
        print(f"Error loading PDF with PyMuPDFLoader: {e}")

##Handling PDF challenges

#Example of RAW PDF Extraction
raw_pdf_text = """ Company Financial Report 
     The financial performance for the fiscal year 2024
     shows significant growth in profitability.




     Revenue increased by 25%.

   The company's efficiency improved due to workflow optimization.


   Page 1 of 10
   """

#Apply Cleaning function 
def clean_raw_pdf_text(raw_text):
    # Remove extra whitespace and newlines
    cleaned_text = ' '.join(raw_text.split())

    #Remove ligatures (e.g., "ﬁ" to "fi")
    cleaned_text = cleaned_text.replace('ﬁ', 'fi').replace('ﬂ', 'fl')
    return cleaned_text
    
cleaned_pdf_text = clean_raw_pdf_text(raw_pdf_text)
print("--------Cleaned PDF Text---------------------------")
print("-----BEFORE CLEANING-----")
print(repr(raw_pdf_text[:100]) + "...")  # Print the first 100 characters of the raw PDF text
print("-----AFTER CLEANING-----")
print(repr(cleaned_pdf_text[:100]) + "...")  # Print the first 100 characters of the cleaned PDF text

#Using SmartPDFProcessor for advanced PDF processing
smart_processor = smart_pdf_processor.SmartPDFProcessor(chunkSize=100, chunkOverlap=20)
smart_chunks = smart_processor.process_pdf("data/pdf_files/attention.pdf")
print("--------SmartPDFProcessor Chunks---------------------------")
print(f"Processed into {len(smart_chunks)} smart chunks")
if(smart_chunks):
    for i, chunk in enumerate(smart_chunks):
        for key,value in chunk.metadata.items():
            print(f"Chunk {i+1} Metadata - {key}: {value}")






