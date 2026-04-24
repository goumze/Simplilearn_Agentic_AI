# Problem Statement

# Organizations and content creators increasingly need accurate research and high-quality written outputs generated quickly and consistently. Manually searching the internet for updated information and then converting that information into clear, engaging blog content is time-consuming, error-prone, and difficult to scale.

# To streamline this process, an automated research-and-writing workflow is required. Such a workflow must be capable of:
# Retrieving verified, recent information from reliable online sources.
# Understanding and organizing the research into meaningful facts.
# Converting those facts into professionally written, context-aware summaries or blog posts.

# The goal of this project is to build a multi-agent CrewAI system where one agent conducts real-time research using external search tools, and another agent transforms this research into a coherent and engaging blog article. The system must also support memory and embeddings so the crew can maintain context across multiple related queries.

# This automated pipeline will help businesses, bloggers, educators, and analysts generate research-driven written content at scale, with consistent quality and reduced manual effort.

from dotenv import load_dotenv
load_dotenv()

from crewai import LLM
import os

llm = LLM(
    model="gpt-4o",
    temperature=0.7
)

import os
from crewai import Agent, Task, Crew
from crewai_tools import SerperDevTool

research_agent = Agent(
    role="Research Specialist",
    goal="Research interesting facts about the topic: {topic}",
    backstory="You are an expert at finding relevant and factual data.",
    tools=[SerperDevTool()] if os.getenv("SERPER_API_KEY") else [],
    verbose=True,
    llm=llm
)

writer_agent = Agent(
    role="Creative Writer",
    goal="Write a short blog summary using the research",
    backstory="You are skilled at writing engaging summaries based on provided content.",
    llm=llm,
    verbose=True,
)

task1 = Task(
    description="Find 3-5 interesting and recent facts about {topic} as of year 2025.",
    expected_output="A bullet list of 3-5 facts",
    agent=research_agent,
)

task2 = Task(
    description="Write a 100-word blog post summary about {topic} using the facts from the research.",
    expected_output="A blog post summary",
    agent=writer_agent,
    context=[task1],
)

crew = Crew(
    agents=[research_agent, writer_agent],
    tasks=[task1, task2],
    verbose=True,
    memory=True, # Turns on long-term memory for the crew.
    embedder={ # Defines the embedding system used for memory storage. Embedding converts text into numeric vectors for similarity search.
        "provider": "openai",
        "config": {
            "api_key": os.getenv("OPENAI_API_KEY"),
            "model": "text-embedding-3-small"
        }
    }
)

crew.kickoff(inputs={"topic": "The future of electrical vehicles"})
crew.kickoff(inputs={"topic": "What is the revenue outlook in this sector?"})
crew.kickoff(inputs={"topic": "My name is Darshan, can you write a blog post about the future of electrical vehicles for me?"})
crew.kickoff(inputs={"topic": "What are the top 3 companies in this sector?"})
crew.kickoff(inputs={"topic": "Do you remember the facts you found about the future of electrical vehicles?"})

# Additional Exploration: https://ai.google.dev/gemini-api/docs/crewai-example