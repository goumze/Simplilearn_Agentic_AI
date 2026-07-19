# Report Generator - Project Specification

## 1. Project Overview

**Purpose:** Multi-agent orchestration system that generates comprehensive reports using LangGraph and LLM-powered agents.

**Architecture:** Sequential workflow with three specialized agents:
- **Planner Agent:** Creates logical outline with 3-4 sections
- **Writer Coordinator:** Orchestrates parallel section writing
- **Compiler Agent:** Assembles final markdown report

**Technology Stack:**
- LangGraph (agent orchestration)
- LangChain (LLM integration)
- OpenAI GPT-4o-mini (language model)
- Python 3.8+
- Python logging (structured tracing)

---

## 2. Current Features

### 2.1 Core Workflow
- Input: topic (string)
- Output: markdown-formatted report
- State management: ReportState TypedDict with:
  - `topic`: report subject
  - `sections`: list of planned section titles
  - `section_drafts`: dict of section_title → content
  - `final_report`: complete markdown output

### 2.2 Logging & Observability
- Structured logging with timestamps and context
- Agent-level tracing: `[agent_name]` prefixed logs
- Section-level progress tracking
- Configurable log level via `LOG_LEVEL` environment variable
- Formatted output: `TIMESTAMP | LEVEL | LOGGER | MESSAGE`

### 2.3 Planner Agent
- Generates 3-4 logical section titles from topic
- Returns sections as list of strings
- Uses LLM prompt to ensure logical flow

### 2.4 Writer Agent
- Generates 2-3 paragraph content per section
- Adaptive tone:
  - Research-backed (for intro/background/analysis)
  - Forward-thinking (for implications/recommendations)
- Tracks section generation time implicitly via logs

### 2.5 Compiler Agent
- Assembles sections in planned order
- Creates markdown header with topic
- Validates section availability before inclusion
- Logs final report size

---

## 3. Specifications by Feature

### Spec A: Error Handling & Resilience

**Requirement:** Graceful handling of LLM API failures

**Implementation Details:**
```
For each LLM call (planner, writer):
- Wrap in try-except for OpenAI exceptions
- Catch: APIError, Timeout, RateLimitError
- Retry strategy: exponential backoff (2^attempt seconds)
- Max retries: 3 attempts
- Log each retry with attempt number and reason
- On final failure: raise custom ReportGenerationError with context
```

**Test Criteria:**
- Planner retry logs show "attempt 1/3", "attempt 2/3", etc.
- Writer retry logs show section_title in context
- Error logs include error type and timestamp
- Graceful degradation: skip section on writer failure (optional)

---

### Spec B: Caching & Performance Optimization

**Requirement:** Reduce redundant LLM calls

**Implementation Details:**
```
Add section cache to state:
- Cache key: hash(section_title + topic)
- Store: section_text
- Check cache before LLM call in write_section()
- Log cache hit/miss with section_title
- Cache invalidation: manual via environment variable (CACHE_CLEAR)
```

**State Addition:**
```python
section_cache: Dict[str, str]  # Add to ReportState
cache_hits: int = 0  # Track performance
cache_misses: int = 0
```

**Test Criteria:**
- Same section generated twice shows cache hit on second call
- Log shows "[writer] cache hit | section_title=X"
- Performance improvement: ~90% time saved on cache hit

---

### Spec C: Progress Tracking & State Management

**Requirement:** Real-time visibility into report generation progress

**Implementation Details:**
```
Add progress metadata:
- current_stage: str (planner/writer/compiler)
- sections_completed: int
- sections_total: int
- progress_percent: float

Update logs with:
- Overall progress: "progress: 2/4 sections (50%)"
- Agent transitions: "[workflow] transitioning planner → writer_coordinator"
- Estimated time remaining (if tracking start time)
```

**State Addition:**
```python
progress_metadata: Dict[str, Any] = {
    'current_stage': str,
    'sections_completed': int,
    'sections_total': int,
    'start_time': float,
}
```

---

### Spec D: Timeout Handling

**Requirement:** Prevent indefinite hanging on slow LLM responses

