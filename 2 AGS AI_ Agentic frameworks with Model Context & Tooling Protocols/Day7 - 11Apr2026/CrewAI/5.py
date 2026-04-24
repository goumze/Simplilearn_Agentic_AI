# Problem Statement

# Modern content teams and individual creators often struggle with producing high-quality, research-driven blog articles consistently. Researching accurate information, analyzing sources, extracting insights, and turning them into a polished blog requires significant time and coordination between researchers and writers. This workflow becomes even more challenging when handling multiple topics or producing content at scale.

# The objective of this system is to automate the end-to-end blog creation workflow using a multi-agent architecture. The system uses specialized AI agents—one dedicated to fact-based research and another focused on writing structured, engaging content. Each agent operates with clearly defined roles and uses external tools where needed.

# The framework separates agent configuration, task descriptions, and execution logic, enabling flexibility and scalability. External tools such as SerperDevTool and web-scraping utilities allow agents to fetch real-time information, while file-reading and file-writing tools support output management.

# The final deliverable is a fully generated, well-researched blog post based on the user-provided topic, created through coordinated multi-agent execution.

from crewai import Agent, Crew, Process, Task, LLM
# Process → (Optional) Defines parallel or sequential execution of tasks within the crew
from crewai.project import CrewBase, agent, crew, task
# CrewBase → Turns a Python class into a structured CrewAI project
# @agent → Marks a method that returns an Agent
# @crew → Marks a method that returns a Crew
# @task → Marks a method that returns a Task
# Why it matters?
# CrewAI supports "project mode" where:
# Agents live in config files
# Tasks live in config files
# Code becomes cleaner and modular
# This is the enterprise / production style of writing CrewAI workflows.

from crewai_tools import SerperDevTool, ScrapeWebsiteTool, DirectoryReadTool, FileWriterTool,FileReadTool
# SerperDevTool → Search engine tool using Serper API
# ScrapeWebsiteTool → Scrapes webpage content
# DirectoryReadTool → Reads files inside a folder
# FileWriterTool → Lets agents create/edit files
# FileReadTool → Allows reading a file’s contents

import os
from dotenv import load_dotenv
load_dotenv()

@CrewBase # @CrewBase turns this into a project container.
class BlogCrew():
    """"Blog writing crew"""

    agents_config = "agents.yaml"
    tasks_config = "tasks.yaml"

    # These two YAML files store the definitions for:
    # Agents (role, goal, backstory, model)
    # Tasks (description, expected output, parameters)

    @agent
    def researcher(self) -> Agent:
        research_tools = [SerperDevTool()] if os.getenv("SERPER_API_KEY") else []
        return Agent(
            config=self.agents_config['research_agent'], # type: ignore[index]
            tools=research_tools,
            verbose=True
        )

    @agent
    def writer(self) -> Agent:
        return Agent(
            config=self.agents_config['writer_agent'], # type: ignore[index]
            verbose=True
        )

    @task
    def research_task(self) -> Task:
        return Task(
            config=self.tasks_config['research_task'], # type: ignore[index]
            agent = self.researcher()
        )

    @task
    def blog_task(self) -> Task:
        return Task(
            config=self.tasks_config['blog_task'], # type: ignore[index]
            agent = self.writer()
        )

    @crew
    def crew(self) -> Crew:
        return Crew(
            agents=[self.researcher(), self.writer()],
            tasks=[self.research_task(), self.blog_task()]
        )

if __name__ == "__main__":
    blog_crew = BlogCrew()
    blog_crew.crew().kickoff(inputs={"topic": "The future of electrical vehicles"})

# Create:
# agents.yaml
# tasks.yaml