#!/usr/bin/env python3
"""
OpenHands LiteLLM Proxy Server
A simple proxy server for LiteLLM that supports multiple LLM providers.
"""

import os
import json
import time
import logging
import asyncio
from typing import Optional, List, Dict, Any, Union
from datetime import datetime

import litellm
from fastapi import FastAPI, Request, Depends, HTTPException, Form
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(os.path.join(os.path.dirname(__file__), "logs", "server.log"))
    ]
)
logger = logging.getLogger("openhands-litellm-proxy")

# Initialize FastAPI app
app = FastAPI(title="OpenHands LiteLLM Proxy")
security = HTTPBearer(auto_error=False)

# Create directories if they don't exist
static_dir = os.path.join(os.path.dirname(__file__), "static")
templates_dir = os.path.join(os.path.dirname(__file__), "templates")
os.makedirs(static_dir, exist_ok=True)
os.makedirs(templates_dir, exist_ok=True)

# Create CSS file if it doesn't exist
css_file = os.path.join(static_dir, "styles.css")
if not os.path.exists(css_file):
    with open(css_file, "w") as f:
        f.write("""
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            line-height: 1.6;
            margin: 0;
            padding: 0;
            color: #333;
            background-color: #f5f7fa;
        }
        .container {
            width: 90%;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
        }
        header {
            background-color: #4F46E5;
            color: white;
            padding: 1rem;
            margin-bottom: 2rem;
        }
        h1, h2, h3 {
            color: #2D3748;
        }
        .card {
            background: white;
            border-radius: 8px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
            padding: 20px;
            margin-bottom: 20px;
        }
        .form-group {
            margin-bottom: 15px;
        }
        label {
            display: block;
            margin-bottom: 5px;
            font-weight: 600;
        }
        input[type="text"], input[type="password"], textarea, select {
            width: 100%;
            padding: 10px;
            border: 1px solid #ddd;
            border-radius: 4px;
            font-size: 16px;
        }
        button {
            background-color: #4F46E5;
            color: white;
            border: none;
            padding: 10px 15px;
            border-radius: 4px;
            cursor: pointer;
            font-size: 16px;
        }
        button:hover {
            background-color: #4338CA;
        }
        .alert {
            padding: 15px;
            margin-bottom: 20px;
            border-radius: 4px;
        }
        .alert-success {
            background-color: #D1FAE5;
            border: 1px solid #10B981;
            color: #047857;
        }
        .alert-danger {
            background-color: #FEE2E2;
            border: 1px solid #EF4444;
            color: #B91C1C;
        }
        table {
            width: 100%;
            border-collapse: collapse;
            margin-bottom: 20px;
        }
        th, td {
            padding: 12px 15px;
            text-align: left;
            border-bottom: 1px solid #ddd;
        }
        th {
            background-color: #f8fafc;
            font-weight: 600;
        }
        tr:hover {
            background-color: #f1f5f9;
        }
        .badge {
            display: inline-block;
            padding: 3px 8px;
            border-radius: 12px;
            font-size: 12px;
            font-weight: 600;
        }
        .badge-success {
            background-color: #D1FAE5;
            color: #047857;
        }
        .badge-warning {
            background-color: #FEF3C7;
            color: #92400E;
        }
        .badge-danger {
            background-color: #FEE2E2;
            color: #B91C1C;
        }
        .tabs {
            display: flex;
            margin-bottom: 20px;
            border-bottom: 1px solid #ddd;
        }
        .tab {
            padding: 10px 20px;
            cursor: pointer;
            margin-right: 5px;
            border-radius: 4px 4px 0 0;
        }
        .tab.active {
            background-color: #4F46E5;
            color: white;
            border: 1px solid #4F46E5;
            border-bottom: none;
        }
        .tab:not(.active) {
            background-color: #f8fafc;
            border: 1px solid #ddd;
            border-bottom: none;
        }
        .tab-content {
            display: none;
        }
        .tab-content.active {
            display: block;
        }
        .code-block {
            background-color: #1E293B;
            color: #E2E8F0;
            padding: 15px;
            border-radius: 4px;
            font-family: monospace;
            overflow-x: auto;
            margin-bottom: 20px;
        }
        .logs {
            background-color: #1E293B;
            color: #E2E8F0;
            padding: 15px;
            border-radius: 4px;
            font-family: monospace;
            height: 600px;
            overflow-y: auto;
            margin-bottom: 20px;
        }
        .log-entry {
            margin-bottom: 5px;
            border-bottom: 1px solid #2D3748;
            padding-bottom: 5px;
        }
        .log-time {
            color: #9CA3AF;
            margin-right: 10px;
        }
        .log-level-info {
            color: #60A5FA;
        }
        .log-level-error {
            color: #F87171;
        }
        .log-level-warning {
            color: #FBBF24;
        }
        .log-message {
            color: #E2E8F0;
        }
        """)

