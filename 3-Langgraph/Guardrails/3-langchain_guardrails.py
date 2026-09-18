from dotenv import load_dotenv
load_dotenv()
from langchain.agents import create_agent
from langchain.agents.middleware import PIIMiddleware
from langchain_openai import ChatOpenAI
from langchain_core.tools import Tool, tool

@tool
def customer_lookup(query:str) -> str:
    """Look up customer information"""
    return f"Customer information for query: {query}"

#Create agent with PII Middleware
agent = create_agent(
    model="gpt-4o",
    tools=[customer_lookup],
    middleware=[
        PIIMiddleware(
            "email",
            strategy="redact",
            apply_to_input=True
        ),
        PIIMiddleware(
            "credit_card",
            strategy="mask",
            apply_to_input=True
        ),
        PIIMiddleware(
            "api_key",
            detector="sk-[a-zA-Z0-9]{32}",
            strategy="block",
            apply_to_input=True
        )
    ]
)

print("Agent with PII Middleware created successfully.")

if __name__ == "__main__":
    #Test PII Redaction
    result = agent.invoke({
        "messages":[{
        "role":"user",
        "content":"My email is test@example.com and my credit card number is 1234-5678-9012-3456."
        }]
    })

    print("===Agent Response===")
    print(result["messages"][-1].content)


