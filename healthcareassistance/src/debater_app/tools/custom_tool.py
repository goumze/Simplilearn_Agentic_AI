from __future__ import annotations

from typing import ClassVar, Optional, Type

from crewai.tools import BaseTool
from langchain_community.vectorstores import FAISS
from pydantic import BaseModel, Field


class RAGSearchInput(BaseModel):
    """Input schema for MedicalRAGTool."""
    query: str = Field(
        ...,
        description=(
            "The medical question or topic to search for in the patient knowledge base. "
            "Examples: 'CKD treatment options for elderly', 'patient Ramesh diagnosis', "
            "'latest nephrology guidelines'."
        ),
    )
    top_k: int = Field(
        default=4,
        ge=1,
        le=10,
        description="Number of most-relevant document chunks to retrieve (1-10).",
    )


class MedicalRAGTool(BaseTool):
    """
    Semantic search tool over the local FAISS patient knowledge base.

    Loads PDF reports and Excel records that were ingested by
    debater_app.tools.rag_pipeline and returns the most relevant chunks
    for a given query.  Results are formatted with their source file so
    the agent can cite them in its response.
    """

    name: str = "medical_rag_search"
    description: str = (
        "Search the internal medical knowledge base (patient reports and records) "
        "using semantic similarity. Use this to retrieve CKD treatment information, "
        "patient history, lab results, or any evidence-based medical content stored "
        "in the patient_data directory."
    )
    args_schema: Type[BaseModel] = RAGSearchInput

    # Class-level cache so the FAISS index is loaded only once per process
    _vectorstore: ClassVar[Optional[FAISS]] = None

    # ── Private helpers ───────────────────────────────────────────────────

    def _get_vectorstore(self) -> FAISS:
        if MedicalRAGTool._vectorstore is None:
            from debater_app.tools.rag_pipeline import load_index
            MedicalRAGTool._vectorstore = load_index()
        return MedicalRAGTool._vectorstore

    # ── BaseTool interface ────────────────────────────────────────────────

    def _run(self, query: str, top_k: int = 4) -> str:
        vectorstore = self._get_vectorstore()
        results = vectorstore.similarity_search(query, k=top_k)

        if not results:
            return "No relevant information found in the medical knowledge base for this query."

        formatted_chunks = []
        for i, doc in enumerate(results, start=1):
            source = doc.metadata.get("source", "unknown")
            page = doc.metadata.get("page", "")
            page_info = f" (page {page + 1})" if page != "" else ""
            header = f"[Result {i} — {source}{page_info}]"
            formatted_chunks.append(f"{header}\n{doc.page_content.strip()}")

        return "\n\n---\n\n".join(formatted_chunks)