# Create HTML template if it doesn't exist
html_file = os.path.join(templates_dir, "index.html")
if not os.path.exists(html_file):
    with open(html_file, "w") as f:
        f.write("""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>OpenHands LiteLLM Proxy</title>
            <link rel="stylesheet" href="/static/styles.css">
        </head>
        <body>
            <header>
                <div class="container">
                    <h1>OpenHands LiteLLM Proxy</h1>
                </div>
            </header>
            <div class="container">
                {% if message %}
                <div class="alert alert-{{ message_type }}">
                    {{ message }}
                </div>
                {% endif %}
                
                <div class="tabs">
                    <div class="tab active" onclick="openTab(event, 'dashboard')">Dashboard</div>
                    <div class="tab" onclick="openTab(event, 'config')">Configuration</div>
                    <div class="tab" onclick="openTab(event, 'keys')">API Keys</div>
                    <div class="tab" onclick="openTab(event, 'logs')">Logs</div>
                </div>
                
                <div id="dashboard" class="tab-content active">
                    <div class="card">
                        <h2>Status</h2>
                        <p>Server is <span class="badge badge-success">Running</span></p>
                        <p>Available Models: 
                            {% for model in models %}
                            <span class="badge badge-success">{{ model }}</span>
                            {% endfor %}
                        </p>
                    </div>
                    
                    <div class="card">
                        <h2>Test Connection</h2>
                        <form action="/test-connection" method="post">
                            <div class="form-group">
                                <label for="model">Model</label>
                                <select name="model" id="model">
                                    {% for model in models %}
                                    <option value="{{ model }}">{{ model }}</option>
                                    {% endfor %}
                                </select>
                            </div>
                            <div class="form-group">
                                <label for="prompt">Test Prompt</label>
                                <textarea name="prompt" id="prompt" rows="4">Hello, how are you today?</textarea>
                            </div>
                            <button type="submit">Test Connection</button>
                        </form>
                        {% if test_result %}
                        <div class="alert alert-{{ test_result.status }}">
                            {{ test_result.message }}
                        </div>
                        {% endif %}
                    </div>
                </div>
                
                <div id="config" class="tab-content">
                    <div class="card">
                        <h2>Provider Configuration</h2>
                        <form action="/update-config" method="post">
                            <h3>OpenAI Configuration</h3>
                            <div class="form-group">
                                <label for="openai_api_key">OpenAI API Key</label>
                                <input type="password" name="openai_api_key" id="openai_api_key" value="{{ config.openai_api_key or '' }}">
                            </div>
                            
                            <h3>Anthropic Configuration</h3>
                            <div class="form-group">
                                <label for="anthropic_api_key">Anthropic API Key</label>
                                <input type="password" name="anthropic_api_key" id="anthropic_api_key" value="{{ config.anthropic_api_key or '' }}">
                            </div>
                            
                            <h3>Google Gemini Configuration</h3>
                            <div class="form-group">
                                <label for="gemini_api_key">Gemini API Key</label>
                                <input type="password" name="gemini_api_key" id="gemini_api_key" value="{{ config.gemini_api_key or '' }}">
                            </div>
                            
                            <button type="submit">Save Configuration</button>
                        </form>
                    </div>
                </div>
                
                <div id="keys" class="tab-content">
                    <div class="card">
                        <h2>API Keys</h2>
                        <table>
                            <thead>
                                <tr>
                                    <th>Name</th>
                                    <th>API Key</th>
                                    <th>Models</th>
                                    <th>Created</th>
                                </tr>
                            </thead>
                            <tbody>
                                {% for key in api_keys %}
                                <tr>
                                    <td>{{ key.name }}</td>
                                    <td>{{ key.key }}</td>
                                    <td>
                                        {% for model in key.models %}
                                        <span class="badge badge-success">{{ model }}</span>
                                        {% else %}
                                        <span class="badge badge-warning">All Models</span>
                                        {% endfor %}
                                    </td>
                                    <td>{{ key.created }}</td>
                                </tr>
                                {% else %}
                                <tr>
                                    <td colspan="4">No API keys configured</td>
                                </tr>
                                {% endfor %}
                            </tbody>
                        </table>
                        
                        <h3>Create API Key</h3>
                        <form action="/create-api-key" method="post">
                            <div class="form-group">
                                <label for="key_name">Name</label>
                                <input type="text" name="key_name" id="key_name" required>
                            </div>
                            <div class="form-group">
                                <label for="key_models">Models (comma-separated, leave empty for all models)</label>
                                <input type="text" name="key_models" id="key_models">
                            </div>
                            <button type="submit">Create API Key</button>
                        </form>
                    </div>
                </div>
                
                <div id="logs" class="tab-content">
                    <div class="card">
                        <h2>Server Logs</h2>
                        <div class="logs" id="log-container">
                            {% for log in logs %}
                            <div class="log-entry">
                                <span class="log-time">{{ log.time }}</span>
                                <span class="log-level-{{ log.level }}">{{ log.level }}</span>
                                <span class="log-message">{{ log.message }}</span>
                            </div>
                            {% endfor %}
                        </div>
                    </div>
                </div>
            </div>
            
            <script>
                function openTab(evt, tabName) {
                    var i, tabcontent, tablinks;
                    tabcontent = document.getElementsByClassName("tab-content");
                    for (i = 0; i < tabcontent.length; i++) {
                        tabcontent[i].className = tabcontent[i].className.replace(" active", "");
                    }
                    tablinks = document.getElementsByClassName("tab");
                    for (i = 0; i < tablinks.length; i++) {
                        tablinks[i].className = tablinks[i].className.replace(" active", "");
                    }
                    document.getElementById(tabName).className += " active";
                    evt.currentTarget.className += " active";
                }
                
                function refreshLogs() {
                    fetch('/api/logs')
                        .then(response => response.json())
                        .then(data => {
                            const logContainer = document.getElementById('log-container');
                            logContainer.innerHTML = '';
                            data.forEach(log => {
                                logContainer.innerHTML += `
                                <div class="log-entry">
                                    <span class="log-time">${log.time}</span>
                                    <span class="log-level-${log.level}">${log.level}</span>
                                    <span class="log-message">${log.message}</span>
                                </div>
                                `;
                            });
                            // Scroll to the bottom of the log container
                            logContainer.scrollTop = logContainer.scrollHeight;
                        });
                }
                
                // Auto-refresh logs every 10 seconds
                setInterval(refreshLogs, 10000);
            </script>
        </body>
        </html>
        """)

