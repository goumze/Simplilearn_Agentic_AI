#!/usr/bin/env python
import sys
import warnings
import os
from pathlib import Path

from datetime import datetime
from dotenv import load_dotenv

from debater_app.crew import HealthcareAssistance

# Load .env from the project root (debater/) regardless of working directory
load_dotenv(dotenv_path=Path(__file__).parents[2] / ".env")

warnings.filterwarnings("ignore", category=SyntaxWarning, module="pysbd")

# This main file is intended to be a way for you to run your
# crew locally, so refrain from adding unnecessary logic into this file.
# Replace with inputs you want to test with, it will automatically
# interpolate any tasks and agents information

def run():
    """
    Run the crew.
    """
    inputs = {
        'user_request': (
            'Book a nephrologist appointment for my 70-year-old father '
            'who has been diagnosed with Chronic Kidney Disease (CKD).'
        ),
    }
    
    try:
        result = HealthcareAssistance().crew().kickoff(inputs=inputs)
        print(result.raw)
    except Exception as e:
        raise Exception(f"An error occurred while running the crew: {e}")
