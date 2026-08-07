from typing_extensions import TypedDict
from langgraph.graph import StateGraph, START, END
#Reducers
from typing import Annotated
from langchain_core.messages import HumanMessage
from langgraph.graph.message import AnyMessage, add_messages
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langgraph.checkpoint.memory import MemorySaver
import asyncio

load_dotenv()

class State(TypedDict):
    messages: Annotated[list[AnyMessage], add_messages]


llm = ChatOpenAI(model_name="gpt-4o")
memory = MemorySaver()

#Node
def superbot(state: State):
    return {"messages":[llm.invoke(state["messages"])]}

#Async function for handling async streaming
async def async_streaming():
    config4 = {"configurable": {"thread_id":"4"}}
    print("\n=== Async Streaming response for thread_id 4 ===")
    async for chunk in graph_builder.astream_events({"messages":[HumanMessage(content="Hi My name is Goutam. I like Cricket.")]}, config=config4, version="v2"):
        print("chunk:", chunk)

#Workflow
graph=StateGraph(State)
graph.add_node("superbot", superbot)
graph.add_edge(START, "superbot")
graph.add_edge("superbot", END)
graph_builder = graph.compile(checkpointer=memory)

if __name__ == "__main__":
    #Specify the thread
    print("\n=== Non Streaming response for thread_id 1 ===")
    config = {"configurable": {"thread_id":"1"}}
    response = graph_builder.invoke({"messages":[HumanMessage(content="Hi My name is Goutam. I like Cricket.")]},config=config)
    print("response:", response)

    config2 = {"configurable": {"thread_id":"2"}}

    print("\n=== Streaming response for thread_id 2 ===")
    for chunk in graph_builder.stream({"messages":[HumanMessage(content="Hi My name is Goutam. I like Cricket.")]}, config=config2, stream_mode="updates"):
        print("chunk:", chunk)

    config3 = {"configurable": {"thread_id":"3"}}

    print("\n=== Streaming response for thread_id 3 ===")
    for chunk in graph_builder.stream({"messages":[HumanMessage(content="Hi My name is Goutam. I like Cricket.")]}, config=config3, stream_mode="values"):
        print("chunk:", chunk)

    # Run async streaming
    asyncio.run(async_streaming())