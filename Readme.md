# Simplilearn Agentic AI - CrewAI Framework

A comprehensive project repository for building intelligent agentic solutions using the **CrewAI framework**. This project demonstrates modern approaches to AI agent development, orchestration, and workflow automation.

## 📋 Table of Contents

- [Project Overview](#project-overview)
- [What is CrewAI?](#what-is-crewai)
- [Quick Start](#quick-start)
- [Installation](#installation)
- [Project Structure](#project-structure)
- [Configuration](#configuration)
- [Usage Examples](#usage-examples)
- [Available Tools](#available-tools)
- [Resources](#resources)

---

## 📌 Project Overview

This repository contains a collection of Agentic AI solutions built using the **CrewAI framework**. It serves as a learning and experimentation platform for:

- **Agent Design & Development**: Building intelligent agents with specialized roles and capabilities
- **Multi-Agent Orchestration**: Coordinating multiple agents to solve complex tasks
- **Task Automation**: Creating autonomous workflows for various business processes
- **LLM Integration**: Working with multiple LLM providers (OpenAI, Anthropic, Google Generative AI)
- **OpenAI Agents SDK**: Exploring OpenAI's agent-based approach to AI development

**Branch**: `feature/ed_donner_crew_ai`  
**Framework**: CrewAI v1.14.4  
**Python**: 3.8+

---

## 🤖 What is CrewAI?

CrewAI is a cutting-edge framework for building collaborative AI agents. Key features include:

- **Agent Abstraction**: Defines agents with specific roles, goals, and backstories
- **Task Definition**: Creates structured tasks with clear objectives and expected outputs
- **Crew Orchestration**: Manages multiple agents working together toward common goals
- **Tool Integration**: Agents can use custom tools and external services
- **Memory Management**: Maintains context across agent interactions
- **LLM Flexibility**: Supports multiple language model providers

For more information: [CrewAI Documentation](https://docs.crewai.com/)

---

## 🚀 Quick Start

### 1. Run the Setup Script

The simplest way to set up CrewAI and all dependencies:

```bash
bash setup_crewai.sh
```

This script will:
- ✓ Check Python installation
- ✓ Upgrade pip and dependencies
- ✓ Install CrewAI framework
- ✓ Install all required packages
- ✓ Verify the installation

### 2. Configure Environment

Create a `.env` file in the project root with your API keys:

```bash
# OpenAI API
OPENAI_API_KEY=your_openai_api_key

# Anthropic API (Claude)
ANTHROPIC_API_KEY=your_anthropic_api_key

# Google Generative AI
GOOGLE_API_KEY=your_google_api_key

# Optional: Model preferences
OPENAI_MODEL_NAME=gpt-4
```

### 3. Start Using CrewAI

```python
from crewai import Agent, Task, Crew

# Create an agent
agent = Agent(
    role="Data Analyst",
    goal="Analyze data and provide insights",
    backstory="You are an expert data scientist"
)

# Create a task
task = Task(
    description="Analyze the provided dataset",
    agent=agent
)

# Create a crew
crew = Crew(agents=[agent], tasks=[task])

# Execute
result = crew.kickoff()
```

---

## 📦 Installation

### Prerequisites

- **Python**: 3.8 or higher
- **pip**: Package manager for Python
- **API Keys**: From OpenAI, Anthropic, or Google (depending on your use case)

### Automated Installation

```bash
bash setup_crewai.sh
```

### Manual Installation

If you prefer manual installation:

```bash
# Upgrade pip
python3 -m pip install --upgrade pip setuptools wheel

# Install CrewAI and dependencies
python3 -m pip install -r requirements.txt
```

### Verify Installation

```bash
python3 -c "import crewai; print(f'CrewAI version: {crewai.__version__}')"
```

---

## 📁 Project Structure

```
Simplilearn_Agentic_AI/
├── setup_crewai.sh              # Main setup script (run this to install CrewAI)
├── requirements.txt             # Python dependencies
├── Readme.md                   # This file
├── OpenAIAgentsSDK_workflow.ipynb # Jupyter notebook with examples and workflows
└── .env                        # Environment variables (create this file with your API keys)
```

### File Descriptions

| File | Purpose |
|------|---------|
| `setup_crewai.sh` | Automated setup script for installing all dependencies and CrewAI |
| `requirements.txt` | List of all Python packages required for the project |
| `OpenAIAgentsSDK_workflow.ipynb` | Interactive Jupyter notebook with CrewAI examples and workflows |
| `.env` | Configuration file for API keys and environment variables (NOT in repo) |

---

## ⚙️ Configuration

### Environment Variables

Create a `.env` file with the following variables:

```bash
# LLM Providers
OPENAI_API_KEY=sk-xxx...
ANTHROPIC_API_KEY=sk-ant-xxx...
GOOGLE_API_KEY=xxx...

# Optional: Model Configuration
OPENAI_MODEL_NAME=gpt-4
OPENAI_TEMPERATURE=0.7
ANTHROPIC_MODEL_NAME=claude-3-opus-20240229

# Optional: Logging
LOG_LEVEL=INFO
```

### Loading Configuration

In your Python code:

```python
from dotenv import load_dotenv
import os

load_dotenv()

openai_key = os.getenv("OPENAI_API_KEY")
anthropic_key = os.getenv("ANTHROPIC_API_KEY")
```

---

## 💡 Usage Examples

### Example 1: Simple Agent

```python
from crewai import Agent, Task, Crew
from dotenv import load_dotenv

load_dotenv()

# Create an agent
analyst = Agent(
    role="Data Analyst",
    goal="Provide accurate data analysis",
    backstory="Expert in statistical analysis"
)

# Create a task
task = Task(
    description="Analyze sales trends",
    agent=analyst,
    expected_output="Summary of sales trends"
)

# Create and execute crew
crew = Crew(agents=[analyst], tasks=[task])
result = crew.kickoff()
print(result)
```

### Example 2: Multi-Agent Crew

```python
from crewai import Agent, Task, Crew

# Create multiple agents
researcher = Agent(
    role="Researcher",
    goal="Find relevant information",
    backstory="Thorough research specialist"
)

writer = Agent(
    role="Content Writer",
    goal="Write compelling content",
    backstory="Expert writer with attention to detail"
)

# Create tasks
research_task = Task(
    description="Research AI trends",
    agent=researcher
)

writing_task = Task(
    description="Write an article about AI trends",
    agent=writer
)

# Create and execute crew
crew = Crew(agents=[researcher, writer], tasks=[research_task, writing_task])
result = crew.kickoff()
```

### Example 3: Running in Jupyter

```bash
jupyter notebook OpenAIAgentsSDK_workflow.ipynb
```

---

## 🛠️ Available Tools

CrewAI agents can use various tools:

### Built-in Tools (crewai-tools)

- **Web Search**: Search the internet for information
- **File Operations**: Read, write, and manage files
- **Code Execution**: Execute Python code
- **API Integration**: Call external APIs
- **Database Operations**: Query databases

### Custom Tools

You can create custom tools by extending the `Tool` class:

```python
from crewai_tools import tool

@tool
def custom_tool(input_text: str) -> str:
    """Custom tool description"""
    return f"Processed: {input_text}"
```

---

## 📚 Resources

### Official Documentation
- [CrewAI Docs](https://docs.crewai.com/)
- [CrewAI GitHub](https://github.com/joaomdmoura/crewai)

### LLM Providers
- [OpenAI API Docs](https://platform.openai.com/docs)
- [Anthropic Claude Docs](https://docs.anthropic.com)
- [Google Generative AI](https://ai.google.dev)

### Learning Resources
- [Simplilearn LinkedIn](https://linkedin.com/company/simplilearn)
- [AI & Machine Learning Courses](https://simplilearn.com)

---

## 🔄 Maintenance & Reinstallation

To update or reinstall CrewAI at any time:

```bash
bash setup_crewai.sh
```

To update specific packages:

```bash
python3 -m pip install --upgrade crewai crewai-tools
```

---

## 📝 Notes

- The setup script will handle all Python dependencies automatically
- API keys are sensitive—never commit `.env` file to version control
- Ensure your Python version is 3.8 or higher
- CrewAI v1.14.4 is the currently installed version
- The `feature/ed_donner_crew_ai` branch is dedicated to CrewAI development

---

## 📧 Support & Contribution

For questions, issues, or contributions, please refer to the official CrewAI repository or Simplilearn resources.

---

**Last Updated**: May 2026  
**Framework**: CrewAI v1.14.4  
**Status**: Active Development
