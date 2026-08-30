# Use an official lightweight Python image
FROM python:3.12-slim-bookworm

# Install security updates
RUN apt-get update && apt-get upgrade -y && apt-get autoremove -y && apt-get clean && rm -rf /var/lib/apt/lists/*

# Install uv using pip
RUN pip install --upgrade pip && pip install uvicorn uv

# Set the working directory inside the container
WORKDIR /app

# Copy the requirements file first to leverage Docker layer caching
COPY requirements.txt .
RUN uv pip install --system --no-cache -r requirements.txt

# Copy the entire backend source code to the working directory
COPY . .

# Create non-root user for security
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# Expose port 8000 so the app can be accessed from outside the container
EXPOSE 8000

# We bind to 0.0.0.0 to allow external connections
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]