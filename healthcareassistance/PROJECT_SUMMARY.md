# Healthcare Assistance CrewAI Project — Summary

## Project Overview

Transformed a debate-crew scaffold into a **multi-agent healthcare assistance system** using CrewAI 1.14.4. The system accepts a natural-language patient request and runs 4 sequential agents to identify intent, retrieve medical records via RAG, book an appointment, and research treatment options.

**Input request used for testing:**
> "Book a nephrologist appointment for my 70-year-old father who has been diagnosed with Chronic Kidney Disease (CKD)."

---

## System Architecture Diagram

![Healthcare Assistance CrewAI — System Architecture](https://mermaid.ink/img/Zmxvd2NoYXJ0IFRECiAgICBVc2VyKFsi8J-RpCBVc2VyIFJlcXVlc3QKQm9vayBuZXBocm9sb2dpc3QgYXBwdApmb3IgQ0tEIHBhdGllbnQiXSkKICAgIFVzZXIgLS0-IE1QWyJtYWluLnB5IMK3IHJ1bigpIl0KICAgIHN1YmdyYXBoIENyZXdbIkhlYWx0aGNhcmVBc3Npc3RhbmNlIENyZXcgIGNyZXcucHkiXQogICAgICAgIGRpcmVjdGlvbiBUQgogICAgICAgIFQxWyLwn46vIFRhc2sgMSDCtyBpZGVudGlmeV9pbnRlbnQKQWdlbnQ6IE1hbmFnZXIiXQogICAgICAgIFQyWyLwn5OLIFRhc2sgMiDCtyByZXRyaWV2ZV9tZWRpY2FsX2hpc3RvcnkKQWdlbnQ6IE1lZGljYWwgUmVjb3JkcyBNYW5hZ2VyIl0KICAgICAgICBUM1si8J-ThSBUYXNrIDMgwrcgYm9va19hcHBvaW50bWVudApBZ2VudDogSGVhbHRoY2FyZSBBc3Npc3RhbnQiXQogICAgICAgIFQ0WyLwn5SsIFRhc2sgNCDCtyByZXNlYXJjaF9ja2RfdHJlYXRtZW50CkFnZW50OiBNZWRpY2FsIFJlc2VhcmNoIFNwZWNpYWxpc3QiXQogICAgICAgIFQxIC0tPnxjb250ZXh0fCBUMgogICAgICAgIFQyIC0tPnxjb250ZXh0fCBUMwogICAgICAgIFQyIC0tPnxjb250ZXh0fCBUNAogICAgZW5kCiAgICBNUCAtLT4gVDEKICAgIHN1YmdyYXBoIFRvb2xzWyJDdXN0b20gVG9vbHMiXQogICAgICAgIFJBR1Rvb2xbIk1lZGljYWxSQUdUb29sCmN1c3RvbV90b29sLnB5Il0KICAgICAgICBTZXJwZXJUb29sWyJTZXJwZXJNZWRpY2FsU2VhcmNoVG9vbApzZXJwZXJfdG9vbC5weSJdCiAgICBlbmQKICAgIFQyIC0tPiBSQUdUb29sCiAgICBUNCAtLT4gUkFHVG9vbAogICAgVDQgLS0-IFNlcnBlclRvb2wKICAgIHN1YmdyYXBoIFJBR1BpcGVsaW5lWyJSQUcgUGlwZWxpbmUgIHJhZ19waXBlbGluZS5weSJdCiAgICAgICAgQ2h1bmtzWyJEb2N1bWVudCBDaHVua3MKNTEyIHRva2VucyDCtyA2NCBvdmVybGFwIl0KICAgICAgICBIRkVtYmVkWyJIdWdnaW5nRmFjZSBJbmZlcmVuY2UgQVBJCkJBQUkvYmdlLXNtYWxsLWVuLXYxLjUgwrcgMzg0LWRpbSJdCiAgICAgICAgRkFJU1NJZHhbKCJGQUlTUyBJbmRleAo1MyB2ZWN0b3JzIildCiAgICBlbmQKICAgIHN1YmdyYXBoIFBhdGllbnREYXRhWyJQYXRpZW50IERhdGEgU291cmNlcyJdCiAgICAgICAgUERGc1siNHggUERGIFJlcG9ydHMKc2FtcGxlX3BhdGllbnQucGRmCnNhbXBsZV9yZXBvcnRfYW5qYWxpLnBkZgpzYW1wbGVfcmVwb3J0X2RhdmlkLnBkZgpzYW1wbGVfcmVwb3J0X3JhbWVzaC5wZGYiXQogICAgICAgIEV4Y2VsWyJyZWNvcmRzLnhsc3giXQogICAgZW5kCiAgICBQREZzICYgRXhjZWwgLS0-IENodW5rcwogICAgQ2h1bmtzIC0tPiBIRkVtYmVkIC0tPiBGQUlTU0lkeAogICAgUkFHVG9vbCA8LS0-fHNlbWFudGljIHNlYXJjaHwgRkFJU1NJZHgKICAgIHN1YmdyYXBoIE1lbW9yeVsiUGVyc2lzdGVudCBNZW1vcnkgIExhbmNlREIiXQogICAgICAgIExhbmNlREJbKCJMYW5jZURCIFN0b3JlCmhlYWx0aGNhcmVfbGFuY2VkYiIpXQogICAgZW5kCiAgICBDcmV3IDwtLT58c2F2ZSAvIHJldHJpZXZlfCBMYW5jZURCCiAgICBzdWJncmFwaCBFeHRBUElzWyJFeHRlcm5hbCBBUElzIl0KICAgICAgICBPcGVuQUlbIk9wZW5BSQpncHQtNG8tbWluaSJdCiAgICAgICAgSEZJbmZlcmVuY2VbIkh1Z2dpbmdGYWNlCkluZmVyZW5jZSBBUEkiXQogICAgICAgIFNlcnBlckFQSVsiU2VycGVyLmRldgpHb29nbGUgU2VhcmNoIl0KICAgIGVuZAogICAgVDEgJiBUMiAmIFQzICYgVDQgLS0-fExMTSBjYWxsc3wgT3BlbkFJCiAgICBIRkVtYmVkIC0tPnxlbWJlZCByZXF1ZXN0c3wgSEZJbmZlcmVuY2UKICAgIFNlcnBlclRvb2wgLS0-fHNlYXJjaHwgU2VycGVyQVBJCiAgICBzdWJncmFwaCBPdXRwdXRzWyJPdXRwdXQgRmlsZXMgIHNyYy9vdXRwdXQvIl0KICAgICAgICBPMVsiaWRlbnRpZnlfaW50ZW50Lm1kIl0KICAgICAgICBPMlsibWVkaWNhbF9oaXN0b3J5Lm1kIl0KICAgICAgICBPM1siYXBwb2ludG1lbnRfY29uZmlybWF0aW9uLm1kIl0KICAgICAgICBPNFsiY2tkX3Jlc2VhcmNoX3N1bW1hcnkubWQiXQogICAgZW5kCiAgICBUMSAtLT4gTzEKICAgIFQyIC0tPiBPMgogICAgVDMgLS0-IE8zCiAgICBUNCAtLT4gTzQ=)

```mermaid
flowchart TD
    User(["👤 User Request\nBook nephrologist appt\nfor CKD patient"])

    User --> MP["main.py · run()"]

    subgraph Crew["HealthcareAssistance Crew  (crew.py)"]
        direction TB
        T1["🎯 Task 1 · identify_intent\nAgent: Manager"]
        T2["📋 Task 2 · retrieve_medical_history\nAgent: Medical Records Manager"]
        T3["📅 Task 3 · book_appointment\nAgent: Healthcare Assistant"]
        T4["🔬 Task 4 · research_ckd_treatment\nAgent: Medical Research Specialist"]

        T1 -->|context| T2
        T2 -->|context| T3
        T2 -->|context| T4
    end

    MP --> T1

    subgraph Tools["Custom Tools"]
        RAGTool["MedicalRAGTool\ncustom_tool.py"]
        SerperTool["SerperMedicalSearchTool\nserper_tool.py"]
    end

    T2 --> RAGTool
    T4 --> RAGTool
    T4 --> SerperTool

    subgraph RAGPipeline["RAG Pipeline  (rag_pipeline.py)"]
        Chunks["Document Chunks\n512 tokens · 64 overlap"]
        HFEmbed["HuggingFace Inference API\nBAAI/bge-small-en-v1.5 · 384-dim"]
        FAISSIdx[("FAISS Index\n53 vectors")]
    end

    subgraph PatientData["Patient Data Sources"]
        PDFs["4× PDF Reports\nsample_patient.pdf\nsample_report_anjali.pdf\nsample_report_david.pdf\nsample_report_ramesh.pdf"]
        Excel["records.xlsx"]
    end

    PDFs & Excel --> Chunks
    Chunks --> HFEmbed --> FAISSIdx
    RAGTool <-->|semantic search| FAISSIdx

    subgraph Memory["Persistent Memory  (LanceDB)"]
        LanceDB[("LanceDB Store\nhealthcare_lancedb")]
    end

    Crew <-->|save / retrieve| LanceDB

    subgraph ExtAPIs["External APIs"]
        OpenAI["OpenAI\ngpt-4o-mini"]
        HFInference["HuggingFace\nInference API"]
        SerperAPI["Serper.dev\nGoogle Search"]
    end

    T1 & T2 & T3 & T4 -->|LLM calls| OpenAI
    HFEmbed -->|embed requests| HFInference
    SerperTool -->|search| SerperAPI

    subgraph Outputs["Output Files  (src/output/)"]
        O1["identify_intent.md"]
        O2["medical_history.md"]
        O3["appointment_confirmation.md"]
        O4["ckd_research_summary.md"]
    end

    T1 --> O1
    T2 --> O2
    T3 --> O3
    T4 --> O4
```

---

## Architecture

### Agents (`config/agents.yaml`)

| Agent Key | Role | LLM | Tools |
|---|---|---|---|
| `manager` | Healthcare Operations and Case Manager | openai/gpt-4o-mini | — |
| `medical_records_manager` | Senior Medical Records Manager | openai/gpt-4o-mini | MedicalRAGTool |
| `medical_research_specialist` | Senior Medical Research Specialist | openai/gpt-4o-mini | MedicalRAGTool, SerperMedicalSearchTool |
| `healthcare_assistant` | Healthcare Scheduling Assistant | openai/gpt-4o-mini | — |

### Tasks (`config/tasks.yaml`)

| # | Task | Agent | Context From | Output File |
|---|---|---|---|---|
| 1 | `identify_intent` | manager | _(input: `{user_request}`)_ | `output/identify_intent.md` |
| 2 | `retrieve_medical_history` | medical_records_manager | identify_intent | `output/medical_history.md` |
| 3 | `book_appointment` | healthcare_assistant | retrieve_medical_history | `output/appointment_confirmation.md` |
| 4 | `research_ckd_treatment` | medical_research_specialist | retrieve_medical_history | `output/ckd_research_summary.md` |

---

## RAG Pipeline

### Embedding Model
- **Model:** `BAAI/bge-small-en-v1.5` (384-dim, MIT license)
- **Provider:** HuggingFace Inference API via `HuggingFaceEndpointEmbeddings` from `langchain-huggingface`
- **No local model download** — API-based, avoids PyTorch/sentence-transformers disk usage (~2GB saved)
- **Requires:** `HUGGINGFACEHUB_API_TOKEN` in `.env`

### Vector Store
- **Backend:** FAISS (`faiss-cpu`)
- **Index location:** `src/debater_app/patient_data/faiss_index/`
- **Vectors:** 53 (built from 22 document pages/rows, chunked at size=512, overlap=64)

### Data Sources (`src/debater_app/patient_data/`)
| File | Type | Content |
|---|---|---|
| `sample_patient.pdf` | PDF | 11-page patient chart (Bridport Family Medicine) |
| `sample_report_anjali.pdf` | PDF | Upper Respiratory Infection report |
| `sample_report_david.pdf` | PDF | Type 2 Diabetes follow-up (David Thompson) |
| `sample_report_ramesh.pdf` | PDF | Essential Hypertension report (Ramesh) |
| `records.xlsx` | Excel | Structured patient records |

### Rebuilding the Index
```bash
cd healthcareassistance
set -a && source .env && set +a
rm -rf src/debater_app/patient_data/faiss_index
cd src && python3 -m debater_app.tools.rag_pipeline
```

---

## Custom Tools

### `MedicalRAGTool` (`tools/custom_tool.py`)
- CrewAI `BaseTool` wrapping FAISS semantic search
- Class-level `_vectorstore` cache (loads once per process)
- Accepts `query` + optional `top_k` (default 5)
- Returns formatted chunks with source file and page number

### `SerperMedicalSearchTool` (`tools/serper_tool.py`)
- Calls Serper.dev Google Search API
- Filters results to trusted medical domains: WHO, PubMed, Medline, Mayo Clinic, CDC, NHS, kidney.org
- Used only by `medical_research_specialist` (Task 4)
- Handles missing `SERPER_API_KEY` gracefully (returns a message instead of crashing)

---

## Memory Configuration (`crew.py`)

Uses CrewAI 1.14.4's unified `Memory` class with `LanceDBStorage`:

```python
from crewai.memory.unified_memory import Memory
from crewai.memory.storage.lancedb_storage import LanceDBStorage

memory = Memory(
    storage=LanceDBStorage(
        path="./memory/healthcare_lancedb",
        table_name="healthcare_memories",
    ),
    embedder={"provider": "openai", "config": {"model": "text-embedding-3-small"}},
    semantic_weight=0.6,
    recency_half_life_days=90,
    default_importance=0.7,
)
```

> **Note:** The old `LongTermMemory` / `ShortTermMemory` / `EntityMemory` classes were removed in crewai 1.x. The unified `Memory` + `LanceDBStorage` approach is correct for 1.14.4.

---

## Dependencies (`pyproject.toml`)

```toml
dependencies = [
    "crewai[tools]==1.14.4",
    "faiss-cpu>=1.7.4",
    "huggingface-hub>=0.23.0",
    "langchain-huggingface>=0.1.0",
    "langchain-community>=0.2.0",
    "langchain-core>=0.2.0",
    "langchain-text-splitters>=0.2.0",
    "pypdf>=4.0.0",
    "openpyxl>=3.1.0",
    "pandas>=2.0.0",
    "requests>=2.31.0",
]
```

**Intentionally excluded:** `sentence-transformers`, `torch` (PyTorch) — these would consume ~2GB+ disk space, which caused disk-full failures in the dev container.

---

## Environment Variables (`.env`)

| Variable | Purpose |
|---|---|
| `OPENAI_API_KEY` | LLM calls (gpt-4o-mini) for all agents |
| `HUGGINGFACEHUB_API_TOKEN` | HuggingFace Inference API for FAISS embeddings |
| `HF_TOKEN` | Alias for HF token (some libraries read this) |
| `SERPER_API_KEY` | Serper.dev Google Search (set to placeholder — tool handles gracefully) |

---

## Key Issues Resolved

| # | Problem | Solution |
|---|---|---|
| 1 | `langchain.schema.Document` removed in LangChain 1.x | Changed to `langchain_core.documents` |
| 2 | `langchain.text_splitter` removed | Changed to `langchain_text_splitters` |
| 3 | `HuggingFaceEmbeddings` deprecated | Switched to `HuggingFaceEndpointEmbeddings` from `langchain-huggingface` |
| 4 | `LongTermMemory`/`ShortTermMemory`/`EntityMemory` don't exist in crewai 1.14.4 | Replaced with unified `Memory` + `LanceDBStorage` |
| 5 | `crewai run` uses isolated `uv` venv — system-installed packages unavailable | Added all deps to `pyproject.toml` |
| 6 | `sentence-transformers` pulls PyTorch (~2GB) → disk full | Removed sentence-transformers; switched to HF Inference API |
| 7 | OpenAI API key returning 401 for embeddings | Switched FAISS embeddings to HuggingFace Inference API |
| 8 | `agents.yaml` had leading-whitespace indentation bug | Fixed all 4 agent keys to correct indentation |
| 9 | `agents.yaml` had invalid `tools:` block | Removed (tools are wired in `crew.py`, not YAML) |
| 10 | `langchain-community` missing from `pyproject.toml` | Added `langchain-community>=0.2.0` to dependencies |
| 11 | `load_index()` in `rag_pipeline.py` still used `OpenAIEmbeddings` | Fixed to `HuggingFaceEndpointEmbeddings` |

---

## Successful Execution Output

```
╭─────────────────── 🚀 Crew Execution Started ──────────────────╮
│  Name: HealthcareAssistance                                    │
╰────────────────────────────────────────────────────────────────╯

Task 1 (identify_intent) ✅
  Agent: Healthcare Operations and Case Manager
  Output:
    - Patient intent: book an appointment
    - Specialist required: Nephrologist
    - Patient details: 70-year-old father with Chronic Kidney Disease (CKD)
    - Sub-tasks delegated to: Medical Records Manager, Healthcare Scheduler,
      Medical Research Specialist

Task 2 (retrieve_medical_history) ✅
  Agent: Senior Medical Records Manager
  Tool calls: 10× medical_rag_search (queried FAISS index)
  Retrieved real patient data from: sample_patient.pdf, sample_report_ramesh.pdf,
  sample_report_david.pdf, records.xlsx

Task 3 (book_appointment) ✅
  Agent: Healthcare Scheduling Assistant

Task 4 (research_ckd_treatment) ✅
  Agent: Senior Medical Research Specialist
  Final output: Comprehensive CKD management and treatment guide

╭──────────────────── 🏁 Crew Execution Complete ────────────────╮
│  Exit code: 0                                                  │
╰────────────────────────────────────────────────────────────────╯
```

**Packages installed in isolated venv:** 162 (including all langchain stack, crewai, faiss-cpu, lancedb, etc. — no PyTorch)

---

## How to Run

```bash
cd /workspaces/Simplilearn_Agentic_AI/healthcareassistance

# Load environment variables
set -a && source .env && set +a

# (First time only) Build FAISS index
cd src && python3 -m debater_app.tools.rag_pipeline && cd ..

# Run the crew
mkdir -p src/output memory
crewai run
```
