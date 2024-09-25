FROM python:3.11-slim

# Install build tools if needed
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Set the working directory to /app
WORKDIR /app

# Copy the action's code into /app
COPY . /app

# Install poetry
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir poetry

# Install deps-report from the local source
RUN poetry config virtualenvs.create false \
    && poetry install --no-dev

# Copy the entry point script into the Docker image
COPY entrypoint.sh /entrypoint.sh

# Make the entry point script executable
RUN chmod +x /entrypoint.sh

# Set the entry point to the script
ENTRYPOINT ["/entrypoint.sh"]

# Default command (optional)
CMD ["--help"]
