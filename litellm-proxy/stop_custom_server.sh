#!/bin/bash

# Find the process ID of the custom LiteLLM server
PID=$(ps aux | grep "python litellm_server.py" | grep -v grep | awk '{print $2}')

if [ -z "$PID" ]; then
  echo "OpenHands LiteLLM Proxy is not running."
else
  echo "Stopping OpenHands LiteLLM Proxy (PID: $PID)..."
  kill $PID
  echo "OpenHands LiteLLM Proxy stopped successfully."
  
  # Append stop time to log
  echo "$(date): Server stopped by user" >> /workspace/litellm-proxy/logs/server.log
  
  # Wait for the process to terminate
  sleep 2
  
  # Check if the process is still running
  if ps -p $PID > /dev/null; then
    echo "Process is still running. Sending SIGKILL..."
    kill -9 $PID
    echo "Process terminated."
  fi
fi