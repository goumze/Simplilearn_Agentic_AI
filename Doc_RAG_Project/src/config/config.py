""" Configuration module for Agentic RAG System """

import os
from dotenv import load_dotenv
from langchain.chat_models import init_chat_model

#Load Environment Variables
load_dotenv()

class Config:
    """ Configuration class for RAG System """

    #API Keys
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

    #Model Configuration
    LLM_MODEL = "openai:gpt-4o"

    #Document Processing
    CHUNK_SIZE = 500
    CHUNK_OVERLAP = 50

    #Default Urls
    DEFAULT_URLS = [
        "https://lilianweng.github.io/posts/2023-06-23-agent/",
        "https://lilianweng.github.io/posts/2024-04-12-diffusion-video/"
    ]


    @classmethod
    def get_llm(cls):
        """Initialize and return the LLM model"""
        os.environ["OPENAI_API_KEY"] = cls.OPENAI_API_KEY
        return init_chat_model(model=cls.LLM_MODEL)