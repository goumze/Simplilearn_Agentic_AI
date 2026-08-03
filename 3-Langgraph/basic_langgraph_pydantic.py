from langgraph.graph import StateGraph, START, END
from pydantic import BaseModel

class State(BaseModel):
    name: str
    
##Node function
def example_node(state: State):
    print("--Example node has been activated--")
    return {"name": "Hello"}

builder = StateGraph(State)
builder.add_node("example_node", example_node)
builder.add_edge(START, "example_node")
builder.add_edge("example_node", END)

graph = builder.compile()

if __name__ == "__main__":
    #Invoke the graph
    result = graph.invoke({"name": "Goutam"})
    print(f"Final response: {result['name']}")


    

