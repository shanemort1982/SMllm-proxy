#!/bin/bash

# Check if the API keys file exists
if [ ! -f "/workspace/litellm-proxy/keys/api_keys.csv" ]; then
  echo "No API keys found. Use create_api_key.sh to generate keys."
  exit 0
fi

echo "Available API keys:"
echo "-------------------"
echo "API Key,Instance Name,Creation Date"
cat /workspace/litellm-proxy/keys/api_keys.csv