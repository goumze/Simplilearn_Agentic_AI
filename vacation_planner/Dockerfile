FROM ghcr.io/astral-sh/uv:python3.11-bookworm-slim

WORKDIR /app

#Copy only the runtime dependencies (AgentCore limits image size; keep it small)
COPY requirements-agent.txt .

#Install build tools, install dependencies, then remove the build tools in the same layer
RUN apt-get update && apt-get install -y --no-install-recommends build-essential \
    && uv pip install --system --no-cache -r requirements-agent.txt \
    && apt-get purge -y --auto-remove build-essential \
    && rm -rf /var/lib/apt/lists/* /root/.cache

RUN pip install --no-cache-dir "aws-opentelemetry-distro>=0.10.1" boto3

#Copy app source code and pyproject.toml
COPY src/ ./src/
COPY pyproject.toml .
#crew.py loads /app/.env at startup (CI writes it from a secret before the build)
COPY .env .

#Open Telemetry Configuration for AgentCore Observability
ENV OTEL_SERVICE_NAME=vacation_planner_agent
ENV OTEL_TRACES_EXPORTER=otlp
ENV OTEL_METRICS_EXPORTER=otlp

#AWS OpenTelemetry Distribution
ENV OTEL_PYTHON_DISTRO=aws_distro
ENV OTEL_PYTHON_CONFIGURATOR=aws_configurator

#Export Protocol
ENV OTEL_EXPORTER_OTLP_PROTOCOL=http/protobuf
ENV OTEL_TRACES_EXPORTER=otlp

#Enable AgentCore Observability
ENV AGENT_OBSERVABILITY_ENABLED=true

#Service Identification
ENV OTEL_TRACES_SAMPLER=always-on
ENV OTEL_RESOURCE_ATTRIBUTES=service.namespace=AgentCore,service.version=1.0

#Expose port
EXPOSE 8080

#Startup command - Runs the app with OpenTelemetry auto-instrumentation so traces reach CloudWatch
CMD ["opentelemetry-instrument","python","src/vacation_planner/crew.py"]