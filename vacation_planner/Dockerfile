FROM ghcr.io/astral-sh/uv:python3.11-bookworm-slim

WORKDIR /app

#Copy only the runtime dependencies (AgentCore limits image size; keep it small)
COPY requirements-agent.txt .

#Install build tools, install dependencies, then remove the build tools in the same layer
RUN apt-get update && apt-get install -y --no-install-recommends build-essential \
    && uv pip install --system --no-cache -r requirements-agent.txt \
    && apt-get purge -y --auto-remove build-essential \
    && rm -rf /var/lib/apt/lists/* /root/.cache

#Copy app source code and pyproject.toml
COPY src/ ./src/
COPY pyproject.toml .

#Expose port
EXPOSE 8080

#Startup command - Runs the app with OpenTelemetry auto-instrumentation so traces reach CloudWatch
CMD ["opentelemetry-instrument","python","src/vacation_planner/crew.py"]