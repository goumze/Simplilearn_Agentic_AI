from langchain_core.messages import AIMessage, HumanMessage
from pprint import pprint
import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
load_dotenv()

if __name__ == "__main__":
    messages=[AIMessage(content="Please tell me how can I help ?", name="LLModel")]
    messages.append(HumanMessage(content="I want to learn coding", name="Goutam"))
    messages.append(AIMessage(content=f"Which programming language you want to learn ?", name="LLModel"))

    for message in messages:
        message.pretty_print()

    llm = ChatOpenAI(model_name="gpt-4o")

    result = llm.invoke(messages)
    pprint(result.response_metadata)

