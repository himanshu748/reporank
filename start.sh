#!/bin/bash
set -e

echo "=== Starting Application ==="

# Prepend Coral bin to PATH
export PATH=$PATH:$(pwd)/bin

# Print version to confirm installation
echo "Coral CLI Version:"
coral --version

# Add the sources to Coral (forces registration on startup)
echo "Registering Coral Data Sources..."
coral source add github || true
coral source add --file sources/pypi.yaml || true
coral source add --file sources/npm.yaml || true
coral source add --file sources/hackernews.yaml || true
coral source add --file sources/opencollective.yaml || true

# Start FastAPI
echo "Starting FastAPI Server..."
python main.py
