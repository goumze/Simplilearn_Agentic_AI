# Run Outcomes — LangChain vs LangGraph Q&A Agent

**Run date:** Friday, May 22, 2026  
**Model used:** `gpt-4o-mini` (temperature = 0)  
**LangChain version:** 1.3.1  
**LangGraph version:** 0.2.x  

---

## Environment note

Both projects load the shared `.env` file at the repo root and install
their own isolated virtual environment under `.venv/` on first run.

> ⚠️ **LangChain 1.x compatibility fix** — `AgentExecutor` and `create_react_agent`
> were removed in LangChain 1.0. The `langchain_project` was updated to use the
> modern **LCEL tool-calling loop** (`llm.bind_tools()` + manual message loop)
> and the `@tool` decorator was updated to import from `langchain_core.tools`.

---

## Project 1 — LangChain LCEL Agent

**Execution model:** Imperative Python loop — the LLM decides which tool to call,
the loop executes it, appends a `ToolMessage`, then calls the LLM again until no
more tool calls are requested.

```
  HumanMessage ──► ChatOpenAI.bind_tools() ──► AIMessage
                          │
                   tool_calls present?
                    Yes │         │ No
                        ▼         ▼
                   call tools   return answer
                   (ToolMessage)
                        │
                        └──► ChatOpenAI again … (repeat up to 6×)
```

### Test Results

| # | Question | Tool Used | Final Answer |
|---|----------|-----------|--------------|
| 1 | What is the square root of 256? | `calculator` | The square root of 256 is **16**. |
| 2 | What is today's date? | `get_current_date` | Today's date is **Friday, May 22, 2026**. |
| 3 | Tell me about LangGraph. | `knowledge_base_lookup` | LangGraph is a library built on top of LangChain for creating stateful, multi-actor agentic applications. It models workflows as directed graphs (nodes + edges) and supports cycles for fine-grained control over agent state and routing. |
| 4 | How many words are in 'The quick brown fox jumps over the lazy dog'? | `word_counter` | The sentence contains **9 words**. |
| 5 | Calculate (15 * 23) + round(sqrt(81)) | `calculator` | Result is **354**. |
| 6 | What is Agentic AI? | `knowledge_base_lookup` | Agentic AI refers to AI systems that can autonomously plan, make decisions, use tools, and take sequences of actions to accomplish complex goals with minimal human intervention. |

### Console output (abbreviated)

```
=================================================================
  LangChain LCEL Agent — Q&A with Tool Use  (LangChain 1.x)
=================================================================

  Test 1/6: What is the square root of 256?
    [iter 1] → tool 'calculator'  args={'expression': 'sqrt(256)'}
    [iter 1] ← result: 16.0
  ✔  Final Answer: The square root of 256 is 16.

  Test 2/6: What is today's date?
    [iter 1] → tool 'get_current_date'  args={'query': 'today'}
    [iter 1] ← result: Current date : Friday, May 22, 2026 / Current time : 15:03:07
  ✔  Final Answer: Today's date is Friday, May 22, 2026.

  Test 3/6: Tell me about LangGraph.
    [iter 1] → tool 'knowledge_base_lookup'  args={'topic': 'LangGraph'}
    [iter 1] ← result: LangGraph is a library built on top of LangChain ...
  ✔  Final Answer: LangGraph is a library built on top of LangChain ...

  Test 4/6: How many words are in the sentence: '...'?
    [iter 1] → tool 'word_counter'  args={'text': 'The quick brown fox ...'}
    [iter 1] ← result: The provided text contains 9 word(s).
  ✔  Final Answer: The sentence contains 9 words.

  Test 5/6: Calculate (15 * 23) + round(sqrt(81))
    [iter 1] → tool 'calculator'  args={'expression': '(15 * 23) + round(sqrt(81))'}
    [iter 1] ← result: 354
  ✔  Final Answer: The result is 354.

  Test 6/6: What is Agentic AI?
    [iter 1] → tool 'knowledge_base_lookup'  args={'topic': 'Agentic AI'}
    [iter 1] ← result: Agentic AI refers to AI systems ...
  ✔  Final Answer: Agentic AI refers to AI systems ...

=================================================================
  All test cases completed.
=================================================================
```

**Status:** ✅ All 6 test cases passed. Each required exactly 1 tool call.

---

## Project 2 — LangGraph StateGraph Agent

**Execution model:** Declarative directed graph — the workflow is expressed as
nodes and edges compiled into a runnable. The agent node and the tool node are
separate graph nodes; conditional routing decides whether to loop back or stop.

```
  START ──► [ agent node ] ──► tool_calls? ──► [ tools node ] ──┐
                    │                                             │
                   END ◄─────────────────────────────────────────┘
                       (no more tool calls)
```

