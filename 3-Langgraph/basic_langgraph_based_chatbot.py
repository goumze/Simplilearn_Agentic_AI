from typing_extensions import TypedDict
from langgraph.graph import StateGraph, START, END
import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
load_dotenv()
#Reducers
from typing import Annotated, List
from langgraph.graph.message import add_messages


class State(TypedDict):
    messages: Annotated[List[str], add_messages]

llm = ChatOpenAI(model_name="gpt-4o") 


#Create Nodes
def superBot(state: 'State') -> None:
    return {"messages": llm.invoke(state["messages"])}

graph = StateGraph(State)
graph.add_node("superBot", superBot)

#Add edges
graph.add_edge(START, "superBot")
graph.add_edge("superBot", END)

if __name__ == "__main__":
    #Invoke the graph
    initial_state: State = {"messages": ["Hi, My name is Goutam, and I like Cricket."]}
    graph_builder = graph.compile()
    result = graph_builder.invoke(initial_state)
    print(f"Final messages: {result['messages']}")
