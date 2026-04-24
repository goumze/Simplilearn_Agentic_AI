# HIERARCHICAL process with a MANAGER agent (delegates + reviews)
# 1) Uses Process.hierarchical
# 2) Adds a manager_agent (Editor-in-Chief) who coordinates the crew
# 3) Keeps memory + embeddings exactly as in your reference
# 4) Keeps SerperDevTool for real-time web research

from dotenv import load_dotenv
load_dotenv()

import os
from crewai import LLM, Agent, Task, Crew, Process
from crewai_tools import SerperDevTool

# 1) LLM CONFIG (shared across agents)
# ------------------------------------------------------------
# In CrewAI, LLM() is a wrapper to configure the model used by agents.
# Temperature controls creativity; higher = more creative, lower = more factual/deterministic.
llm = LLM(
    model="gpt-4o",
    temperature=0.7
)

# 2) TOOLS (Real-time internet research)
# ------------------------------------------------------------
# SerperDevTool uses SERPER_API_KEY from environment.
# It enables agents to search the web for updated information.
import os

# 3) AGENTS
# ------------------------------------------------------------
# A) Research Agent (worker)
research_agent = Agent(
    role="Research Specialist",
    goal="Find accurate, interesting, and recent facts about the topic: {topic}",
    backstory=(
        "You are an expert internet researcher. "
        "You prioritize credible sources, recent updates, and factual accuracy."
    ),
    tools=[SerperDevTool()] if os.getenv("SERPER_API_KEY") else [],      # This agent can do web search
    llm=llm,
    verbose=True
)

# B) Writer Agent (worker)
writer_agent = Agent(
    role="Creative Writer",
    goal="Write a short blog summary using the research provided",
    backstory=(
        "You are skilled at writing clear and engaging blog summaries. "
        "You only use the verified facts given by research."
    ),
    llm=llm,
    verbose=True
)

# C) Manager Agent (the boss)
# In hierarchical mode, manager supervises, delegates tasks, and ensures quality.
# allow_delegation=True is important: it enables the manager to assign subtasks to other agents.
manager_agent = Agent(
    role="Editor-in-Chief (Manager)",
    goal=(
        "Run the overall workflow: ensure research is credible and recent, "
        "ensure the final blog is coherent and grounded in research."
    ),
    backstory=(
        "You are the managing editor. You break down the work, delegate to the right agent, "
        "review outputs for quality and factual grounding, and produce the final deliverable."
    ),
    llm=llm,
    verbose=True,
    allow_delegation=True
)

# 4) TASKS
# ------------------------------------------------------------
# Task 1: Research
task1 = Task(
    description=(
        "Find 3-5 interesting and recent facts about {topic} as of year 2025. "
        "Prefer reputable sources and include the year/time reference in each fact."
    ),
    expected_output=(
        "A bullet list of 3-5 facts. Each bullet should be a crisp fact with time reference."
    ),
    agent=research_agent
)

# Task 2: Writing (uses Task 1 output as context)
task2 = Task(
    description=(
        "Write a 100-word blog post summary about {topic} using the facts from the research. "
        "Tone: professional, simple, and engaging. Do NOT invent facts."
    ),
    expected_output="A 100-word blog post summary grounded in the research facts.",
    agent=writer_agent,
    context=[task1]  # This ensures writer sees task1 output
)

# 5) CREW (HIERARCHICAL MODE + MEMORY + EMBEDDINGS)
# ------------------------------------------------------------
# memory=True enables long-term memory so the crew can remember prior runs.
# embedder config defines how memory text gets embedded for similarity search.
crew = Crew(
    agents=[research_agent, writer_agent],
    tasks=[task1, task2],

    # Key change: hierarchical process
    process=Process.hierarchical,

    # Key change: manager agent controls delegation + review
    manager_agent=manager_agent,

    verbose=True,

    # Long-term memory enabled
    memory=True,

    # Embedding provider config for memory
    embedder={
        "provider": "openai",
        "config": {
            "api_key": os.getenv("OPENAI_API_KEY"),
            "model": "text-embedding-3-small"
        }
    }
)

# 6) RUNS (Multiple related queries to test memory)
# ------------------------------------------------------------
# Run 1: Topic A
result_1 = crew.kickoff(inputs={"topic": "The future of electrical vehicles"})
print("\n\n==================== FINAL OUTPUT (RUN 1) ====================\n")
print(result_1)

# Run 2: Follow-up topic (should benefit from memory)
result_2 = crew.kickoff(inputs={"topic": "What is the revenue outlook in this sector?"})
print("\n\n==================== FINAL OUTPUT (RUN 2) ====================\n")
print(result_2)

