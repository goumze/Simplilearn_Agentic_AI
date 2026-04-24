# Course End Project
# NewsGenie – An AI-Powered Information and News Assistant

# Overview
# In this project, you will build NewsGenie, an AI-powered information and news assistant
# designed to help users navigate today’s fast-paced digital landscape. You will develop a
# system that efficiently filters misinformation, curates reliable and up-to-date news, and
# provides quick answers to general queries—all within a single, unified platform.

# Instructions
# Submission: Submit a detailed report or presentation via the LMS, including:
# 1. AI chatbot design: Guidelines for conversation management and query
# differentiation
# 2. Real-time news integration: Sample outputs showing news updates for technology,
# finance, and sports categories
# 3. Workflow and error handling: A proposed process detailing API integration, fallback
# mechanisms, and overall query processing management

# Task
# The core task is to build NewsGenie as a unified platform that:
# 1. Handles conversations: Develop an AI chatbot that can interpret and answer general
# queries while distinguishing them from news requests
# 2. Integrates APIs: Combine a real-time news API with a web search tool to fetch topic-
# specific news and additional external resources
# 3. Manages workflow: Utilize a LangGraph-based workflow to process user requests
# efficiently and maintain conversation context
# 4. Delivers an intuitive UI: Provide a robust, interactive interface via Streamlit that
# allows users to select news categories and input queries effortlessly

# Actions
# To achieve these objectives, the following actions will be implemented:
# 1. Chatbot development:
# • Build and train an AI chatbot using natural language processing techniques to
# manage and distinguish between different query types
# 2. API and web search integration:
# • Integrate a real-time news API to retrieve the latest news based on user-selected
# categories
# • Implement a web search tool to dynamically fetch external information that
# complements the chatbot’s responses
# 3. Workflow optimization:
# • Employ a LangGraph-based workflow to streamline query processing, ensuring
# efficient handling of both news and general queries
# • Develop fallback mechanisms to manage API failures or instances when no
# relevant news is found
# 4. User interface deployment:
# • Design and deploy a Streamlit-based frontend that is user-friendly, supports
# session management, and optimizes response times
# • Ensure the interface allows users to easily choose news categories and interact
# with the assistant
# 5. Error handling and performance optimization:
# • Incorporate strategies to manage missing API keys, failed API

# Result
# The final submission will include:
# 1. An interactive AI-powered assistant that delivers instant responses to general
# queries while providing real-time, curated news updates
# 2. A fully integrated system showcasing the use of a real-time news API, a dynamic web
# search tool, and a LangGraph-based workflow for efficient query processing
# 3. A demonstration of the user-friendly interface built with Streamlit, highlighting
# session management, error handling, and responsive design
# 4. A detailed explanation of fallback mechanisms and optimization strategies ensuring
# reliable performance even during API failures
# This project will demonstrate your ability to integrate multiple AI components into a
# cohesive platform that simplifies information access and enhances the overall user
# experience in a fast-paced digital environment.

import os
import requests # For making API calls
import streamlit as st # For building the user interface
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode, tools_condition
from langchain_community.utilities.tavily_search import TavilySearchAPIWrapper # For web search functionality
import sqlite3
from typing import Annotated, TypedDict

# Load API keys securely from the .env file
load_dotenv()
AI_API_KEY = os.getenv('OPENAI_API_KEY')
NEWS_API_KEY = os.getenv('NEWSAPI_API_KEY')
SEARCH_API_KEY = os.getenv('TAVILY_API_KEY')

# Ensure all API keys are available before proceeding
if not all([AI_API_KEY, NEWS_API_KEY, SEARCH_API_KEY]):
    raise ValueError("Missing API keys. Please check your .env file.")

# Identifying Key Components
web_search_tool = TavilySearchAPIWrapper()

def search_web(query: str, max_results=8) -> list:
    """Fetch web search results from Tavily API."""
    search_results = web_search_tool.raw_results(
        query=query,
        max_results=max_results,
        search_depth='advanced',
        include_answer=False, # We only want the search results, not a generated answer
        include_raw_content=True # This ensures we get the full content of the search results, which is crucial for accurate information retrieval
    )
    return search_results

def get_news(category: str) -> dict:
    """Fetch real-time news articles from NewsAPI based on the selected category."""
    base_url = "https://newsapi.org/v2/top-headlines"
    news_url = f"{base_url}?apiKey={NEWS_API_KEY}&category={category}&language=en"
    
    response = requests.get(news_url)
    news_data = response.json() # Parse the JSON response to a Python dictionary
    return news_data if news_data.get("articles") else {"error": "No news found for the selected category."}

# Breaking Down API Integrations
# Define tools for AI assistant
assistant_tools = [search_web, get_news]

# Initialize AI assistant with OpenAI's GPT model and bind tools
ai_assistant = ChatOpenAI(model="gpt-3.5-turbo", temperature=0, openai_api_key=AI_API_KEY)
ai_with_tools = ai_assistant.bind_tools(assistant_tools)

# AI Chatbot Workflow
class ConversationState(TypedDict):
    dialogue_history: Annotated[list, add_messages]

news_graph = StateGraph(ConversationState)

def generate_response(state: ConversationState):
    """Processes user queries and determines AI response or tool usage."""
    messages = state["dialogue_history"]
    return {"dialogue_history": [ai_with_tools.invoke(messages)]}

# Add AI response and tool execution nodes
news_graph.add_node("ai_response", generate_response)
tool_node = ToolNode(tools=assistant_tools)
news_graph.add_node("news_tool", tool_node)
news_graph.add_conditional_edges("ai_response", tools_condition, ['news_tool', '__end__'])
news_graph.add_edge("news_tool", "ai_response")
news_graph.set_entry_point("ai_response")
news_agent = news_graph.compile()

# ============================================
# 6. Streamlit Frontend
# ============================================
# User interface is designed for ease of use.
# Users enter queries or select news categories via text input.
# UI improvements include displaying previous interactions.

st.title("NewsGenie - AI-Powered News & Information Assistant")

user_session = st.text_input("Session ID:", value="guest001")
query_input = st.text_area("Enter your question or news category (e.g., technology, sports, finance)")

if st.button("Submit"):
    if query_input:
        output_response = process_user_request(query_input, user_session)
        st.markdown(f"**Response:**\n\n{output_response}")
    else:
        st.warning("Please enter a valid input.")

st.write("## Session History")
st.write("Your recent queries and news updates will appear here.")

# ============================================
# 7. Error Handling and Optimization
# ============================================
# Handles missing API keys and failed API calls.
# Optimizes performance by reducing unnecessary API calls.
# Processes long or complex queries efficiently.
