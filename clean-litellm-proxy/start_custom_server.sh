#!/bin/bash

# Set environment variables (replace these with your actual API keys in production)
export AZURE_API_BASE="your-azure-api-base"
export AZURE_API_KEY="your-azure-api-key"
export ANTHROPIC_API_KEY="your-anthropic-api-key"
export PORT="54658"

# Create necessary directories
mkdir -p /workspace/litellm-proxy/logs
mkdir -p /workspace/litellm-proxy/keys
mkdir -p /workspace/litellm-proxy/static
mkdir -p /workspace/litellm-proxy/templates

# Start the custom LiteLLM server
cd /workspace/litellm-proxy
echo "Starting OpenHands LiteLLM Proxy..."
echo "Web UI will be available at http://localhost:$PORT"
echo "API endpoint will be available at http://localhost:$PORT/v1"
echo "Log file: /workspace/litellm-proxy/logs/server.log"

# Run the server
python litellm_server.py