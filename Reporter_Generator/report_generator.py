import os
import logging
from typing import TypedDict, List, Dict, Any
from dotenv import load_dotenv
from langgraph.graph import StateGraph, END
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage

load_dotenv(override=True)  # Load environment variables from .env file

class ReportState(TypedDict):
    topic: str
    sections: List[str]
    section_drafts: Dict[str, str]
    final_report: str


def setup_logger() -> logging.Logger:
    """Configure and return a logger for orchestration tracing."""
    print("""Configure and return a logger for orchestration tracing.""")
    logger = logging.getLogger('report_orchestration')
    if logger.handlers:
        return logger

    log_level_name = os.getenv('LOG_LEVEL', 'INFO').upper()
    log_level = getattr(logging, log_level_name, logging.INFO)

    logger.setLevel(log_level)
    handler = logging.StreamHandler()
    formatter = logging.Formatter(
        '%(asctime)s | %(levelname)s | %(name)s | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S',
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.propagate = False
    return logger


logger = setup_logger()

#Initialize the LLM
llm = ChatOpenAI(model='gpt-4o-mini')


def planner_agent(state: ReportState) -> ReportState:
    """
    Planner agent that generates a list of sections for the report based on the topic.
    """
    print("""Planner agent that generates a list of sections for the report based on the topic.""")
    topic = state['topic']
    logger.info('[planner] started | topic="%s"', topic)
    planning_prompt = f"""
    You are a report planning expert. Given the topic: "{topic}"
    
    Create a logical outline with 3-4 main sections for a comprehensive report.
    Return only the section titles, one per line, without numbering.
    
    Example format:
    Introduction and Background
    Current State Analysis
    Future Implications
    Conclusion and Recommendations
    """
    logger.info('[planner] invoking llm for outline generation')
    response = llm.invoke([HumanMessage(content=planning_prompt)])
    sections = [line.strip() for line in response.content.strip().split("\n") if line.strip()]
    logger.info('[planner] completed | sections=%s', sections)
    return {**state, 'sections': sections}

def write_section(section_title: str, topic: str) -> str:
    """
    Helper function to write a single section
    """
    print("""Helper function to write a single section""")
    if any(keyword in section_title.lower() for keyword in ['introduction', 'background', 'analysis', 'current']):
        focus = 'research-backed information and analysis'
        tone = 'professional and factual'
    else:
        focus = 'strategic insights and actionable recommendations'
        tone = 'forward-thinking and suggestive'

    logger.info('[writer] started section | section_title="%s"', section_title)

    writer_prompt = f"""
    You are an expert report writer. Write a detailed section for a report on "{topic}"

    Section to write: "{section_title}"

    Requirements:
    - Write 2-3 substantial paragraphs.
    - Focus on {focus}.
    - Use a {tone}
    - Do not include the section title itself in your response, just the content
    """
    logger.info('[writer] invoking llm for section | section_title="%s"', section_title)
    response = llm.invoke([HumanMessage(content=writer_prompt)])
    section_text = response.content.strip()
    logger.info('[writer] completed section | section_title="%s" | chars=%d', section_title, len(section_text))
    return section_text

def writer_coordinator(state: ReportState) -> ReportState:
    """
    Coordinates the writing of all sections
    """
    print("""Coordinates the writing of all sections""")
    topic = state['topic']
    sections = state['sections']
    section_drafts = {}
    logger.info('[writer_coordinator] started | sections_count=%d', len(sections))

    #Write each section
    for idx, section_title in enumerate(sections, start=1):
        logger.info('[writer_coordinator] dispatching section %d/%d | section_title="%s"', idx, len(sections), section_title)
        section_content = write_section(section_title, topic)
        section_drafts[section_title] = section_content

    logger.info('[writer_coordinator] completed | drafted_sections=%d', len(section_drafts))
    return {**state,'section_drafts':section_drafts}

def compiler_agent(state: ReportState) -> ReportState:
    """
    Compiles the final report from the section drafts
    """
    print("""Compiles the final report from the section drafts""")
    topic = state['topic']
    section_drafts = state['section_drafts']
    sections = state['sections']
    logger.info('[compiler] started | sections_in_plan=%d | drafts_available=%d', len(sections), len(section_drafts))

    final_report_content = f'# Report: {topic}\n\n'

    #Compile Sections in the planned order
    for section_title in sections:
        if section_title in section_drafts:
            final_report_content += f'## {section_title}\n\n{section_drafts[section_title]}\n\n'
            logger.info('[compiler] appended section | section_title="%s"', section_title)
    
    logger.info('[compiler] completed | final_report_chars=%d', len(final_report_content))
    return {**state, 'final_report': final_report_content}

#----Graph Definition----
workflow = StateGraph(ReportState)

# Add Nodes
workflow.add_node('planner', planner_agent)
workflow.add_node('writer_coordinator', writer_coordinator)
workflow.add_node('compiler', compiler_agent)

#Set the entry point
workflow.set_entry_point('planner')

#Add edge (simple sequential flow)
workflow.add_edge('planner', 'writer_coordinator')
workflow.add_edge('writer_coordinator', 'compiler')
workflow.add_edge('compiler', END)

#Compile the graph
app = workflow.compile()


# --- Execution Functions ---


def generate_report(topic: str) -> str:
    """Generate a report using the sequential workflow."""
    logger.info('[workflow] started report generation | topic="%s"', topic)
    initial_state = {'topic': topic, 'sections': [], 'section_drafts': {}, 'final_report': ''}
    result = app.invoke(initial_state, debug=True)
    logger.info('[workflow] completed report generation | final_report_chars=%d', len(result['final_report']))
    return result['final_report']


if __name__ == '__main__':
    topic = 'The Impact of Artificial Intelligence on Healthcare'

    print(f'Generating report on: {topic}...')
    report = generate_report(topic)
    print(report)

    # For async version:
    # import asyncio
    # report_async = asyncio.run(generate_report_async(topic))
    # print(report_async)

