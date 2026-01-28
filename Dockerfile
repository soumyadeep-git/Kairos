FROM python:3.11-slim-bookworm

# Install system dependencies for audio handling and SSL
RUN apt-get update && apt-get install -y \
    build-essential \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy dependency definition from the agent folder
COPY agent/requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the agent code from the agent folder
COPY agent/ .

# Command to run the agent
CMD ["python", "main.py", "start"]
