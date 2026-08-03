from langgraph.prebuilt import ToolNode
from langgraph.prebuilt import tool_condition
from langgraph.graph import END, START, StateGraph
from langchain_core.messages import HumanMessage
builder = StateGraph(START)

#Add Nodes
builder.add_node("llm_tool",llm_tool)
builder.add_node("tools",ToolNode(tools))
builder.add_edge(START,"llm_tool")
builder.add_conditional_edges("llm_tool",tool_condition)
builder.add_edge("tools",END)

graph_builder = builder.compile()


#Invocation
messages = graph_builder.invoke({"messages":[HumanMessage(content="What is 2 plus 2", name="Goutam")]})

