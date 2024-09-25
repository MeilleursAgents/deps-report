#!/bin/sh -l

echo "Starting deps-report action..."

# Change to the GitHub workspace directory
cd /github/workspace || exit 1

# Display the current working directory
echo "Current directory: $(pwd)"

# List the files in the current directory (for debugging)
echo "Contents of current directory:"
ls -la

# Run deps-report with the provided arguments
deps-report "$@"
