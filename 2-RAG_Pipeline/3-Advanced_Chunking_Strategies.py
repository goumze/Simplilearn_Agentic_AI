from dotenv import load_dotenv
load_dotenv()

from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
from langchain.schema import Document
from langchain.vectorstores import FAISS
from langchain.embeddings import HuggingFaceEmbeddings, OpenAIEmbeddings
from langchain.chat_models import init_chat_model
from langchain.schema.runnable import RunnableLambda, RunnableMap
from langchain.prompts import PromptTemplate
from langchain_core.output_parsers import StructuredOutputParser
import numpy as np

#Initialize the embedding model
print("Initializing the embedding model...\n")
model = SentenceTransformer('all-MiniLM-L6-v2')

#Sample Text
print("Sample Text: \n")
text = """ 
Python Programming Introduction
Python is a versatile programming language that is widely used for various applications, including web development, data analysis, artificial intelligence, and more. It was created by Guido van Rossum and first released in 1991. Python's design philosophy emphasizes code readability and simplicity, making it an excellent choice for both beginners and experienced developers.    
Key Features of Python
1. Easy to Learn and Use: Python's syntax is clear and straightforward, which makes it
   easy for beginners to learn and use. It allows developers to express concepts in fewer lines of code compared to other programming languages.
2. Extensive Libraries: Python has a vast standard library and a rich ecosystem of third-party libraries that provide functionality for various tasks, such as data manipulation (Pandas), machine learning (Scikit-learn), and web development (Django).
3. Cross-Platform Compatibility: Python is a cross-platform language, meaning it can run on various operating systems, including Windows, macOS, and Linux, without requiring significant changes to the code.
4. Community Support: Python has a large and active community of developers who contribute to its growth and provide support through forums, tutorials, and documentation.
5. Versatility: Python can be used for a wide range of applications, from simple scripting to complex web applications and scientific computing. It is also popular in fields like data science, artificial intelligence, and automation.
In conclusion, Python's simplicity, extensive libraries, cross-platform compatibility, strong community support, and versatility make it a powerful programming language that continues to grow in popularity across various industries.
"""

#Step 1: Split into sentences
print("Step 1: Split into sentences: \n")
sentences = [s.strip() for s in text.split("\n") if s.strip()]
print("Sentences: \n")
for idx, sentence in enumerate(sentences):
    print(f"Sentence {idx + 1}: {sentence}\n")

#Step 2: Generate embeddings for each sentence
print("Step 2: Generate embeddings for each sentence: \n")
embeddings = model.encode(sentences)
print("Embeddings generated for each sentence.\n")
print("Embeddings shape: ", embeddings.shape, "\n")  # Print the shape of the embeddings array
print("Embeddings: \n", embeddings, "\n")  # Print the actual embeddings

#Step 3: Initialize parameters for chunking
print("Step 3: Initialize parameters for chunking: \n")
# Lowered threshold for better semantic grouping
threshold = 0.5  # Similarity threshold for merging sentences (0.5 = 50% similarity)
min_chunk_size = 2  # Minimum sentences per chunk
max_chunk_size = 10  # Maximum sentences per chunk (optional constraint)
chunks = []
current_chunk = [sentences[0]]

#Step 4: Semantic grouping based on threshold
print("Step 4: Semantic grouping based on threshold: \n")
print(f"Using threshold: {threshold} (lower = more lenient grouping)\n")
for i in range(1, len(sentences)):
    similarity = cosine_similarity([embeddings[i]], [embeddings[i-1]])[0][0]
    print(f"Similarity between Sentence {i} and Sentence {i-1}: {similarity:.4f}")
    print(f"Threshold: {threshold} | Group together: {similarity >= threshold}\n")
    
    if similarity >= threshold:
        current_chunk.append(sentences[i])
    else:
        # Only create a chunk if it meets minimum size or merge with next chunk if too small
        if len(current_chunk) >= min_chunk_size:
            chunks.append(" ".join(current_chunk))
            current_chunk = [sentences[i]]
        else:
            # If chunk is too small, add to it instead of starting new chunk
            current_chunk.append(sentences[i])

#Step 5: Append the last chunk
print("Step 5: Append the last chunk: \n")
if current_chunk:
    chunks.append(" ".join(current_chunk))

#Step 6: Output the chunks
print("Step 6: Output the chunks: \n")
for idx, chunk in enumerate(chunks):
    print(f"Chunk {idx + 1}: {chunk}\n")

#========================================
# THRESHOLD TUNING GUIDE
#========================================
# 
# Current threshold: 0.5 (50% similarity)
# 
# Adjust threshold based on your needs:
# - 0.3-0.4: Very lenient (allows very different sentences in same chunk) - LARGER chunks
# - 0.5-0.6: Balanced (good for most generic texts) - RECOMMENDED
# - 0.7-0.8: Strict (only highly similar sentences grouped) - SMALLER chunks
# - 0.9+: Very strict (almost identical sentences only)
#
# For generic texts like this, 0.5-0.6 works best.
# If chunks still feel wrong, try:
# 1. Lower threshold to 0.45 for more lenient grouping
# 2. Increase min_chunk_size to ensure minimum quality
# 3. Decrease min_chunk_size if too few chunks are created
#========================================

#RAG Pipeline Integration Note:
# The chunks generated here can be used as input for a RAG (Retrieval-Augmented Generation) pipeline. Each chunk can be treated as a separate document for retrieval, allowing the RAG
#    model to access relevant information from the text when generating responses. Adjusting the chunking strategy can significantly impact the quality of the retrieved information and, consequently, the generated output.





