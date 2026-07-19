# Agent Guidelines for Report Generator Maintenance

This document guides AI agents (GitHub Copilot, coding assistants) on how to interpret specifications and maintain the report generator project.

---

## 1. Agent Responsibilities

### 1.1 When a New Spec is Added
1. **Read** the spec section (e.g., "Spec A: Error Handling")
2. **Identify** what code needs to change (functions, new files, config)
3. **Generate** implementation code based on spec details
4. **Add** corresponding tests
5. **Update** logging calls to match spec requirements
6. **Validate** against test criteria in spec

### 1.2 When Code Changes are Requested
1. **Reference** the spec first (find relevant spec section)
2. **Trace** which agents/functions are affected
3. **Check** if logging needs to be updated
4. **Add** tests for the new behavior
5. **Verify** spec requirements are met

### 1.3 When Bugs are Reported
1. **Check** spec against actual behavior
2. **Identify** spec violation or implementation gap
3. **Fix** the implementation
4. **Add** test case to prevent regression
5. **Log** the fix details

---

## 2. Code Structure & Patterns

### 2.1 Agent Functions

**Pattern for Agent Functions:**
```python
def agent_name(state: ReportState) -> ReportState:
    """
    <Agent purpose from spec>
    
    Spec Reference: <Spec letter and title>
    - Requirement: <one-liner>
    - Input: <what state fields it reads>
    - Output: <what state fields it modifies>
    """
    logger.info('[agent_name] started | <key_metrics>')
    
    try:
        # Main logic here
        logger.info('[agent_name] invoking <action>')
        # ... implementation ...
        logger.info('[agent_name] completed | <result_metrics>')
        
    except SpecificError as e:
        logger.error('[agent_name] error | error_type="%s" | context=...', type(e).__name__)
        # Handle per spec
        
    return {**state, 'updated_field': value}
```

**Logging Requirements:**
- Start log: `[agent_name] started | key_context`
- Action logs: `[agent_name] action_verb key_info`
- End log: `[agent_name] completed | result_metrics`
- Error log: `[agent_name] error | error_type="%s" | context`

### 2.2 Helper Functions

**Pattern for Helpers:**
```python
def helper_function(param1: str, param2: str) -> str:
    """
    <What it does> per Spec X.
    
    Args:
        param1: <description>
        param2: <description>
    
    Returns:
        <description of return value>
    
    Raises:
        <CustomError>: when <condition>
    """
    logger.info('[component] action_started | param1="%s"', param1)
    
    try:
        result = perform_action()
        logger.info('[component] action_completed | chars=%d', len(result))
        return result
    except Exception as e:
        logger.error('[component] action_failed | reason="%s"', str(e))
        raise
```

### 2.3 State Management

**ReportState Fields:**
```python
class ReportState(TypedDict):
    # Current fields
    topic: str
    sections: List[str]
    section_drafts: Dict[str, str]
    final_report: str
    
    # Add new fields only when spec requires it
    # Example: Add field and spec reference
    section_cache: Dict[str, str]  # Spec B: Caching
    progress_metadata: Dict[str, Any]  # Spec C: Progress
```

**Rule:** Every new field must have a corresponding spec justification in a comment.

---

## 3. Implementing Specs

### 3.1 Spec A: Error Handling & Resilience

**When implementing:**
1. Identify all LLM call sites (planner_agent, write_section)
2. Wrap with try-except catching: `APIError`, `Timeout`, `RateLimitError`
3. Create `max_retries` loop with exponential backoff
4. Log each retry: `logger.info('[agent] retry %d/%d | reason="%s"', attempt, max_retries, reason)`
5. Create `CustomError` subclass: `class ReportGenerationError(Exception)`
6. On final failure, log and raise with full context

**Generate test:**
```python
def test_planner_retry_on_timeout():
    # Mock LLM to timeout first, succeed on retry
    # Verify log contains "attempt 1/3" and "attempt 2/3"
    # Assert final sections are returned
```

### 3.2 Spec B: Caching & Performance

**When implementing:**
1. Add `section_cache` to `ReportState`
2. In `write_section()`:
   - Before LLM call: `cache_key = hash(section_title + topic)`
   - Check: `if cache_key in state.get('section_cache', {})`
   - Log hit: `logger.info('[writer] cache hit | section_title="%s"', section_title)`
   - If miss, log: `logger.info('[writer] cache miss | section_title="%s"', section_title)`
   - Store result: `section_cache[cache_key] = result`
