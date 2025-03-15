#!/bin/bash

echo "Installing OpenHands LiteLLM Proxy dependencies..."

# Install Python dependencies
pip install litellm fastapi uvicorn requests jinja2 python-multipart

# Create necessary directories
mkdir -p /workspace/litellm-proxy/logs
mkdir -p /workspace/litellm-proxy/keys
mkdir -p /workspace/litellm-proxy/static
mkdir -p /workspace/litellm-proxy/templates

# Make scripts executable
chmod +x /workspace/litellm-proxy/*.sh
chmod +x /workspace/litellm-proxy/*.py

echo "✅ Dependencies installed successfully."
echo "Next steps:"
echo "1. Start the server with ./start_custom_server.sh"
echo "2. Access the web UI at http://localhost:54658"
echo "3. Configure your API keys through the web UI"