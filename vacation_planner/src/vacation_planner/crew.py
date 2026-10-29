from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from crewai_tools import SerperDevTool
from dotenv import load_dotenv
from pathlib import Path
import os
from crewai import LLM
from bedrock_agentcore.runtime import BedrockAgentCoreApp
import requests
from crewai.tools import tool

app = BedrockAgentCoreApp()

# Load AWS credentials and settings from the project .env before the LLM is created.
load_dotenv(Path(__file__).resolve().parents[2] / ".env", override=True)

#Initialize SerperDev Tool
serper_dev_tool=SerperDevTool(api_key=os.getenv("SERPER_API_KEY"))
llm=LLM(model=os.getenv("LLM_MODEL"),region=os.getenv("AWS_DEFAULT_REGION"),api_key=os.getenv("AWS_BEARER_TOKEN_BEDROCK"))
# If you want to run a snippet of code before or after the crew starts,
# you can use the @before_kickoff and @after_kickoff decorators
# https://docs.crewai.com/concepts/crews#example-crew-class-with-decorators

def fetch_access_token(client_id, client_secret, token_url):
    """Gets a JWT from Cognito using the OAuth client credentials grant"""
    response = requests.post(
        token_url,
        data={
            "grant_type": "client_credentials",
            "client_id": client_id,
            "client_secret": client_secret,
        },
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        timeout=30,
    )
    response.raise_for_status()
    return response.json()["access_token"]


def call_tool(gateway_url, access_token, tool_name, arguments):
    """Calls a tool on the AgentCore Gateway (MCP, JSON-RPC over HTTP)"""
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {access_token}",
    }
    payload = {
        "jsonrpc": "2.0",
        "id": "call-tool-request",
        "method": "tools/call",
        "params": {"name": tool_name, "arguments": arguments},
    }
    response = requests.post(gateway_url, headers=headers, json=payload, timeout=60)
    response.raise_for_status()
    return response.json()


# Gateway tool names are "<target name>___<tool name>"; the target name comes from Terraform.
GATEWAY_TOOL_NAME = os.getenv("GATEWAY_TOOL_NAME", "target-travel-agent-tool___get_travel_packages")


@tool("Get Travel Packages")
def get_travel_packages(city: str) -> str:
    """Fetches available travel packages (plan, cost, duration) for the given city from the AgentCore Gateway"""
    access_token = fetch_access_token(os.getenv("COGNITO_CLIENT_ID"), os.getenv("COGNITO_SECRET"), os.getenv("TOKEN_URL"))
    result = call_tool(os.getenv("GATEWAY_URL"), access_token, GATEWAY_TOOL_NAME, {"city": city})
    if "error" in result:
        return f"Error from gateway: {result['error']}"
    content = result.get("result", {}).get("content", [])
    return "\n".join(item.get("text", "") for item in content) or str(result)


@CrewBase
class VacationPlanner():
    """VacationPlanner crew"""

    # Learn more about YAML configuration files here:
    # Agents: https://docs.crewai.com/concepts/agents#yaml-configuration-recommended
    # Tasks: https://docs.crewai.com/concepts/tasks#yaml-configuration-recommended
    agents_config = 'config/agents.yaml'
    tasks_config = 'config/tasks.yaml'

    # If you would like to add tools to your agents, you can learn more about it here:
    # https://docs.crewai.com/concepts/agents#agent-tools
    @agent
    def vacation_researcher(self) -> Agent:
        return Agent(
            config=self.agents_config['vacation_researcher'],
            verbose=True,
            tools=[serper_dev_tool, get_travel_packages],
            llm=llm
        )

    @agent
    def itinerary_planner(self) -> Agent:
        return Agent(
            config=self.agents_config['itinerary_planner'],
            verbose=True,
            llm=llm
        )

    # To learn more about structured task outputs,
    # task dependencies, and task callbacks, check out the documentation:
    # https://docs.crewai.com/concepts/tasks#overview-of-a-task
    @task
    def research_task(self) -> Task:
        return Task(
            config=self.tasks_config['research_task'],
        )

    @task
    def reporting_task(self) -> Task:
        return Task(
            config=self.tasks_config['reporting_task'],
            output_file='report.md'
        )

    @crew
    def crew(self) -> Crew:
        """Creates the VacationPlanner crew"""
        # To learn how to add knowledge sources to your crew, check out the documentation:
        # https://docs.crewai.com/concepts/knowledge#what-is-knowledge

        return Crew(
            agents=self.agents, # Automatically created by the @agent decorator
            tasks=self.tasks, # Automatically created by the @task decorator
            process=Process.sequential,
            verbose=True,
            # process=Process.hierarchical, # In case you wanna use that instead https://docs.crewai.com/how-to/Hierarchical/
        )


@app.entrypoint
def agent_invocation(payload, context):
    """Handler for agent invocation"""
    print(f"Payload: {payload}", flush=True)
    try:
        user_input = payload.get("topic", "Bengaluru, India")
        print(f"Processing vacation destination: {user_input}", flush=True)

        result = VacationPlanner().crew().kickoff(inputs={"topic": user_input})
        print("Result Raw:\n************\n", result.raw, flush=True)

        return {"result": result.raw}
    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"Error during agent invocation: {e}", flush=True)
        return {"error": str(e)}


def test_local():
    """Test the crew locally without AgentCore"""
    try:
        result = VacationPlanner().crew().kickoff(inputs={"topic": "Plan a vacation to Bengaluru, India"})
        print("Result Raw:\n************\n", result.raw)
        return result
    except Exception as e:
        print(f"Error during local test: {e}")
        return None

if __name__ == "__main__":
    #Run AgentCore server - HTTP Server on port 8080
    app.run()