3. Add env var check: `CACHE_ENABLED = os.getenv('CACHE_ENABLED', 'true').lower() == 'true'`

**Generate test:**
```python
def test_section_cache_hit():
    # Call write_section twice with same params
    # Verify second call doesn't invoke LLM
    # Check logs show "cache hit"
```

### 3.3 Spec C: Progress Tracking

**When implementing:**
1. Add `progress_metadata` dict to state
2. In each agent, update:
   - `current_stage`: agent name
   - `sections_completed`: count so far
   - `sections_total`: total expected
3. Log with percentage: `logger.info('[workflow] progress | %d/%d sections (%.0f%%)', completed, total, (completed/total)*100)`
4. Add `start_time` tracking for ETA (optional)

**Generate test:**
```python
def test_progress_tracking():
    # Run generate_report
    # Verify logs show "1/4 sections", "2/4 sections", etc.
```

### 3.4 Spec D: Timeout Handling

**When implementing:**
1. Add timeout params to ChatOpenAI: `request_timeout=timeout_seconds`
2. Wrap LLM calls in timeout handler
3. Log timeout: `logger.warning('[writer] timeout on section | section_title="%s" | timeout=%ds', section_title, timeout)`
4. Implement single retry: `attempt_timeout = timeout_seconds * 0.5` (faster retry)
5. On second timeout, skip section: `logger.error('[writer] timeout again, skipping | section_title="%s"', section_title)`

**Generate test:**
```python
def test_timeout_triggers_retry():
    # Mock slow response
    # Verify timeout logged and retry triggered
    # Verify final result (skip or success)
```

### 3.5 Spec E: Content Validation

**When implementing:**
1. Create validator function: `validate_section(content: str, section_title: str) -> bool`
2. Check rules: MIN_LENGTH, no extra markdown, topic mention
3. In `write_section()`, after LLM call:
   ```python
   if not validate_section(section_text, section_title):
       logger.warning('[writer] validation failed | section_title="%s" | reason="%s"', section_title, reason)
       # Retry with stricter prompt
   ```
4. Log success: `logger.info('[writer] validation passed | section_title="%s"', section_title)`

**Generate test:**
```python
def test_content_validation():
    # Generate sections with various lengths
    # Verify validation accepts good content
    # Verify validation rejects short content
```

### 3.6 Spec F: Configuration Management

**When implementing:**
1. Create `config.py`:
   ```python
   import os
   from dataclasses import dataclass
   
   @dataclass
   class Config:
       MODEL_NAME: str = "gpt-4o-mini"
       LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
       TIMEOUT_SECTION: int = int(os.getenv("SECTION_TIMEOUT", "30"))
       MAX_RETRIES: int = 3
       # ... etc
   
   config = Config()
   ```
2. Import and use: `from config import config` → `timeout = config.TIMEOUT_SECTION`
3. Remove all magic numbers from code

**Generate test:**
```python
def test_config_loads():
    from config import config
    assert config.MODEL_NAME == "gpt-4o-mini"
    assert config.MAX_RETRIES == 3
```

### 3.7 Spec G: Testing & Validation

**Test Structure:**
```
tests/
├── test_agents.py           # Unit tests for individual agents
├── test_workflow.py         # Integration tests
├── test_error_handling.py   # Error scenarios
├── test_performance.py      # Performance/caching
└── conftest.py              # Pytest fixtures
```

**Fixture Pattern:**
```python
@pytest.fixture
def mock_llm():
    with patch('report_generator.llm') as mock:
        mock.invoke.return_value.content = "Test content\nTest section"
        yield mock

def test_planner_with_mock(mock_llm):
    state = ReportState(topic="AI", sections=[], section_drafts={}, final_report="")
    result = planner_agent(state)
    assert len(result['sections']) == 2
```

---

## 4. Logging Best Practices

### 4.1 Log Format Standards

**Always use this format:**
```python
# ✅ CORRECT
logger.info('[agent] action | key="%s" | value=%d', key_var, value_var)

# ❌ WRONG
logger.info(f"[agent] {key_var} did something with {value_var}")
logger.info('[agent] action | key="' + key_var + '" | value=' + str(value_var))
```

