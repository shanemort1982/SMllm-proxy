#!/bin/bash

# Find the PID of the simplified server
PID=$(ps aux | grep "python /workspace/litellm-proxy/simplified_server.py" | grep -v grep | awk '{print $2}')

if [ -n "$PID" ]; then
    echo "Stopping OpenHands LiteLLM Proxy (Simplified) (PID: $PID)..."
    kill -15 $PID
    sleep 2
    
    # Check if the process is still running
    if ps -p $PID > /dev/null; then
        echo "Process still running, forcing termination..."
        kill -9 $PID
    fi
    
    echo "OpenHands LiteLLM Proxy (Simplified) stopped successfully."
else
    echo "OpenHands LiteLLM Proxy (Simplified) is not running."
fi