from dotenv import load_dotenv
load_dotenv()

import os
import re


# Illustration of two approaches Deterministic and Model approach

def deterministic_guardrail(text:str) -> bool:
    """Returns True if content is blocked"""
    banned_keywords = ["hack","exploit","malware", "bomb"]
    return any(keyword in text.lower() for keyword in banned_keywords)

test_inputs = [
    "How do I hack into a database ?",
    "What is the capital of India ?",
    "Explain how malware spreads"
]

print("=== Deterministic Guardrail Demo ===")
for inp in test_inputs:
    blocked = deterministic_guardrail(inp)
    status = "Blocked" if blocked else "Allowed"
    print(f"{status}: {inp}")

if __name__ == "__main__":
    print("=== Deterministic Guardrail Demo ===")
    for inp in test_inputs:
        blocked = deterministic_guardrail(inp)
        status = "Blocked" if blocked else "Allowed"
        print(f"{status}: {inp}")