**Reasons:**
- Lazy formatting is more efficient
- Consistent parsing for log aggregation tools
- Security: no risk of log injection

### 4.2 When to Log

| Scenario | Level | Example |
|----------|-------|---------|
| Agent start | INFO | `logger.info('[agent] started \| key="%s"', value)` |
| LLM call | INFO | `logger.info('[agent] invoking llm')` |
| Retry attempt | WARNING | `logger.warning('[agent] retry %d/%d', attempt, max)` |
| Agent complete | INFO | `logger.info('[agent] completed \| result=%d', result)` |
| Error | ERROR | `logger.error('[agent] error \| type="%s"', error_type)` |
| Debug info | DEBUG | `logger.debug('[agent] state=%s', state_dict)` |

### 4.3 Agent Name Conventions

- Use function name without `_agent` suffix: `planner_agent` → `[planner]`
- Use class name for class methods: `WriterCoordinator.execute()` → `[writer_coordinator]`
- Use helper function name for utils: `validate_section()` → `[validator]`

---

## 5. Enhancement Workflow (Step-by-Step)

### When Adding a New Feature

1. **Create a new spec section** (e.g., "Spec H: New Feature")
   - Define requirements
   - List test criteria
   - Describe logging expectations

2. **Ask Copilot Chat (via `/`):**
   ```
   I'm implementing Spec H from spec.md.
   
   Current code: [paste relevant code]
   
   Spec H requirements:
   [paste spec section]
   
   Generate the implementation following all logging patterns and error handling from existing code.
   ```

3. **Review generated code:**
   - Verify logging format matches patterns in section 4.1
   - Check all test criteria from spec are covered
   - Ensure error handling follows Spec A patterns

4. **Generate tests:**
   ```
   @Copilot Generate test for Spec H implementation.
   Test criteria from spec: [paste test_criteria]
   ```

5. **Validate:**
   - Run: `pytest tests/` to verify all tests pass
   - Check logs show proper format: `grep '\[agent\]' generated_logs.txt`
   - Measure performance if applicable

6. **Update spec.md:**
   - Mark spec as "Implemented" with date
   - Link to commit/PR

---

## 6. Code Review Checklist

When reviewing code changes, verify:

- [ ] **Spec Reference:** Does code reference which spec it implements?
- [ ] **Logging:** Are all agent transitions logged with [agent_name] prefix?
- [ ] **Error Handling:** Are LLM errors caught and retried per Spec A?
- [ ] **State Management:** Are state changes returned via {**state, 'field': value}?
- [ ] **Testing:** Are new functions covered by tests in tests/ dir?
- [ ] **Configuration:** Are magic numbers moved to config.py?
- [ ] **Docstrings:** Do functions explain what spec they implement?
- [ ] **Performance:** Does logging use lazy formatting (logger.info(..., var) not f-strings)?
- [ ] **Type Hints:** Are function signatures fully type-hinted?

---

## 7. Common Patterns

### Pattern: Adding a New Agent
```python
def new_agent(state: ReportState) -> ReportState:
    """
    <Purpose> per Spec X.
    """
    logger.info('[new_agent] started | field="%s"', state.get('field'))
    
    try:
        # Main logic
        result = some_operation(state)
        logger.info('[new_agent] completed | result="%s"', result)
        return {**state, 'result_field': result}
        
    except Exception as e:
        logger.error('[new_agent] failed | error="%s"', str(e))
        raise ReportGenerationError(f"new_agent failed: {e}") from e
```

### Pattern: Adding Config Parameter
```python
# In config.py
NEW_PARAM: str = os.getenv("NEW_PARAM", "default_value")

# In agent
from config import config
value = config.NEW_PARAM
```

### Pattern: Adding Cached Operation
```python
cache_key = hash_func(input1, input2)
if cache_key in state.get('cache', {}):
    logger.info('[component] cache hit | key="%s"', cache_key)
    return state['cache'][cache_key]

logger.info('[component] cache miss | key="%s"', cache_key)
result = expensive_operation()
state['cache'][cache_key] = result
return result
```

---

## 8. Success Metrics

After implementing a spec:
- ✅ All test criteria pass
- ✅ Logs show expected messages at correct levels
- ✅ No performance degradation (< 5% overhead for logging/caching)
- ✅ Code follows patterns in section 7
- ✅ Docstrings reference spec
- ✅ Config parameters are used (no magic numbers)
