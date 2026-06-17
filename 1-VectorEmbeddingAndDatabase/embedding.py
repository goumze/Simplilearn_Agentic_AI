import numpy as np
import matplotlib.pyplot as plt
import requests
import os
from dotenv import load_dotenv
from huggingface_hub import InferenceClient
from langchain_openai import OpenAIEmbeddings

def cosine_similarity(vec1, vec2):
    """
    Calculate the cosine similarity between two vectors.
    
    Args:
        vec1 (list or np.array): First vector.
        vec2 (list or np.array): Second vector.
        
    Returns:
        float: Cosine similarity between vec1 and vec2.
    """
    vec1 = np.array(vec1)
    vec2 = np.array(vec2)
    
    dot_product = np.dot(vec1, vec2)
    norm_vec1 = np.linalg.norm(vec1)
    norm_vec2 = np.linalg.norm(vec2)
    
    if norm_vec1 == 0 or norm_vec2 == 0:
        return 0.0
    
    return dot_product / (norm_vec1 * norm_vec2)

if __name__ == "__main__":
    
    #Simplified 2D example (real embedding have hundreds of dimensions)

    word_embeddings = {
        "cat": [0.8, 0.6],
        "dog": [0.7, 0.3],
        "kitten": [0.75,0.65],
        "puppy": [0.65,0.35],
        "car": [-0.5, 0.2],
        "truck": [-0.45, 0.15]
        }

    fig, ax = plt.subplots(figsize=(8, 6))

    for word, coords in word_embeddings.items():
        ax.scatter(coords[0], coords[1], label=word)
        ax.annotate(word, (coords[0], coords[1]), textcoords="offset points", xytext=(5,5))

    ax.set_xlabel("Dimension 1")   
    ax.set_ylabel("Dimension 2")
    ax.set_title("Simplified Word Embeddings in 2D Space")
    ax.grid(True,alpha=0.3)

    plt.tight_layout()
    plt.show()

    cosine_sim = cosine_similarity(word_embeddings["cat"], word_embeddings["kitten"])
    print(f"Cosine similarity between 'cat' and 'kitten': {cosine_sim:.4f}")

    cosine_sim = cosine_similarity(word_embeddings["cat"], word_embeddings["car"])
    print(f"Cosine similarity between 'cat' and 'car': {cosine_sim:.4f}")

def cosine_similarity(vec1, vec2):
    """
    Calculate the cosine similarity between two vectors.
    
    Args:
        vec1 (list or np.array): First vector.
        vec2 (list or np.array): Second vector.
        
    Returns:
        float: Cosine similarity between vec1 and vec2.
    """
    vec1 = np.array(vec1)
    vec2 = np.array(vec2)
    
    dot_product = np.dot(vec1, vec2)
    norm_vec1 = np.linalg.norm(vec1)
    norm_vec2 = np.linalg.norm(vec2)
    
    if norm_vec1 == 0 or norm_vec2 == 0:
        return 0.0
    
    return dot_product / (norm_vec1 * norm_vec2)


#Hugging Face Inference via InferenceClient (no local model download required)



load_dotenv()
HF_TOKEN = os.getenv("HF_TOKEN")
HF_MODEL = "sentence-transformers/all-MiniLM-L6-v2"

class HFInferenceEmbeddings:
    """
    Mimics LangChain's Embeddings interface using HuggingFace InferenceClient.
    No local model download required — all inference is done via the hosted API.
    """
    def __init__(self, model: str = HF_MODEL, token: str = HF_TOKEN):
        self.client = InferenceClient(model=model, token=token)

    def embed_query(self, text: str) -> list[float]:
        """Embed a single query string. Returns a 1D list of floats."""
        return self.client.feature_extraction(text).tolist()

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        """Embed a list of documents. Returns a 2D list (one vector per text)."""
        return [self.client.feature_extraction(text).tolist() for text in texts]


embedder = HFInferenceEmbeddings()

print("\n--- Using Hugging Face InferenceClient Embeddings ---")
single_text = "Langchain and RAG are powerful tools for building AI applications."
# embed_query — single text (e.g. a user search query)
query_embedding = embedder.embed_query(single_text)
print(f"embed_query result — dims: {len(query_embedding)}, first 5 values: {query_embedding[:5]}")

# embed_documents — multiple texts (e.g. a document corpus)
documents = [
    "This is an example sentence",
    "Each sentence is converted",
    "Embeddings are numerical representations of text",
    "They capture semantic meaning",
]
doc_embeddings = embedder.embed_documents(documents)
print(f"embed_documents result — {len(doc_embeddings)} docs, all doc embeddings {doc_embeddings} ")


print("\n--- Using OpenAI Embeddings ---")
embeddings = OpenAIEmbeddings(model="text-embedding-3-small")

#Single Text Embedding
single_embeddings=embeddings.embed_query(single_text)
print(f"Single Text Embedding — dims: {len(single_embeddings)}, all values  : {single_embeddings}")

print("\n--- Using OpenAI Embeddings for Multiple Documents ---")
#Multiple Text Embeddings
multiple_embeddings=embeddings.embed_documents(documents)
print(f"Multiple Text Embeddings — {len(multiple_embeddings)} docs, all doc embeddings : {multiple_embeddings}")