# Deploying OpenHands LiteLLM Proxy on a Dedicated Server

This guide provides instructions for deploying the OpenHands LiteLLM Proxy on a dedicated server for production use.

## Server Requirements

- Ubuntu 20.04 LTS or newer
- Python 3.9+ installed
- Sufficient RAM (at least 2GB)
- Open port for the proxy (default: 54658)

## Step 1: Install Required Packages

```bash
# Update package lists
sudo apt update

# Install Python and pip if not already installed
sudo apt install -y python3 python3-pip python3-venv

# Install other dependencies
sudo apt install -y git curl
```

## Step 2: Clone the Repository

```bash
# Create a directory for the proxy
mkdir -p /opt/openhands-litellm-proxy
cd /opt/openhands-litellm-proxy

# Clone the repository (if using Git)
# git clone https://your-repository-url.git .

# Or copy the files manually
# scp -r /path/to/litellm-proxy/* user@server:/opt/openhands-litellm-proxy/
```

## Step 3: Set Up Python Virtual Environment

```bash
# Create a virtual environment
python3 -m venv venv

# Activate the virtual environment
source venv/bin/activate

# Install dependencies
./install_dependencies.sh
```

## Step 4: Configure API Keys

Edit the `start_custom_server.sh` script to set your actual API keys:

```bash
# Edit the start script
nano start_custom_server.sh
```

Update the following lines with your actual API keys:

```bash
export AZURE_API_BASE="your-azure-api-base"
export AZURE_API_KEY="your-azure-api-key"
export ANTHROPIC_API_KEY="your-anthropic-api-key"
```

## Step 5: Generate API Keys for OpenHands Instances

```bash
# Generate API keys for each OpenHands instance
./create_api_key.sh openhands-instance-1
./create_api_key.sh openhands-instance-2
```

Add the generated API keys to the `litellm_server.py` file:

```bash
# Edit the server file
nano litellm_server.py
```

Update the `API_KEYS` dictionary with the generated keys:

```python
API_KEYS = {
    "sk-openhands-instance-1-abc123def456": "openhands-instance-1",
    "sk-openhands-instance-2-789012ghijkl": "openhands-instance-2",
}
```

## Step 6: Set Up Systemd Service

Create a systemd service file to run the proxy as a service:

```bash
sudo nano /etc/systemd/system/openhands-litellm-proxy.service
```

Add the following content:

```ini
[Unit]
Description=OpenHands LiteLLM Proxy
After=network.target

[Service]
User=ubuntu  # Replace with your user
WorkingDirectory=/opt/openhands-litellm-proxy
ExecStart=/opt/openhands-litellm-proxy/venv/bin/python /opt/openhands-litellm-proxy/litellm_server.py
Environment="AZURE_API_BASE=your-azure-api-base"
Environment="AZURE_API_KEY=your-azure-api-key"
Environment="ANTHROPIC_API_KEY=your-anthropic-api-key"
Environment="PORT=54658"
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Enable and start the service:

```bash
sudo systemctl daemon-reload
sudo systemctl enable openhands-litellm-proxy
sudo systemctl start openhands-litellm-proxy
```

Check the status of the service:

```bash
sudo systemctl status openhands-litellm-proxy
```

## Step 7: Set Up Firewall

Allow traffic to the proxy port:

```bash
sudo ufw allow 54658/tcp
```

## Step 8: Configure OpenHands Instances

On each OpenHands instance, set the following environment variables:

```bash
export OPENAI_API_KEY="sk-openhands-instance-1-abc123def456"  # Use the appropriate key for each instance
export OPENAI_API_BASE="http://<your-server-ip>:54658"
export OPENAI_API_TYPE="openai"
```

## Step 9: Test the Proxy

Test the proxy from your local machine:

```bash
curl http://<your-server-ip>:54658/health
```

You should see a response like:

```json
{"status":"healthy","models":["gpt-3.5-turbo","gpt-4","claude-3-opus"]}
```

## Step 10: Set Up HTTPS (Optional but Recommended)

For production use, it's recommended to set up HTTPS using a reverse proxy like Nginx with Let's Encrypt:

```bash
# Install Nginx
sudo apt install -y nginx

# Install Certbot for Let's Encrypt
sudo apt install -y certbot python3-certbot-nginx

# Configure Nginx
sudo nano /etc/nginx/sites-available/openhands-litellm-proxy
```

Add the following configuration:

```nginx
server {
    listen 80;
    server_name proxy.yourdomain.com;  # Replace with your domain

    location / {
        proxy_pass http://localhost:54658;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

Enable the site and get an SSL certificate:

```bash
sudo ln -s /etc/nginx/sites-available/openhands-litellm-proxy /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
sudo certbot --nginx -d proxy.yourdomain.com
```

Update your OpenHands instances to use HTTPS:

```bash
export OPENAI_API_BASE="https://proxy.yourdomain.com"
```

## Monitoring and Maintenance

### View Logs

```bash
# View systemd service logs
sudo journalctl -u openhands-litellm-proxy -f

# View application logs
tail -f /opt/openhands-litellm-proxy/logs/server.log
```

### Restart the Service

```bash
sudo systemctl restart openhands-litellm-proxy
```

### Update the Proxy

```bash
cd /opt/openhands-litellm-proxy
source venv/bin/activate

# Pull latest changes if using Git
# git pull

# Or update files manually
# scp -r /path/to/litellm-proxy/* user@server:/opt/openhands-litellm-proxy/

# Restart the service
sudo systemctl restart openhands-litellm-proxy
```

## Troubleshooting

### Service Won't Start

Check the logs for errors:

```bash
sudo journalctl -u openhands-litellm-proxy -e
```

### Connection Issues

Verify the server is listening on the correct port:

```bash
sudo netstat -tuln | grep 54658
```

Check firewall settings:

```bash
sudo ufw status
```

### API Key Issues

Verify the API keys are correctly set in the environment variables:

```bash
sudo systemctl show openhands-litellm-proxy -p Environment
```