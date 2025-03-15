#!/usr/bin/env python3
"""
Test client for OpenHands LiteLLM proxy server.
Usage: python custom_test_client.py [api_key] [model] [message]
Example: python custom_test_client.py sk-openhands-instance-1 gpt-3.5-turbo "What is the capital of France?"
"""

import requests
import json
import sys
import argparse
from typing import Dict, List, Optional

def test_litellm_proxy(
    api_key: Optional[str] = None,
    model: str = "gpt-3.5-turbo",
    message: str = "Hello, how are you today?",
    host: str = "localhost",
    port: int = 54658
) -> None:
    """Test the LiteLLM proxy server with a simple request."""
    
    # API endpoint
    url = f"http://{host}:{port}/v1/chat/completions"
    
    # Request headers
    headers = {"Content-Type": "application/json"}
    
    # Add Authorization header if API key is provided
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"
    
    # Request data
    data = {
        "model": model,
        "messages": [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": message}
        ],
        "temperature": 0.7,
        "max_tokens": 100
    }
    
    print(f"\n🔍 Testing OpenHands LiteLLM Proxy")
    print(f"URL: {url}")
    print(f"Model: {model}")
    print(f"API Key: {api_key if api_key else 'None (anonymous)'}")
    print(f"Message: '{message}'")
    print("\nSending request...")
    
    # Make the request
    try:
        response = requests.post(url, headers=headers, json=data)
        
        # Check if the request was successful
        if response.status_code == 200:
            result = response.json()
            print("\n✅ Success! Response from LiteLLM server:")
            if "choices" in result and len(result["choices"]) > 0:
                print(f"\n{result['choices'][0]['message']['content']}")
            else:
                print(json.dumps(result, indent=2))
            print("\nThe LiteLLM proxy is working correctly.")
        else:
            print(f"\n❌ Error: {response.status_code}")
            print(response.text)
            
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("\nTroubleshooting tips:")
        print("1. Make sure the LiteLLM server is running")
        print("2. Verify the URL is correct")
        print("3. Check the server logs for more information")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Test the OpenHands LiteLLM proxy server")
    parser.add_argument("api_key", nargs="?", default=None, help="API key for authentication")
    parser.add_argument("model", nargs="?", default="gpt-3.5-turbo", help="Model to use for the test")
    parser.add_argument("message", nargs="?", default="Hello, how are you today?", help="Message to send to the model")
    parser.add_argument("--host", default="localhost", help="Host where the proxy is running")
    parser.add_argument("--port", type=int, default=54658, help="Port where the proxy is running")
    
    args = parser.parse_args()
    
    test_litellm_proxy(
        api_key=args.api_key,
        model=args.model,
        message=args.message,
        host=args.host,
        port=args.port
    )