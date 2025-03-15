# OpenHands LiteLLM Proxy

A centralized LiteLLM proxy server with web UI for OpenHands instances across a LAN. This setup provides a unified API for accessing different LLM providers through a single endpoint.

![OpenHands LiteLLM Proxy](https://i.imgur.com/placeholder.png)

## Quick Start

1. Install dependencies:
   ```bash
   ./install_dependencies.sh
   ```

2. Start the server:
   ```bash
   ./start_custom_server.sh
   ```

3. Access the web UI:
   ```
   http://localhost:54658
   ```

4. Configure your API keys through the web UI:
   - Go to the "Configuration" tab
   - Enter your OpenAI and/or Anthropic API keys
   - Click "Save Configuration"

5. Create API keys for your OpenHands instances:
   - Go to the "API Keys" tab
   - Fill in the form and click "Create API Key"

6. Configure OpenHands instances to use the proxy:
   ```bash
   export OPENAI_API_KEY="sk-openhands-instance-1-abc123def456"
   export OPENAI_API_BASE="http://<your-server-ip>:54658"
   export OPENAI_API_TYPE="openai"
   ```

## Web UI Features

- **Dashboard**: View server status and test connections to LLM providers
- **Configuration**: Set up API keys for OpenAI and Anthropic
- **API Keys**: Create and manage API keys for OpenHands instances
- **Logs**: View server logs and monitor activity

## Documentation

- For deployment on a dedicated server, see [DEPLOYMENT.md](DEPLOYMENT.md)

## Key Features

- **Web UI for Management**: Easy-to-use interface for configuration and monitoring
- **Centralized API Key Management**: Store and manage all your API keys in one place
- **Model Routing**: Route requests to the appropriate provider (OpenAI, Anthropic)
- **Unified API**: All OpenHands instances use the same API format (OpenAI-compatible)
- **LAN-wide Access**: Make the proxy available to all machines on your network
- **Logging and Monitoring**: Track usage and troubleshoot issues

## Directory Structure

- `litellm_server.py`: FastAPI server implementation with web UI
- `start_custom_server.sh`: Script to start the server
- `stop_custom_server.sh`: Script to stop the server
- `install_dependencies.sh`: Script to install dependencies
- `logs/`: Directory for server logs
- `keys/`: Directory for API key storage
- `static/`: Directory for web UI static files
- `templates/`: Directory for web UI templates

## Security Considerations

- Use secure API keys for each OpenHands instance
- Consider setting up HTTPS for production use
- Restrict access to the proxy server using firewall rules
- Set appropriate rate limits for each instance

## Troubleshooting

If you encounter issues:

1. Check the server logs in the "Logs" tab of the web UI
2. Verify that your API keys are correct in the "Configuration" tab
3. Test connections in the "Dashboard" tab
4. Ensure the server is accessible from your OpenHands instances