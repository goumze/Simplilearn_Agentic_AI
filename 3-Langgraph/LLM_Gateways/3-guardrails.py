import re
import litellm
from litellm import completion
from dotenv import load_dotenv

load_dotenv()

#PII Patterns - simple, fast, no external dependencies

PII_PATTERNS = {
    "email": re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b"),
    "phone": re.compile(r"\b\d{3}[-.\s]??\d{3}[-.\s]??\d{4}\b"),
    "ssn": re.compile(r"\b\d{3}-\d{2}-\d{4}\b")
}

def redact_pii(text: str) -> str:
    """Redacts PII from the given text based on predefined patterns."""
    detected = []
    clean = text
    for label, pattern in PII_PATTERNS.items():
        matches = pattern.findall(clean)
        if matches:
            detected.extend(matches)
            clean = re.sub(pattern, f"<REDACTED_{label.upper()}>", clean)
    return clean, detected

def pii_input_guardrail(kwargs):
    """LiteLLM pre-call hook: scrub PII from user messages."""
    messages = kwargs.get("messages", [])
    for msg in messages:
      if msg.get("role") == "user":
          clean, detected = redact_pii(msg["content"])
          msg["content"] = clean

#Register the Guardrail
litellm.input_callback = [pii_input_guardrail]

if __name__ == "__main__":

    user_msg = (
        "Hi, I'm Goutam. My email is goutam@example.com. "
        "My phone number is 123-456-7890. "
        "My SSN is 123-45-6789"
    )

    response = completion(model="gpt-4o", messages=[{"role": "user", "content": user_msg}], max_tokens=80)

    print("\n LLM response:")
    print(response.choices[0].message.content)
