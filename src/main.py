"""
CLI entry point for Banking Customer Support AI Agent.
Demonstrates the multi-agent workflow with sample use cases.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

import logging
from dotenv import load_dotenv

load_dotenv()

from database import init_db
from workflow import run_support_agent

logging.basicConfig(level=logging.WARNING)


def print_result(user_message: str, customer_name: str, result: dict) -> None:
    print("\n" + "-" * 60)
    print(f"User     : {user_message}")
    print(f"Customer : {customer_name}")
    print(f"Category : {result['classification'].replace('_', ' ').title()}")
    print(f"Agent    : {result['agent_used']}")
    if result.get("ticket_id"):
        print(f"Ticket   : #{result['ticket_id']}")
    print(f"Response : {result['response']}")


def main() -> None:
    init_db()

    demo_cases = [
        ("Thanks for sorting out my net banking login issue.", "Alice Johnson"),
        ("My debit card replacement still hasn't arrived.", "Bob Smith"),
        ("Could you check the status of ticket 650932?", "Carol White"),
        ("Your app is fantastic, saved me so much time!", "David Lee"),
        ("I was double-charged on my credit card. Very frustrated.", "Eve Davis"),
    ]

    print("=" * 60)
    print(" Banking Customer Support AI Agent — Demo")
    print("=" * 60)

    if not os.getenv("OPENAI_API_KEY") or os.getenv("OPENAI_API_KEY") == "your-openai-api-key-here":
        print("\nERROR: OPENAI_API_KEY is not set.")
        print("Please edit the .env file and add your OpenAI API key.")
        sys.exit(1)

    for message, name in demo_cases:
        result = run_support_agent(message, name)
        print_result(message, name, result)

    print("\n" + "=" * 60)
    print(" Demo complete. Run 'streamlit run src/app.py' for the UI.")
    print("=" * 60)


if __name__ == "__main__":
    main()
