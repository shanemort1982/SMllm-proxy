# OpenHands LiteLLM Proxy

A centralized LiteLLM proxy server for OpenHands instances across a LAN. This setup provides a unified API for accessing different LLM providers through a single endpoint.

## Overview

The OpenHands LiteLLM proxy acts as a central gateway for all OpenHands instances on your LAN to access various LLM APIs. This setup provides several benefits:

1. **Centralized API Key Management**: Store and manage all your API keys in one place
2. **Model Routing**: Route requests to the appropriate provider (OpenAI, Anthropic, Azure, etc.)
3. **Unified API**: All OpenHands instances use the same API format (OpenAI-compatible)
4. **LAN-wide Access**: Make the proxy available to all machines on your network

## Quick Start

1. Install dependencies:
   ```bash
   ./install_dependencies.sh
   ```

2. Configure API keys in `start_custom_server.sh` or directly in `litellm_server.py`

3. Generate API keys for your OpenHands instances:
   ```bash
   ./create_api_key.sh openhands-instance-1
   ```

4. Start the server:
   ```bash
   ./start_custom_server.sh
   ```

5. Test the server:
   ```bash
   ./custom_test_client.py sk-openhands-instance-1
   ```

## Detailed Setup Instructions

### 1. Install Dependencies

Run the installation script to install all required dependencies:

```bash
./install_dependencies.sh
```

### 2. Configure Provider API Keys

Edit the `start_custom_server.sh` script to set your actual API keys:

```bash
export AZURE_API_BASE="your-azure-api-base"
export AZURE_API_KEY="your-azure-api-key"
export ANTHROPIC_API_KEY="your-anthropic-api-key"
```

Alternatively, you can edit the `MODEL_CONFIG` dictionary in `litellm_server.py` directly.

### 3. Generate API Keys for OpenHands Instances

Create API keys for each OpenHands instance:

```bash
./create_api_key.sh openhands-instance-1
./create_api_key.sh openhands-instance-2
```

This will generate API keys and provide instructions for adding them to the `API_KEYS` dictionary in `litellm_server.py`:

```python
API_KEYS = {
    "sk-openhands-instance-1-abc123def456": "openhands-instance-1",
    "sk-openhands-instance-2-789012ghijkl": "openhands-instance-2",
}
```

### 4. Start the Proxy Server

```bash
./start_custom_server.sh
```

The server will be available at `http://<your-server-ip>:54658`.

### 5. Configure OpenHands Instances

On each OpenHands instance, set the following environment variables:

```bash
export OPENAI_API_KEY="sk-openhands-instance-1-abc123def456"  # Use the appropriate key for each instance
export OPENAI_API_BASE="http://<your-server-ip>:54658"
export OPENAI_API_TYPE="openai"
```

## Managing the Proxy

### List API Keys

To list all generated API keys:

```bash
./list_api_keys.sh
```

### Check Server Status

To check if the server is running and view available models:

```bash
curl http://localhost:54658/health
curl http://localhost:54658/v1/models
```

### Test the Proxy

To test if the proxy is working correctly:

```bash
./custom_test_client.py sk-openhands-instance-1-abc123def456
```

You can also specify a different model and message:

```bash
./custom_test_client.py sk-openhands-instance-1-abc123def456 gpt-4 "What is the capital of France?"
```

### Stop the Proxy

To stop the running proxy server:

```bash
./stop_custom_server.sh
```

## Available Models

The following models are configured by default:

- `gpt-3.5-turbo` (Azure)
- `gpt-4` (Azure)
- `claude-3-opus` (Anthropic)

You can add more models by updating the `MODEL_CONFIG` dictionary in `litellm_server.py`.

## Logs and Monitoring

Server logs are stored in:
```
/workspace/litellm-proxy/logs/server.log
```

API keys are stored in:
```
/workspace/litellm-proxy/keys/api_keys.csv
```

## Security Considerations

- Use secure API keys for each OpenHands instance
- Consider setting up HTTPS for production use
- Restrict access to the proxy server using firewall rules
- Set appropriate rate limits for each instance

## Troubleshooting

If you encounter issues:

1. Check the server logs for error messages
2. Verify that your API keys are correct
3. Ensure the server is accessible from your OpenHands instances
4. Check that the models are configured correctly

## Advanced Configuration

For more advanced configuration options, refer to the LiteLLM documentation:
https://docs.litellm.ai/docs/

You can customize the proxy server by modifying the `litellm_server.py` file to add features like:

- Rate limiting
- Request logging
- Cost tracking
- Custom model routing logic