from langchain_openai import ChatOpenAI
from dotenv import load_dotenv
load_dotenv()

# --- Model Based Guardrail --#

def model_based_guardrail(text: str) -> str:
    """ Uses an LLM to evaluate content safety. Return SAFE or UNSAFE."""
    model = ChatOpenAI(model="gpt-4o",temperature=0)
    prompt = f"""Is the following user input safe to process ? Reply with 'SAFE' or 'UNSAFE'.
    
    Input: "{text}"
    """
    result = model.invoke([{"role": "user", "content": prompt}])
    return result.content.strip()

if __name__ == "__main__":
    test_inputs = [
        "How do I hack into a database ?",
        "What is the capital of India ?",
        "Explain how malware spreads"
    ]

    print("=== Model Based Guardrail Demo ===")
    for inp in test_inputs:
        status = model_based_guardrail(inp)
        print(f"{status}: {inp}")
