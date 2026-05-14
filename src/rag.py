"""
RAG module — LanceDB vector store with FAISS IVF-PQ index.

Stores completed conversations as embeddings so that when a similar
user message arrives, the most semantically relevant past interactions
are retrieved and injected into agent prompts as grounding context.

Flow:
  store_conversation(state)   →  embed message → upsert to LanceDB
                                 → rebuild FAISS index if ≥ threshold
  retrieve_similar(query)     →  embed query → ANN search in LanceDB
                                 → return top-k similar conversations
"""

import os
import uuid
import logging
from datetime import datetime

import numpy as np
import pyarrow as pa
import lancedb
from openai import OpenAI

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
LANCEDB_URI = os.getenv("LANCEDB_URI", ".lancedb")
TABLE_NAME = "conversations"
EMBEDDING_MODEL = "text-embedding-3-small"
EMBEDDING_DIM = 1536          # text-embedding-3-small output dimension
FAISS_INDEX_THRESHOLD = 50    # minimum records before building IVF-PQ index
TOP_K_DEFAULT = 3             # how many neighbours to retrieve by default


# ---------------------------------------------------------------------------
# Embedding helper
# ---------------------------------------------------------------------------

def _get_embedding(text: str) -> list[float]:
    """Return an L2-normalised embedding vector for *text* via OpenAI."""
    client = OpenAI()
    response = client.embeddings.create(input=text, model=EMBEDDING_MODEL)
    vec = np.asarray(response.data[0].embedding, dtype=np.float32)
    # L2-normalise so cosine similarity = dot-product
    norm = np.linalg.norm(vec)
    if norm > 0:
        vec = vec / norm
    return vec.tolist()


# ---------------------------------------------------------------------------
# Schema
# ---------------------------------------------------------------------------

def _conversation_schema() -> pa.Schema:
    return pa.schema([
        pa.field("id",             pa.string()),
        pa.field("user_message",   pa.string()),
        pa.field("classification", pa.string()),
        pa.field("response",       pa.string()),
        pa.field("agent_used",     pa.string()),
        pa.field("ticket_id",      pa.string()),
        pa.field("timestamp",      pa.string()),
        # Fixed-size list required by LanceDB for ANN indexing
        pa.field("vector", pa.list_(pa.float32(), EMBEDDING_DIM)),
    ])


# ---------------------------------------------------------------------------
# Table access
# ---------------------------------------------------------------------------

def _get_or_create_table(db: lancedb.DBConnection) -> lancedb.table.Table:
    """Open the conversations table or create it with the correct schema."""
    if TABLE_NAME in db.table_names():
        return db.open_table(TABLE_NAME)
    logger.info("RAG: creating LanceDB table '%s'", TABLE_NAME)
    return db.create_table(TABLE_NAME, schema=_conversation_schema())


# ---------------------------------------------------------------------------
# FAISS IVF-PQ index builder
# ---------------------------------------------------------------------------

