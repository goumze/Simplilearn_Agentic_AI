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
    pass

def run_universal_ingestion(base_dir: str,explicit_source_types: str = None, wipe: bool = False):
    """
    Scan base_dir, map sub-folders to source types, and ingest all documents.
    Pass --wipe to drop and recreate the Qdrant collection before ingestion.

    """
    pass
