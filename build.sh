#!/bin/bash
set -e

echo "=== Building Application ==="

# Install dependencies
echo "Installing Python dependencies..."
pip install -r requirements.txt

# Install Coral CLI locally
echo "Downloading and installing Coral CLI..."
curl -fsSL https://withcoral.com/install.sh | sh

echo "=== Build Complete ==="
