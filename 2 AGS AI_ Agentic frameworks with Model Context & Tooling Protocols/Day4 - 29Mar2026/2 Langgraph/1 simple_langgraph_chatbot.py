# Problem Statement
# Design and implement a basic conversational chatbot system using a graph-based architecture that leverages a local large language model for generating responses.
    
# The system should:
# - Accept user input in a continuous loop from the command line.
# - Maintain a conversation history (messages) between the user and the assistant.
# - Use a graph-based workflow (LangGraph) to process the conversation.
# - Pass the user’s message to a local LLM (via Ollama) to generate a response.
# - Append the generated response to the conversation state.
# - Display the assistant’s response to the user in real time.
# - Continue interaction until the user chooses to exit.

# Objective
# To demonstrate how a simple chatbot pipeline can be built using:
# - LangGraph for workflow orchestration
# - State management for conversation tracking
# - Ollama LLM for local response generation


# Install packages
# pip install --upgrade langchain langchain-community langgraph

# #### Provides access to the ollama models.
# pip install langchain-ollama

# #### To run this code- Open command prompt and type
# python 1.py

# pip install --upgrade langchain langchain-community langgraph

# pip install langchain-ollama

from typing import List, Dict
from langgraph.graph import StateGraph, START, END
from langchain_ollama.llms import OllamaLLM


# Step 1: Define State
class State(Dict):
    messages: List[Dict[str, str]] # eg: [{"role": "user", "content": "Hello!"}, {"role": "assistant", "content": "Hi there!"}]


# Step 2: Initialize StateGraph
graph_builder = StateGraph(State)

# Initialize the LLM
# llm = OllamaLLM(model="llama3.1")
llm = OllamaLLM(model="llama3.2")


# Define chatbot function
def chatbot(state: State):
    response = llm.invoke(state["messages"])
    state["messages"].append({"role": "assistant", "content": response})  # Treat response as a string
    return {"messages": state["messages"]}



# Add nodes and edges
graph_builder.add_node("chatbot", chatbot)
graph_builder.add_edge(START, "chatbot")
graph_builder.add_edge("chatbot", END)


# Compile the graph
graph = graph_builder.compile()


# Stream updates
def stream_graph_updates(user_input: str): # Hello  
    state = {"messages": [{"role": "user", "content": user_input}]}
    for event in graph.stream(state): # Run the LangGraph. It will yield updates to the state as the graph processes it.
        for value in event.values(): # Get the result inside the event. In this case, the value will be the updated state after processing the chatbot node.
            print("Assistant:", value["messages"][-1]["content"])



# Run chatbot in a loop
if __name__ == "__main__":
    while True:
        try:
            user_input = input("User: ")
            if user_input.lower() in ["quit", "exit", "q"]:
                print("Goodbye!")
                break

            stream_graph_updates(user_input)
        except Exception as e:
            print(f"An error occurred: {e}")
            break