# Mount static files
app.mount("/static", StaticFiles(directory=static_dir), name="static")

# Set up templates
templates = Jinja2Templates(directory=templates_dir)

# Config file paths
CONFIG_FILE = os.path.join(os.path.dirname(__file__), "config.json")
API_KEYS_FILE = os.path.join(os.path.dirname(__file__), "keys", "api_keys.json")
LOGS_FILE = os.path.join(os.path.dirname(__file__), "logs", "server.log")

# Load or create config
def load_config():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r") as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error loading config: {str(e)}")
    return {}

def save_config(config_data):
    try:
        with open(CONFIG_FILE, "w") as f:
            json.dump(config_data, f, indent=2)
        return True
    except Exception as e:
        logger.error(f"Error saving config: {str(e)}")
        return False

# Load or create API keys
def load_api_keys():
    if os.path.exists(API_KEYS_FILE):
        try:
            with open(API_KEYS_FILE, "r") as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error loading API keys: {str(e)}")
    return {}

def save_api_keys(api_keys):
    try:
        with open(API_KEYS_FILE, "w") as f:
            json.dump(api_keys, f, indent=2)
        return True
    except Exception as e:
        logger.error(f"Error saving API keys: {str(e)}")
        return False

# Load or create initial data
config = load_config()
api_keys = load_api_keys()