def _try_build_faiss_index(table: lancedb.table.Table, record_count: int) -> None:
    """
    Build / refresh the FAISS IVF-PQ index on the vector column.

    IVF-PQ partitions: ≈ sqrt(N), bounded to [2, N].
    PQ sub-vectors   : 8  (1536 / 8 = 192 — must divide evenly).

    Requires at least FAISS_INDEX_THRESHOLD records for meaningful training.
    """
    if record_count < FAISS_INDEX_THRESHOLD:
        logger.debug("RAG: skipping index build — only %d records (threshold=%d)",
                     record_count, FAISS_INDEX_THRESHOLD)
        return

    num_partitions = max(2, int(record_count ** 0.5))
    num_sub_vectors = 8  # 1536 % 8 == 0

    try:
        # LanceDB >= 0.6 API — IvfPq config object
        from lancedb.index import IvfPq
        table.create_index(
            "vector",
            config=IvfPq(num_partitions=num_partitions, num_sub_vectors=num_sub_vectors),
            replace=True,
        )
        logger.info("RAG: FAISS IVF-PQ index built via lancedb.index.IvfPq "
                    "(partitions=%d, sub_vectors=%d)", num_partitions, num_sub_vectors)
        return
    except (ImportError, Exception) as exc:
        logger.debug("RAG: IvfPq config API unavailable (%s), trying legacy API", exc)

    try:
        # LanceDB < 0.6 legacy keyword API
        table.create_index(
            metric="cosine",
            num_partitions=num_partitions,
            num_sub_vectors=num_sub_vectors,
            replace=True,
        )
        logger.info("RAG: FAISS IVF-PQ index built via legacy API "
                    "(partitions=%d, sub_vectors=%d)", num_partitions, num_sub_vectors)
    except Exception as exc2:
        logger.warning("RAG: FAISS index build failed — will use brute-force search. "
                       "Reason: %s", exc2)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def store_conversation(state: dict) -> None:
    """
    Embed the user message and persist the full conversation to LanceDB.
    Triggers a FAISS index rebuild when the record count crosses the threshold.

    Args:
        state: The final SupportState dict produced by the LangGraph workflow.
    """
    try:
        db = lancedb.connect(LANCEDB_URI)
        table = _get_or_create_table(db)

        vector = _get_embedding(state["user_message"])
        row = {
            "id":             str(uuid.uuid4()),
            "user_message":   state["user_message"],
            "classification": state.get("classification", ""),
            "response":       state.get("response", ""),
            "agent_used":     state.get("agent_used", ""),
            "ticket_id":      state.get("ticket_id") or "",
            "timestamp":      datetime.utcnow().isoformat(),
            "vector":         vector,
        }
        table.add([row])

        record_count = len(table)
        _try_build_faiss_index(table, record_count)
        logger.info("RAG: conversation stored (total records: %d)", record_count)

    except Exception:
        # RAG failures must never break the main workflow
        logger.exception("RAG: store_conversation failed — continuing without storage")


def retrieve_similar(query: str, top_k: int = TOP_K_DEFAULT) -> list[dict]:
    """
    Retrieve the *top_k* most semantically similar past conversations.

    Uses ANN search (FAISS IVF-PQ when index exists, brute-force otherwise).
    Returns an empty list on any failure so downstream agents degrade gracefully.

    Args:
        query:  The incoming user message to match against.
        top_k:  Number of neighbours to return (default 3).

    Returns:
        List of dicts with keys: user_message, classification, response,
        ticket_id, timestamp, _distance (cosine distance).
    """
    try:
        db = lancedb.connect(LANCEDB_URI)
        if TABLE_NAME not in db.table_names():
            return []

        table = db.open_table(TABLE_NAME)
        total = len(table)
        if total == 0:
            return []

        vector = _get_embedding(query)
        results = (
            table.search(vector)
                 .limit(min(top_k, total))
                 .select(["user_message", "classification", "response", "ticket_id", "timestamp", "_distance"])
                 .to_list()
        )

        logger.info("RAG: retrieved %d/%d similar conversation(s)", len(results), total)
        return results

    except Exception:
        logger.exception("RAG: retrieve_similar failed — returning empty context")
        return []


def format_rag_context(similar: list[dict]) -> str:
    """
    Format retrieved conversations into a compact, prompt-ready context block.

    Args:
        similar: Output of retrieve_similar().

    Returns:
        Multi-line string ready to be appended to an LLM system prompt,
        or an empty string if no similar conversations were found.
    """
    if not similar:
        return ""

    lines = [
        "--- Relevant past interactions (use for context, do NOT copy verbatim) ---"
    ]
    for i, item in enumerate(similar, 1):
        dist = item.get("_distance", "")
        dist_str = f"  [similarity: {1 - float(dist):.2f}]" if dist != "" else ""
        lines.append(
            f"[{i}]{dist_str}\n"
            f"  Prior message  : \"{item['user_message']}\"\n"
            f"  Classification : {item['classification']}\n"
            f"  Response given : \"{item['response']}\""
        )
    lines.append("--- End of context ---")
    return "\n".join(lines)


def get_all_rag_records() -> list[dict]:
    """Return all stored conversation records for UI display."""
    try:
        db = lancedb.connect(LANCEDB_URI)
        if TABLE_NAME not in db.table_names():
            return []
        table = db.open_table(TABLE_NAME)
        return (
            table.search()
                 .select(["id", "user_message", "classification", "response",
                          "agent_used", "ticket_id", "timestamp"])
                 .limit(500)
                 .to_list()
        )
    except Exception:
        logger.exception("RAG: get_all_rag_records failed")
        return []
