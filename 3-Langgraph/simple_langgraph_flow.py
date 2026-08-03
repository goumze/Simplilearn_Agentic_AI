from typing_extensions import TypedDict
import random
from typing import Literal
from IPython.display import display, Markdown
from langgraph.graph import StateGraph, START, END


class State(TypedDict):
    graph_info: str

def start_play(state: 'State') -> None:
    #print(f"Starting play node with graph info: {state['graph_info']}")
    return {"graph_info": state["graph_info"] + "I am planning to play"}

def cricket(state: 'State') -> None:
    #print(f"Starting cricket node with graph info: {state['graph_info']}")
    return {"graph_info": state["graph_info"] + " cricket"}

def badminton(state: 'State') -> None:
    #print(f"Starting badminton node with graph info: {state['graph_info']}")
    return {"graph_info": state["graph_info"] + " badminton"}

def random_play(state:State)-> Literal["cricket", "badminton"]:
    #print(f"Starting random_play node with graph info: {state['graph_info']}")
    if random.random() > 0.5:
        return "cricket"
    else:
        return "badminton"

#Building the state graph
state_graph = StateGraph(State)
state_graph.add_node("start_play", start_play)
state_graph.add_node("cricket", cricket)
state_graph.add_node("badminton", badminton)

state_graph.add_edge(START, "start_play")
state_graph.add_conditional_edges("start_play", random_play)
state_graph.add_edge("cricket", END)
state_graph.add_edge("badminton", END)        

#Compile the graph
graph_builder = state_graph.compile()


if __name__ == "__main__":
    #Invoke the graph
    initial_state: State = {"graph_info": "My name is Goutam. "}
    result = graph_builder.invoke(initial_state)
    print(f"Final graph info: {result['graph_info']}")
    #View the graph
    display(Markdown(f"```mermaid\n{graph_builder.get_graph().draw_mermaid()}\n```"))


    