# Define API keys - add your OpenHands instances here
API_KEYS = api_keys

# Global variable to store discovered models
DISCOVERED_MODELS = {}

# Model routing configuration - just the three specified models
def get_model_config():
    global DISCOVERED_MODELS
    model_config = {}
    
    # Use discovered models if available
    if DISCOVERED_MODELS:
        logger.info(f"Using {len(DISCOVERED_MODELS)} discovered models")
        return DISCOVERED_MODELS
    
    # Anthropic model - Claude 3.7 Sonnet
    if config.get("anthropic_api_key"):
        anthropic_models = {
            "claude-3.7-sonnet": {
                "model": "anthropic/claude-3-7-sonnet-20250219",
                "api_key": config.get("anthropic_api_key", ""),
            }
        }
        model_config.update(anthropic_models)
    
    # OpenAI model - GPT-4 Turbo
    if config.get("openai_api_key"):
        openai_models = {
            "gpt-4-turbo": {
                "model": "openai/gpt-4-turbo",
                "api_key": config.get("openai_api_key", ""),
            }
        }
        model_config.update(openai_models)
    
    # Gemini model - Gemini 2.0 Flash
    if config.get("gemini_api_key"):
        gemini_models = {
            "gemini-2.0-flash": {
                "model": "gemini/gemini-2.0-flash",
                "api_key": config.get("gemini_api_key", ""),
            }
        }
        model_config.update(gemini_models)
    
    # If no models are configured, add placeholders
    if not model_config:
        model_config = {
            "claude-3.7-sonnet": {
                "model": "anthropic/claude-3-7-sonnet-20250219",
                "api_key": "",
            },
            "gpt-4-turbo": {
                "model": "openai/gpt-4-turbo",
                "api_key": "",
            },
            "gemini-2.0-flash": {
                "model": "gemini/gemini-2.0-flash",
                "api_key": "",
            }
        }
    
    return model_config

# Function to fetch available models from providers and update model config
async def fetch_available_models():
    global DISCOVERED_MODELS
    available_models = {}
    model_config = {}
    
    # Fetch Anthropic model - Claude 3.7 Sonnet
    if config.get("anthropic_api_key"):
        try:
            logger.info("Fetching Anthropic model...")
            anthropic_models = [
                {"id": "claude-3-7-sonnet-20250219", "name": "claude-3.7-sonnet"}
            ]
            available_models["anthropic"] = anthropic_models
            
            # Update model config for Anthropic
            model_config["claude-3.7-sonnet"] = {
                "model": "anthropic/claude-3-7-sonnet-20250219",
                "api_key": config.get("anthropic_api_key", ""),
            }
            
            logger.info("Found Anthropic model: claude-3.7-sonnet")
        except Exception as e:
            logger.error(f"Error fetching Anthropic model: {str(e)}")
    
    # Fetch OpenAI model - GPT-4 Turbo
    if config.get("openai_api_key"):
        try:
            logger.info("Fetching OpenAI model...")
            openai_models = [
                {"id": "gpt-4-turbo", "name": "gpt-4-turbo"}
            ]
            available_models["openai"] = openai_models
            
            # Update model config for OpenAI
            model_config["gpt-4-turbo"] = {
                "model": "openai/gpt-4-turbo",
                "api_key": config.get("openai_api_key", ""),
            }
            
            logger.info("Found OpenAI model: gpt-4-turbo")
        except Exception as e:
            logger.error(f"Error fetching OpenAI model: {str(e)}")
    
    # Fetch Gemini model - Gemini 2.0 Flash
    if config.get("gemini_api_key"):
        try:
            logger.info("Fetching Gemini model...")
            gemini_models = [
                {"id": "gemini-2.0-flash", "name": "gemini-2.0-flash"}
            ]
            available_models["gemini"] = gemini_models
            
            # Update model config for Gemini
            model_config["gemini-2.0-flash"] = {
                "model": "gemini/gemini-2.0-flash",
                "api_key": config.get("gemini_api_key", ""),
            }
            
            logger.info("Found Gemini model: gemini-2.0-flash")
        except Exception as e:
            logger.error(f"Error fetching Gemini model: {str(e)}")
    
    # Update the global discovered models
    if model_config:
        global MODEL_CONFIG
        DISCOVERED_MODELS = model_config
        MODEL_CONFIG = model_config
        logger.info(f"Updated model configuration with {len(model_config)} models")
    
    return available_models

