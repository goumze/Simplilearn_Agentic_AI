from langchain.agents import create_agent
from langchain.agents.middleware import HumanInTheLoopMiddleware
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.types import Command
from langchain_core.tools import tool
from dotenv import load_dotenv
load_dotenv()

@tool
def search_web(query: str) -> str:
    """Search the web for information"""
    return f"Search results for query: {query}"

@tool
def send_email(to: str, subject: str, body: str) -> str:
    """Send an email to a recipient"""
    return f"Email sent to {to} with subject '{subject}' and body '{body}'"

@tool
def delete_records(table:str,condition:str) -> str:
    """Delete records from a table based on a condition"""
    return f"Records deleted from table '{table}' where {condition}"

#Create agent with Human In The Loop Middleware
hitl_agent = create_agent(
    model="gpt-4o",
    tools=[search_web, send_email, delete_records],
    middleware=[
        HumanInTheLoopMiddleware ({
            "interrupt_on": True,
            "delete_records": True,
            "search_web": False
            }
        ),
    ],
    checkpointer=InMemorySaver() #Required for State persistence
)

print("Human in the loop agent created successfully.")

#Step 1: Invoke - Agent will pause before send email
config = {"configurable":{"thread_id":"session_001"}}

if __name__ == "__main__":

    #Step 1: Invoke - agent will pause before send email
    result = hitl_agent.invoke(
        {"messages":[{"role":"user","content":"Send an email to team@company.com about the Q4 results"}]},
        config=config
    )

    print("=== Agent paused - awaiting human approval ===")
    print("Result so far:", result)

    #Step 2: Human approves - agent continues
    approved_result = hitl_agent.invoke(
        Command(resume={"decisions":[{"type":"approve"}]}),
        config=config
    )
    print("===Approved! Final response===")
    print(approved_result["messages"][-1].content)

    #Step 3: Alternatives - Human Rejects
    config2 = {"configurable":{"thread_id":"session_002"}}

    hitl_agent.invoke(
        {"messages":[{"role":"user","content":"Send an email to team@company.com about the Q4 results"}]},
        config=config2
    )

    rejected_result = hitl_agent.invoke(
        Command(resume={"decisions":[{"type":"reject"}]}),
        config=config2
    )
    print("===Rejected! Final response===")
    print(rejected_result["messages"][-1].content)

    