**Implementation Details:**
```
Add timeout configuration:
- SECTION_TIMEOUT: 30 seconds per section (env var)
- PLANNER_TIMEOUT: 20 seconds (env var)
- Implement via OpenAI timeout parameter
- On timeout: log warning, retry once
- On second timeout: skip section, log error

Timeout logging:
- "[writer] timeout on section X, retrying..."
- "[writer] timeout on section X again, skipping"
```

**Test Criteria:**
- Timeout triggers after configured duration
- Retry happens automatically
- Final timeout logged but doesn't crash workflow

---

### Spec E: Content Validation

**Requirement:** Ensure generated content meets quality thresholds

**Implementation Details:**
```
Validation checks:
1. Section length: minimum 200 characters
2. Section format: no unwanted markdown (###, ####)
3. Uniqueness: no duplicate sections in final report
4. Topic relevance: section_title appears in section_content (heuristic)

On validation failure:
- Log warning with reason
- Retry once with stricter prompt
- Skip section if second attempt fails
```

**Validation Rules:**
```python
MIN_SECTION_LENGTH = 200
MAX_SECTION_LENGTH = 5000
REQUIRED_TOPIC_MENTION_RATE = 0.3  # % of sections that must mention topic
```

---

### Spec F: Configuration Management

**Requirement:** Centralized configuration for all parameters

**Implementation Details:**
```
Create config.py with:
- MODEL_NAME: "gpt-4o-mini"
- LOG_LEVEL: from env or "INFO"
- TIMEOUT_SECTION: from env or 30
- TIMEOUT_PLANNER: from env or 20
- MAX_RETRIES: 3
- RETRY_BACKOFF_BASE: 2
- MIN_SECTION_LENGTH: 200
- CACHE_ENABLED: from env or True
```

**Environment Variables:**
```
LOG_LEVEL=INFO|DEBUG|WARNING|ERROR
OPENAI_API_KEY=<required>
SECTION_TIMEOUT=30
PLANNER_TIMEOUT=20
CACHE_CLEAR=false
```

---

### Spec G: Testing & Validation

**Requirement:** Comprehensive test coverage for all agents

**Test Categories:**

1. **Unit Tests (test_agents.py):**
   - planner_agent produces 3-4 sections
   - write_section handles all tone types
   - compiler_agent produces valid markdown

2. **Integration Tests (test_workflow.py):**
   - Full workflow completes without errors
   - State transitions correctly
   - Logging captures all stages

3. **Error Tests (test_error_handling.py):**
   - Timeout scenarios trigger retry
   - API errors are caught and logged
   - Graceful degradation works

4. **Performance Tests (test_performance.py):**
   - Cache hits reduce execution time
   - Logging overhead < 5% of total time
   - Timeout prevents hanging

---

## 4. Non-Functional Requirements

### NFR-1: Logging Overhead
- Logging should not exceed 5% of total execution time
- Use lazy string formatting: `logger.info('[agent] %s', var)` not f-strings

### NFR-2: Memory Usage
- Cache size capped at 100 entries (configurable)
- State object < 10MB per report generation

### NFR-3: Observability
- All agent transitions must be logged
- All LLM calls must be logged with duration
- All failures must be logged with context

### NFR-4: Scalability
- Support reports with 10+ sections
- Support parallel section writing (future enhancement)

---

## 5. Dependencies

```
langchain>=0.1.0
langgraph>=0.0.1
langchain-openai>=0.0.1
python-dotenv>=1.0.0
```

---

## 6. Future Enhancements (Planned)

### Phase 2: Parallel Execution
- Parallelize section writing with `asyncio`
- Log task IDs for tracing parallel execution

### Phase 3: Human-in-the-Loop
- Allow user review of section drafts before compilation
- Add approval/revision workflow

### Phase 4: Multi-Model Support
- Support Claude, Gemini, Llama alongside GPT-4
- Pluggable LLM interface

### Phase 5: Output Formats
- Export to PDF, DOCX, HTML
- Custom CSS/styling

---

## 7. Success Criteria

✅ **Reliability:** 95% successful report generation (no crashes)
✅ **Performance:** < 5 min for 4-section report (development)
✅ **Observability:** Every agent action logged with context
✅ **Maintainability:** All specs covered by tests
✅ **Code Quality:** No magic numbers, all params configurable