MODEL_CONFIG = get_model_config()

# Authentication dependency
async def get_api_key(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
) -> Optional[str]:
    if credentials:
        token = credentials.credentials
        if token in API_KEYS:
            return token
    
    # Allow requests without authentication for testing
    return None

# Read logs
def read_logs(n=200):
    logs = []
    try:
        with open(LOGS_FILE, "r") as f:
            lines = f.readlines()
            for line in lines[-n:]:
                parts = line.strip().split(" - ", 3)
                if len(parts) >= 3:
                    time_str = parts[0]
                    level = parts[2]
                    message = parts[3] if len(parts) > 3 else ""
                    logs.append({
                        "time": time_str,
                        "level": level.lower(),
                        "message": message
                    })
    except Exception as e:
        logger.error(f"Error reading logs: {str(e)}")
    return logs

# Pydantic models for API
class Message(BaseModel):
    role: str
    content: str

class ChatCompletionRequest(BaseModel):
    model: str
    messages: List[Message]
    temperature: float = 0.7
    max_tokens: int = 100
    client: Optional[Any] = None

# Routes
@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse(
        "index.html", 
        {
            "request": request,
            "models": list(MODEL_CONFIG.keys()),
            "config": config,
            "api_keys": [
                {
                    "name": details.get("name", "Unknown"),
                    "key": key,
                    "models": details.get("models", []),
                    "created": details.get("created", "Unknown")
                }
                for key, details in API_KEYS.items()
            ],
            "logs": read_logs()
        }
    )

@app.post("/update-config")
async def update_config(
    request: Request,
    anthropic_api_key: str = Form(""),
    openai_api_key: str = Form(""),
    gemini_api_key: str = Form(""),
):
    global config, MODEL_CONFIG, DISCOVERED_MODELS
    
    # Store the current discovered models
    current_discovered_models = DISCOVERED_MODELS.copy() if DISCOVERED_MODELS else {}
    
    # Update config
    config = {
        "anthropic_api_key": anthropic_api_key,
        "openai_api_key": openai_api_key,
        "gemini_api_key": gemini_api_key,
    }
    
    # Save config
    success = save_config(config)
    
    # Set environment variables
    os.environ["ANTHROPIC_API_KEY"] = anthropic_api_key
    os.environ["OPENAI_API_KEY"] = openai_api_key
    os.environ["GEMINI_API_KEY"] = gemini_api_key
    
    # If we have discovered models, use them
    if current_discovered_models:
        DISCOVERED_MODELS = current_discovered_models
        MODEL_CONFIG = current_discovered_models
    else:
        # Otherwise, update model config and fetch models
        MODEL_CONFIG = get_model_config()
        # Fetch available models asynchronously
        asyncio.create_task(fetch_available_models())
    
    logger.info("Configuration updated")
    
    return templates.TemplateResponse(
        "index.html", 
        {
            "request": request,
            "models": list(MODEL_CONFIG.keys()),
            "config": config,
            "api_keys": [
                {
                    "name": details.get("name", "Unknown"),
                    "key": key,
                    "models": details.get("models", []),
                    "created": details.get("created", "Unknown")
                }
                for key, details in API_KEYS.items()
            ],
            "logs": read_logs(),
            "message": "Configuration updated successfully",
            "message_type": "success"
        }
    )

