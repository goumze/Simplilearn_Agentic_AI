"""
SerperDev Medical Search Tool
==============================
A CrewAI BaseTool that queries the Serper.dev Google Search API and
restricts results to reputable medical sources (WHO, PubMed, Medline,
Mayo Clinic, CDC, NHS) to support the medical_records_manager agent
during the retrieve_medical_history task.

Requires the environment variable:
    SERPER_API_KEY=<your serper.dev api key>
"""

from __future__ import annotations

import json
import os
from typing import Any, Type

import requests
from crewai.tools import BaseTool
from pydantic import BaseModel, Field

SERPER_API_URL = "https://google.serper.dev/search"

# Trusted medical domains used to focus the site: filter
TRUSTED_MEDICAL_SITES = [
    "who.int",
    "pubmed.ncbi.nlm.nih.gov",
    "medlineplus.gov",
    "mayoclinic.org",
    "cdc.gov",
    "nhs.uk",
    "kidney.org",         # National Kidney Foundation — relevant for CKD
    "ncbi.nlm.nih.gov",
]


class SerperMedicalSearchInput(BaseModel):
    """Input schema for SerperMedicalSearchTool."""

    query: str = Field(
        ...,
        description=(
            "The medical query to search for. Examples: "
            "'CKD stage 3 symptoms in elderly patients', "
            "'nephrologist referral criteria chronic kidney disease', "
            "'WHO guidelines CKD management 2024'."
        ),
    )
    num_results: int = Field(
        default=5,
        ge=1,
        le=10,
        description="Number of search results to return (1–10).",
    )
    restrict_to_trusted_sites: bool = Field(
        default=True,
        description=(
            "When True, appends a site: filter to restrict results to "
            "trusted medical domains (WHO, PubMed, Medline, Mayo Clinic, etc.)."
        ),
    )


class SerperMedicalSearchTool(BaseTool):
    """
    Search Google via the Serper.dev API for medical information.

    Used by the medical_records_manager during the retrieve_medical_history
    task to supplement local patient records with authoritative online
    sources such as WHO guidelines and PubMed articles.

    Set the SERPER_API_KEY environment variable before running.
    """

    name: str = "serper_medical_search"
    description: str = (
        "Search the web for up-to-date medical information using the Serper.dev "
        "Google Search API. Restricts results to trusted sources like WHO, PubMed, "
        "Medline, Mayo Clinic, and the National Kidney Foundation. Use this to look up "
        "CKD diagnostic criteria, specialist referral guidelines, medication interactions, "
        "or any clinical information not available in the local patient records."
    )
    args_schema: Type[BaseModel] = SerperMedicalSearchInput

    # ── Helpers ───────────────────────────────────────────────────────────

    @staticmethod
    def _build_query(query: str, restrict: bool) -> str:
        if not restrict:
            return query
        site_filter = " OR ".join(f"site:{s}" for s in TRUSTED_MEDICAL_SITES)
        return f"{query} ({site_filter})"

    @staticmethod
    def _format_results(data: dict[str, Any], num_results: int) -> str:
        organic = data.get("organic", [])
        if not organic:
            return "No results found for this query."

        lines: list[str] = []
        for i, result in enumerate(organic[:num_results], start=1):
            title = result.get("title", "No title")
            link = result.get("link", "")
            snippet = result.get("snippet", "No description available.")
            lines.append(f"[{i}] {title}\n    URL: {link}\n    {snippet}")

        # Include answer box if present (Serper feature)
        answer_box = data.get("answerBox", {})
        if answer_box:
            answer = answer_box.get("answer") or answer_box.get("snippet", "")
            if answer:
                lines.insert(0, f"[Featured Answer]\n{answer}\n")

        return "\n\n".join(lines)

    # ── BaseTool interface ────────────────────────────────────────────────

    def _run(
        self,
        query: str,
        num_results: int = 5,
        restrict_to_trusted_sites: bool = True,
    ) -> str:
        api_key = os.getenv("SERPER_API_KEY")
        if not api_key:
            return (
                "SERPER_API_KEY environment variable is not set. "
                "Obtain a free API key from https://serper.dev and add it to your .env file."
            )

        full_query = self._build_query(query, restrict_to_trusted_sites)

        headers = {
            "X-API-KEY": api_key,
            "Content-Type": "application/json",
        }
        payload = {
            "q": full_query,
            "num": num_results,
        }

        try:
            response = requests.post(
                SERPER_API_URL,
                headers=headers,
                data=json.dumps(payload),
                timeout=15,
            )
            response.raise_for_status()
        except requests.exceptions.Timeout:
            return "The Serper API request timed out. Please try again."
        except requests.exceptions.HTTPError as exc:
            return f"Serper API returned an error: {exc.response.status_code} — {exc.response.text}"
        except requests.exceptions.RequestException as exc:
            return f"Failed to reach the Serper API: {exc}"

        return self._format_results(response.json(), num_results)
