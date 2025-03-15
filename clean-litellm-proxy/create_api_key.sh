#!/bin/bash

# Check if a key name was provided
if [ -z "$1" ]; then
  echo "Usage: $0 <instance_name>"
  echo "Example: $0 openhands-instance-3"
  exit 1
fi

INSTANCE_NAME="$1"
API_KEY="sk-$INSTANCE_NAME-$(openssl rand -hex 8)"

echo "Generated API key for $INSTANCE_NAME:"
echo "$API_KEY"
echo ""
echo "To use this key with OpenHands, set the following environment variables:"
echo "export OPENAI_API_KEY=\"$API_KEY\""
echo "export OPENAI_API_BASE=\"http://<your-server-ip>:54658\""
echo "export OPENAI_API_TYPE=\"openai\""
echo ""
echo "Add this key to the API_KEYS dictionary in litellm_server.py:"
echo "\"$API_KEY\": \"$INSTANCE_NAME\","

# Create keys directory if it doesn't exist
mkdir -p /workspace/litellm-proxy/keys

# Save the key to a file
echo "$API_KEY,$INSTANCE_NAME,$(date)" >> /workspace/litellm-proxy/keys/api_keys.csv
echo "Key saved to /workspace/litellm-proxy/keys/api_keys.csv"