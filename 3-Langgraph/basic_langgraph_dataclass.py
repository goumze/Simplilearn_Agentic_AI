from typing_extensions import TypedDict
from typing import Literal
import random
#from IPython import Image, display
from langgraph.graph import StateGraph, START, END
from dataclasses import dataclass

#from asyncio import graph

class TypedDictState(TypedDict):
    name:str
    game: Literal["Cricket", "Football", "Basketball", "Badminton"]

#State using Dataclass
@dataclass
class DataclassState:
    name: str
    game: Literal["Cricket", "Football", "Basketball", "Badminton"]

def play_game(state: TypedDictState | DataclassState):
    print("--Play game node has been activated--")
    if isinstance(state, DataclassState):
        return {"name": state.name + " want to play"}
    else:
        return {"name": state["name"] + " want to play"}

def cricket(state: TypedDictState | DataclassState):
    print("--Cricket node has been activated--")
    return {"game":"Cricket"}

def badminton(state: TypedDictState | DataclassState):
    print("--Badminton node has been activated--")
    return {"game":"Badminton"}

def route_to_game(state: TypedDictState | DataclassState) -> Literal["cricket", "badminton"]:
    """Route to game node based on state's game field."""
    game = state.game if isinstance(state, DataclassState) else state["game"]
    if game == "Cricket":
        return "cricket"
    else:
        return "badminton"

#Flow of the graph

builder = StateGraph(TypedDictState)
builder.add_node("playgame", play_game)
builder.add_node("cricket", cricket)
builder.add_node("badminton", badminton)

builder.add_conditional_edges("playgame", route_to_game)
builder.add_edge(START, "playgame")
builder.add_edge("cricket", END)
builder.add_edge("badminton", END)

graph = builder.compile()

if __name__ == "__main__":
    #This graph invokes using TypedDictState
    #print(f"Final response using TypedDictState: {graph.invoke({'name':'Goutam', 'game': 'Cricket'})}")
    #This graph invokes using DataclassState
    print(f"Final response using DataclassState: {graph.invoke(DataclassState(name='Goutam', game='Badminton'))}")

