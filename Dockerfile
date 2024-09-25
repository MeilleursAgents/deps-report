FROM python:3.11-slim

# Install build tools if needed (e.g., for dependencies that require compilation)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Set the working directory to /app
WORKDIR /app

# Copy the action's code into the Docker image
COPY . /app

# Install poetry
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir poetry

# Install deps-report from the local source code
RUN poetry config virtualenvs.create false \
    && poetry install --no-dev

# Set the working directory to the GitHub workspace where the user's code is checked out
WORKDIR /github/workspace

# Set the entrypoint to run deps-report
ENTRYPOINT ["deps-report"]

# (Optional) Set the default command to display help if no arguments are provided
CMD ["--help"]
