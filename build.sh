#!/bin/bash
set -e

echo "=== Building Application ==="

# Install dependencies
echo "Installing Python dependencies..."
pip install -r requirements.txt

# Install Coral CLI locally inside the project directory
echo "Downloading and installing Coral CLI..."
mkdir -p bin
export CORAL_INSTALL_DIR=$(pwd)/bin
curl -fsSL https://withcoral.com/install.sh | sh

echo "=== Build Complete ==="
