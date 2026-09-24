import os
import sys
import uuid
import json
import logfire

from qdrant_client import QdrantClient
from qdrant_client.http import models
from torch import chunk

from app.config import settings
from app.services.retrieval.embedding import embed_texts, get_embedding_dim
from app.ingestion.loaders.pdf import parse_pdf
from app.ingestion.loaders.html import parse_html
from app.ingestion.loaders.text import parse_text
from app.ingestion.loaders.office import parse_office
from app.ingestion.chunking.splitter import chunk_text
from dotenv import load_dotenv
load_dotenv()

logfire.configure(service_name="enterprise-ingestion-service")

PROCESSED_DATA_DIR = "processed_data"

#Initialize Qdrant client
qdrant_client = QdrantClient(
    url=settings.QDRANT_URL,
    api_key=settings.QDRANT_API_KEY
)


def save_processed_locally(data: dict, source_type: str, file_name: str) -> str:
    """Save parsed chunk metadata as JSON in processed_data/<source_type>/."""
    folder=os.path.join(PROCESSED_DATA_DIR, source_type)
    os.makedirs(folder,exist_ok=True)
    dest=os.path.join(folder,f"{file_name}.json")
    with open(dest,"w",encoding="utf-8") as f:
        json.dump(data,f,ensure_ascii=False, indent=2)
    return dest

def process_file(file_path:str,filename: str, source_type: str):
    """Parse -> chunk -> save locally -> embed -> index in Qdrant"""
    with logfire.span("Processing File",file=filename,source=source_type):
        try:
            ext = filename.lower().rsplit(".",1)[-1]
            if ext == "pdf":
               full_text = parse_pdf(file_path)
            elif ext in ("html","htm"):
                full_text = parse_html(file_path)
            elif ext == "txt":
                full_text = parse_text(file_path)
            elif ext in ("docx","pptx"):
                full_text = parse_office(file_path)
            else:
                logfire.warning(f"Skipping unsupported file types: {filename}")
                return

            #2. Chunk text
            chunks = chunk_text(full_text)
            if not chunks:
                return

            #3. Save processed metadata locally
            processed_data = {
                "file_name": filename,
                "source_type": source_type,
                "chunks": chunks
            }

            local_path = save_processed_locally(processed_data, source_type, filename)
            logfire.info(f"Processed data saved locally at {local_path}")


            #4. Embed chunks and index in Qdrant
            with logfire.span("Vectorizing and Indexing"):
                embeddings = embed_texts(chunks)
                points = [
                    models.PointStruct(
                        id=str(uuid.uuid4()),
                        vector=vector,
                        payload={
                            "text":chunk,
                            "source":filename,
                            "source_type":source_type
                        }
                    )
                    for vector, chunk in zip(embeddings, chunks)
                ]

                qdrant_client.upsert(
                    collection_name=settings.QDRANT_COLLECTION_NAME,
                    points=points
                )
                logfire.info(f"Indexed {len(points)} chunks from file {filename} into Qdrant")

        except Exception as e:
            logfire.error(f"Error occurred while processing file {filename}: {e}")
            return


        except Exception as e:
            logfire.error(f"Failed to process file {filename}: {e}")
            return


def process_directory(directory_path: str, source_type: str):
    """Process all files in a directory."""
    files=[f for f in os.listdir(directory_path) if os.path.isfile(os.path.join(directory_path, f))]
    logfire.info(f"Found {len(files)} files in directory {directory_path}")
    for filename in files:
        process_file(os.path.join(directory_path, filename), filename, source_type)

def run_universal_ingestion(base_dir: str, explicit_source_types: str = None, wipe: bool = False):
    """
    Scan base_dir, map sub-folders to source types, and ingest all documents.
    Pass --wipe to drop and recreate the Qdrant collection before ingestion.
    """
    with logfire.span("Universal Ingestion Started", base_directory=base_dir):
        # Recreate collection - dimension resolved at runtime after embedding model probe
        if not qdrant_client.collection_exists(settings.QDRANT_COLLECTION_NAME):
            dim = get_embedding_dim()
            qdrant_client.create_collection(
                collection_name=settings.QDRANT_COLLECTION_NAME,
                vectors_config=models.VectorParams(
                    size=dim,
                    distance=models.Distance.COSINE
                ),
            )
            logfire.info(
                f"Created collection '{settings.QDRANT_COLLECTION_NAME}' "
                f"({dim}-dim, Cosine)"
            )
        
        # Discover subdirectories
        subdirs = [
            d for d in os.listdir(base_dir) 
            if os.path.isdir(os.path.join(base_dir, d))
        ]

        if not subdirs:
            # No subdirectories - process base directory directly
            if explicit_source_types:
                source_type = explicit_source_types
            else:
                base_name = os.path.basename(os.path.normpath(base_dir)).lower()
                source_type = (
                    "true" if "true" in base_name
                    else "noisy" if "noisy" in base_name
                    else "general"
                )
            logfire.info(f"No sub-folders found - processing '{base_dir}' as '{source_type}'")
            process_directory(base_dir, source_type)
        else:
            # Process each subdirectory
            for subdir in subdirs:
                subdir_path = os.path.join(base_dir, subdir)
                source_type = subdir.lower()
                logfire.info(f"Processing subdirectory '{subdir}' as source_type '{source_type}'")
                process_directory(subdir_path, source_type)
               
if __name__ == "__main__":
    # Usage:
    #   python -m app.ingestion.processor DATA --wipe
    #   python -m app.ingestion.processor DATA/true_data true
    wipe_requested = "--wipe" in sys.argv
    clean_args = [a for a in sys.argv if a != "--wipe"]

    target_dir = clean_args[1] if len(clean_args) > 1 else "DATA"
    explicit_type = clean_args[2] if len(clean_args) > 2 else None

    if not os.path.exists(target_dir):
        print(f"Error: path '{target_dir}' does not exist.")
        sys.exit(1)

    run_universal_ingestion(target_dir, explicit_source_types=explicit_type, wipe=wipe_requested)
    logfire.info("Ingestion job completed.")            
