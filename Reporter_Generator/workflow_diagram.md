# Report Generator Workflow Diagram

## Flowchart

```mermaid
flowchart LR
    S([Start: generate_report(topic)])
    I[Initialize ReportState:\n- topic\n- sections = []\n- section_drafts = {}\n- final_report = ""]
    P[Planner Agent\nplanner_agent(state)]
    O[Outline Produced\nsections: 3-4 titles]
    W[Writer Coordinator\nwriter_coordinator(state)]
    L{For each section}
    WS[Writer Agent\nwrite_section(section_title, topic)]
    SD[Save draft in section_drafts]
    C[Compiler Agent\ncompiler_agent(state)]
    R[Assemble Markdown Report\ntitle + all section drafts]
    E([End: return final_report])

    S --> I --> P --> O --> W --> L
    L --> WS --> SD --> L
    L --> C --> R --> E
```

## Sequence Diagram

```mermaid
sequenceDiagram
    participant Main as generate_report
    participant Planner as planner_agent
    participant Coord as writer_coordinator
    participant Writer as write_section
    participant Compiler as compiler_agent

    Main->>Planner: state(topic)
    Planner->>Planner: LLM outline call
    Planner-->>Main: state + sections

    Main->>Coord: state(sections)
    loop each section_title
        Coord->>Writer: write_section(section_title, topic)
        Writer->>Writer: LLM section call
        Writer-->>Coord: section text
        Coord->>Coord: section_drafts[section_title] = text
    end
    Coord-->>Main: state + section_drafts

    Main->>Compiler: state(sections, section_drafts)
    Compiler->>Compiler: build final_report markdown
    Compiler-->>Main: state + final_report
```
