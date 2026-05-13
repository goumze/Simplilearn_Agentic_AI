"""
RAG Ingestion Pipeline for Healthcare Assistance
=================================================
Loads PDF reports and Excel records from patient_data/, splits them into
chunks, embeds each chunk with a local sentence-transformer model, and
persists a FAISS vector index to patient_data/faiss_index/.

Run once (or whenever patient_data changes):
    # from the healthcareassistance/ directory
    python -m debater_app.tools.rag_pipeline
"""

from __future__ import annotations

import logging
from pathlib import Path

import pandas as pd
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import PyPDFLoader
from langchain_huggingface import HuggingFaceEndpointEmbeddings
from langchain_community.vectorstores import FAISS

logging.basicConfig(level=logging.INFO, format="[RAG Pipeline] %(message)s")
logger = logging.getLogger(__name__)

# ── Paths ─────────────────────────────────────────────────────────────────────
DATA_DIR: Path = Path(__file__).parents[1] / "patient_data"
INDEX_DIR: Path = DATA_DIR / "faiss_index"

# BAAI/bge-small-en-v1.5: 384-dim, state-of-the-art retrieval, MIT license.
# Runs on HuggingFace's Inference API — no local GPU or PyTorch required.
EMBED_MODEL: str = "BAAI/bge-small-en-v1.5"

# Chunk parameters — 512 tokens balances context richness vs. retrieval precision
CHUNK_SIZE: int = 512
CHUNK_OVERLAP: int = 64


# ── Loaders ───────────────────────────────────────────────────────────────────

def _load_pdfs(data_dir: Path) -> list[Document]:
    """Load every PDF in data_dir using LangChain's PyPDFLoader (page-level docs)."""
    docs: list[Document] = []
    pdf_files = sorted(data_dir.glob("*.pdf"))
    if not pdf_files:
        logger.warning("No PDF files found in %s", data_dir)
    for pdf_path in pdf_files:
        logger.info("Loading PDF: %s", pdf_path.name)
        loader = PyPDFLoader(str(pdf_path))
        pages = loader.load()
        # Enrich metadata so retrieved chunks know their origin
        for page in pages:
            page.metadata["file_type"] = "pdf"
        docs.extend(pages)
    return docs


def _load_excel(data_dir: Path) -> list[Document]:
    """Load every .xlsx file; each row becomes one Document."""
    docs: list[Document] = []
    xlsx_files = sorted(data_dir.glob("*.xlsx"))
    if not xlsx_files:
        logger.warning("No Excel files found in %s", data_dir)
    for xlsx_path in xlsx_files:
        logger.info("Loading Excel: %s", xlsx_path.name)
        df = pd.read_excel(xlsx_path)
        for idx, row in df.iterrows():
            content = "\n".join(
                f"{col}: {val}" for col, val in row.items() if pd.notna(val)
            )
            docs.append(
                Document(
                    page_content=content,
                    metadata={
                        "source": str(xlsx_path),
                        "row": int(idx),
                        "file_type": "excel",
                    },
                )
            )
    return docs


# ── Pipeline ──────────────────────────────────────────────────────────────────

def build_index(force_rebuild: bool = False) -> None:
    """
    Ingest all documents in DATA_DIR and save a FAISS index to INDEX_DIR.

    Args:
        force_rebuild: If True, rebuild even when an index already exists.
    """
    if INDEX_DIR.exists() and not force_rebuild:
        logger.info(
            "FAISS index already exists at %s. "
            "Pass force_rebuild=True or delete the directory to rebuild.",
            INDEX_DIR,
        )
        return

    # 1. Load raw documents
    logger.info("Loading documents from %s ...", DATA_DIR)
    documents = _load_pdfs(DATA_DIR) + _load_excel(DATA_DIR)
    if not documents:
        raise RuntimeError(
            f"No documents loaded from {DATA_DIR}. "
            "Add PDF or Excel files before running the pipeline."
        )
    logger.info("Loaded %d document pages / rows.", len(documents))

    # 2. Chunk documents
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        separators=["\n\n", "\n", ". ", " ", ""],
    )
    chunks = splitter.split_documents(documents)
    logger.info("Split into %d chunks (size=%d, overlap=%d).", len(chunks), CHUNK_SIZE, CHUNK_OVERLAP)

    # 3. Embed via HuggingFace Inference API (no local model download)
    logger.info("Embedding via HF Inference API with model '%s' ...", EMBED_MODEL)
    embeddings = HuggingFaceEndpointEmbeddings(model=EMBED_MODEL)

    # 4. Build FAISS index
    logger.info("Building FAISS index ...")
    vectorstore = FAISS.from_documents(chunks, embeddings)

    # 5. Persist
    INDEX_DIR.mkdir(parents=True, exist_ok=True)
    vectorstore.save_local(str(INDEX_DIR))
    logger.info("FAISS index saved to: %s", INDEX_DIR)
    logger.info(
        "Index contains %d vectors. Ready for retrieval.",
        vectorstore.index.ntotal,
    )


def load_index() -> FAISS:
    """
    Load and return the persisted FAISS vectorstore.
    Raises FileNotFoundError if the index has not been built yet.
    """
    if not INDEX_DIR.exists():
        raise FileNotFoundError(
            f"FAISS index not found at {INDEX_DIR}. "
            "Run 'python -m debater_app.tools.rag_pipeline' to build it first."
        )
    embeddings = HuggingFaceEndpointEmbeddings(model=EMBED_MODEL)
    return FAISS.load_local(
        str(INDEX_DIR),
        embeddings,
        allow_dangerous_deserialization=True,
    )


if __name__ == "__main__":
    build_index(force_rebuild=True)