State is a `TypedDict` (`AgentState`) whose `messages` list grows via the
`operator.add` reducer as each node appends its outputs.

### Test Results

| # | Question | Graph steps | Tool Used | Final Answer |
|---|----------|-------------|-----------|--------------|
| 1 | What is the square root of 256? | 3 | `calculator` | The square root of 256 is **16**. |
| 2 | What is today's date? | 3 | `get_current_date` | Today's date is **Friday, May 22, 2026**. |
| 3 | Tell me about LangGraph. | 3 | `knowledge_base_lookup` | LangGraph is a library built on top of LangChain for creating stateful, multi-actor agentic applications … |
| 4 | How many words are in 'The quick brown fox jumps over the lazy dog'? | 3 | `word_counter` | The sentence contains **9 words**. |
| 5 | Calculate (15 * 23) + round(sqrt(81)) | 3 | `calculator` | Result is **354**. |
| 6 | What is Agentic AI? | 3 | `knowledge_base_lookup` | Agentic AI refers to AI systems that can autonomously plan … |

> Each run took 3 streaming steps: initial HumanMessage → agent (tool call) → tool result → agent (final answer).

### Console output (abbreviated)

```
=================================================================
  LangGraph StateGraph Agent — Q&A with Tool Use
=================================================================

  Graph topology:
    START ──► agent ──► (tool calls?) ──► tools ──┐
                │                                  │
               END ◄─────────────────────────────┘
                   (no more tool calls)

  Test 1/6: What is the square root of 256?
    [Step 1] Tool 'None' returned: What is the square root of 256?
    [Step 2] Agent → calling tool(s): calculator
    [Step 3] Tool 'calculator' returned: 16.0
  ✔  Final Answer: The square root of 256 is 16.

  Test 2/6: What is today's date?
    [Step 2] Agent → calling tool(s): get_current_date
    [Step 3] Tool 'get_current_date' returned: Current date : Friday, May 22, 2026 ...
  ✔  Final Answer: Today's date is Friday, May 22, 2026.

  Test 3/6: Tell me about LangGraph.
    [Step 2] Agent → calling tool(s): knowledge_base_lookup
    [Step 3] Tool 'knowledge_base_lookup' returned: LangGraph is a library ...
  ✔  Final Answer: LangGraph is a library built on top of LangChain ...

  Test 4/6: How many words are in the sentence: '...'?
    [Step 2] Agent → calling tool(s): word_counter
    [Step 3] Tool 'word_counter' returned: The provided text contains 9 word(s).
  ✔  Final Answer: The sentence contains 9 words.

  Test 5/6: Calculate (15 * 23) + round(sqrt(81))
    [Step 2] Agent → calling tool(s): calculator
    [Step 3] Tool 'calculator' returned: 354
  ✔  Final Answer: The result is 354.

  Test 6/6: What is Agentic AI?
    [Step 2] Agent → calling tool(s): knowledge_base_lookup
    [Step 3] Tool 'knowledge_base_lookup' returned: Agentic AI refers to AI systems ...
  ✔  Final Answer: Agentic AI refers to AI systems ...

=================================================================
  All test cases completed.
=================================================================
```

**Status:** ✅ All 6 test cases passed. Each ran through 3 graph steps (initial state → agent → tool → agent final).

---

## Comparison Summary

| Aspect | LangChain (LCEL) | LangGraph (StateGraph) |
|--------|-----------------|------------------------|
| **Answers correct** | 6 / 6 | 6 / 6 |
| **Answer quality** | Identical | Identical |
| **Tool calls per question** | 1 | 1 |
| **Execution model** | Imperative Python `while` loop | Declarative compiled graph |
| **State management** | Local `list[BaseMessage]` variable | `AgentState` TypedDict — external, inspectable |
| **Routing logic** | `if response.tool_calls` in Python | `should_continue()` conditional edge |
| **Streaming** | Not used | `app.stream()` — step-by-step visibility |
| **Cycles** | `for` loop with max iterations | Explicit `tools → agent` back-edge |
| **Observability** | Print inside loop | Each graph step is a separate streamed value |
| **Extensibility** | Add more `if/else` branches | Add more nodes and edges to the graph |
| **Best for** | Simple, linear tool-use chains | Complex multi-step, multi-actor workflows |

### Key takeaway

Both frameworks produce **identical final answers** for these test cases because
the problem is simple (one tool call per question). The architectural difference
becomes significant at scale:

- **LangChain LCEL** is concise and easy to reason about for straightforward pipelines. State lives inside a plain Python function — no framework overhead.  
- **LangGraph** shines when workflows need **branching**, **cycles**, **parallel nodes**, **checkpointing**, or **human-in-the-loop** pauses. The graph is introspectable, serialisable, and each step can be monitored independently.
