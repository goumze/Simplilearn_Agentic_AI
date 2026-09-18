from typing import Any
from langchain.agents.middleware import AgentMiddleware, AgentState, hook_config
from langgraph.runtime import Runtime
from langchain.agents import create_agent
from langchain_core.tools import tool

class ContentFilterMiddleWare(AgentMiddleware):

   """
   Determine guardrail: Block requests containing banned keywords. 
   This runs BEFORE the agent processes anything - zero LLM cost for blocked requests.
   """

   def __init__(self, banned_keywords: list[str]):
      super().__init__()
      self.banned_keywords = [kw.lower()]
    