@app.post("/create-api-key")
async def create_api_key(
    request: Request,
    key_name: str = Form(...),
    key_models: str = Form(""),
):
    global API_KEYS
    
    # Generate a random API key
    import secrets
    api_key = f"sk-{secrets.token_hex(16)}"
    
    # Parse models
    models = [model.strip() for model in key_models.split(",")] if key_models else []
    
    # Add to API keys
    API_KEYS[api_key] = {
        "name": key_name,
        "models": models,
        "created": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    
    # Save API keys
    success = save_api_keys(API_KEYS)
    
    logger.info(f"Created API key: {key_name}")
    
    return templates.TemplateResponse(
        "index.html", 
        {
            "request": request,
            "models": list(MODEL_CONFIG.keys()),
            "config": config,
            "api_keys": [
                {
                    "name": details.get("name", "Unknown"),
                    "key": key,
                    "models": details.get("models", []),
                    "created": details.get("created", "Unknown")
                }
                for key, details in API_KEYS.items()
            ],
            "logs": read_logs(),
            "message": f"API key created: {api_key}",
            "message_type": "success"
        }
    )

@app.post("/test-connection")
async def test_connection(
    request: Request,
    model: str = Form(...),
    prompt: str = Form(...),
):
    # Check if model exists
    if model not in MODEL_CONFIG:
        return templates.TemplateResponse(
            "index.html", 
            {
                "request": request,
                "models": list(MODEL_CONFIG.keys()),
                "config": config,
                "api_keys": [
                    {
                        "name": details.get("name", "Unknown"),
                        "key": key,
                        "models": details.get("models", []),
                        "created": details.get("created", "Unknown")
                    }
                    for key, details in API_KEYS.items()
                ],
                "logs": read_logs(),
                "test_result": {
                    "status": "danger",
                    "message": f"Model {model} not supported"
                }
            }
        )
    
    model_config = MODEL_CONFIG[model]
    
    # Check if API key is set
    provider = model_config["model"].split("/")[0]
    if not model_config.get("api_key"):
        return templates.TemplateResponse(
            "index.html", 
            {
                "request": request,
                "models": list(MODEL_CONFIG.keys()),
                "config": config,
                "api_keys": [
                    {
                        "name": details.get("name", "Unknown"),
                        "key": key,
                        "models": details.get("models", []),
                        "created": details.get("created", "Unknown")
                    }
                    for key, details in API_KEYS.items()
                ],
                "logs": read_logs(),
                "test_result": {
                    "status": "danger",
                    "message": f"{provider.capitalize()} API Key must be configured"
                }
            }
        )
    
    # Call the model
    messages = [{"role": "user", "content": prompt}]
    
    logger.info(f"Testing connection to {model}")
    
    try:
        response = litellm.completion(
            model=model_config["model"],
            messages=messages,
            temperature=0.7,
            max_tokens=100,
            api_key=model_config.get("api_key"),
        )
        
        logger.info(f"Connection test successful: {model}")
        
        return templates.TemplateResponse(
            "index.html", 
            {
                "request": request,
                "models": list(MODEL_CONFIG.keys()),
                "config": config,
                "api_keys": [
                    {
                        "name": details.get("name", "Unknown"),
                        "key": key,
                        "models": details.get("models", []),
                        "created": details.get("created", "Unknown")
                    }
                    for key, details in API_KEYS.items()
                ],
                "logs": read_logs(),
                "test_result": {
                    "status": "success",
                    "message": f"Connection successful! Response: {response.choices[0].message.content[:100]}..."
                }
            }
        )
    except Exception as e:
        logger.error(f"Connection test failed: {str(e)}")
        
        return templates.TemplateResponse(
            "index.html", 
            {
                "request": request,
                "models": list(MODEL_CONFIG.keys()),
                "config": config,
                "api_keys": [
                    {
                        "name": details.get("name", "Unknown"),
                        "key": key,
                        "models": details.get("models", []),
                        "created": details.get("created", "Unknown")
                    }
                    for key, details in API_KEYS.items()
                ],
                "logs": read_logs(),
                "test_result": {
                    "status": "danger",
                    "message": f"Connection failed: {str(e)}"
                }
            }
        )

@app.get("/api/logs")
async def api_logs():
    return read_logs()

@app.get("/api/available-models")
async def api_available_models():
    """Fetch available models from all configured providers"""
    return await fetch_available_models()

# Health check endpoint
@app.get("/health")
async def health_check():
    return {"status": "healthy", "models": list(MODEL_CONFIG.keys())}

# List models endpoint (OpenAI compatible)
@app.get("/v1/models")
async def list_models():
    models = [{"id": model, "object": "model"} for model in MODEL_CONFIG.keys()]
    return {"object": "list", "data": models}

# Chat completions endpoint (OpenAI compatible)
@app.post("/v1/chat/completions")
async def chat_completions(
    request: ChatCompletionRequest,
    api_key: Optional[str] = Depends(get_api_key),
):
    try:
        # Get the model configuration
        model = request.model
        if model not in MODEL_CONFIG:
            logger.warning(f"Model not supported: {model}")
            raise HTTPException(status_code=400, detail=f"Model {model} not supported")
        
        model_config = MODEL_CONFIG[model]
        
        # Check if API key is set
        provider = model_config["model"].split("/")[0]
        if not model_config.get("api_key"):
            logger.error(f"Provider API key not configured: {provider}")
            raise HTTPException(
                status_code=400, 
                detail=f"{provider.capitalize()} API Key must be configured"
            )
        
        # Check if API key is authorized for this model
        if api_key and api_key in API_KEYS:
            allowed_models = API_KEYS[api_key].get("models", [])
            if allowed_models and model not in allowed_models:
                logger.warning(f"API key not authorized for model: {model}")
                raise HTTPException(status_code=403, detail=f"API key not authorized for model: {model}")
        
        # Log the request
        client_name = API_KEYS.get(api_key, {}).get("name", "anonymous") if api_key else "anonymous"
        client_ip = request.client.host if hasattr(request, "client") else "unknown"
        logger.info(f"Request: {model} from {client_name} ({client_ip})")
        
        # Convert Pydantic messages to dict format for litellm
        messages = [{"role": msg.role, "content": msg.content} for msg in request.messages]
        
        # Call the model using LiteLLM
        start_time = time.time()
        response = litellm.completion(
            model=model_config["model"],
            messages=messages,
            temperature=request.temperature,
            max_tokens=request.max_tokens,
            api_key=model_config.get("api_key"),
        )
        end_time = time.time()
        
        # Log the response
        duration = round(end_time - start_time, 2)
        tokens = response.usage.total_tokens if hasattr(response, "usage") and hasattr(response.usage, "total_tokens") else "unknown"
        logger.info(f"Response: {model} to {client_name} - {duration}s, {tokens} tokens")
        
        return response
    
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Startup event to fetch available models
@app.on_event("startup")
async def startup_event():
    global config
    
    # Log startup
    port = int(os.environ.get("PORT", 54658))
    logger.info(f"Starting OpenHands LiteLLM Proxy on port {port}...")
    logger.info(f"Available models: {', '.join(MODEL_CONFIG.keys())}")
    logger.info(f"Web UI available at http://localhost:{port}")
    
    # Set environment variables
    os.environ["ANTHROPIC_API_KEY"] = config.get("anthropic_api_key", "")
    os.environ["OPENAI_API_KEY"] = config.get("openai_api_key", "")
    os.environ["GEMINI_API_KEY"] = config.get("gemini_api_key", "")
    
    # Fetch available models
    logger.info("Server starting up, fetching available models...")
    await fetch_available_models()

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 54658))
    uvicorn.run(app, host="0.0.0.0", port=port)