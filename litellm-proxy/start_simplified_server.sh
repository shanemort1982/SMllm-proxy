#!/bin/bash

echo "Starting OpenHands LiteLLM Proxy (Simplified)..."

# Set environment variables (replace these with your actual API keys in production)
export OPENAI_API_KEY=""
export ANTHROPIC_API_KEY=""
export GEMINI_API_KEY=""
export PORT="54658"

# Create necessary directories
mkdir -p /workspace/litellm-proxy/logs
mkdir -p /workspace/litellm-proxy/keys
mkdir -p /workspace/litellm-proxy/static
mkdir -p /workspace/litellm-proxy/templates

# Start the server
python /workspace/litellm-proxy/simplified_server.py

echo "Server stopped by user"