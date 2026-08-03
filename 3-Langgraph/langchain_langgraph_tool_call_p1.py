from dotenv import load_dotenv
from typing import Annotated, List, Any as AnyMessage
from langchain_openai import ChatOpenAI
from langchain_core.messages import AIMessage, HumanMessage
from typing_extensions import TypedDict
from langgraph.graph.message import add_messages
from IPython.display import Image,display
from langgraph.graph import StateGraph, START, END
load_dotenv()

def add(a:int,b:int)->int:
    """
    Adds two integers.

    Args:
        a (int): The first integer.
        b (int): The second integer.

    Returns:
        int: The sum of the two integers.
    """
    return a+b

llm = ChatOpenAI(model_name="gpt-4o")
llm_with_tools = llm.bind_tools([add])


class State(TypedDict):
    messages: Annotated[List[AnyMessage],add_messages]
    name: str

initial_messages = [AIMessage(content=f"Please tell me how can I help", name="LLModel")]
initial_messages.append(HumanMessage(content=f"I want to learn coding", name="Krish"))

initial_messages
ai_message = AIMessage(content=f"Which programming language do you want to learn?", name="LLModel")
add_messages(initial_messages, ai_message)

def llm_tool(state:State):
    return {"messages":[llm_with_tools.invoke(state["messages"])]}

builder = StateGraph(State)
builder.add_node("llm_tool",llm_tool)
builder.add_edge(START,"llm_tool")
builder.add_edge("llm_tool",END)
graph = builder.compile()


if __name__ == "__main__":
    tool_call = llm_with_tools.invoke([HumanMessage(content="What is 2 plus 2", name="Goutam")])
    print("Tool call:", tool_call.tool_calls)

    #Invocation
    result = graph.invoke({"messages": [HumanMessage(content="What is 2 plus 2", name="Goutam")]})

    for message in result["messages"]:
        message.pretty_print()


