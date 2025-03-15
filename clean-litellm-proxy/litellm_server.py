#!/usr/bin/env python3
"""
LiteLLM proxy server for OpenHands using FastAPI.
This server provides a central API endpoint for multiple OpenHands instances
to access various LLM providers through a unified interface.
"""

import os
import json
import time
import logging
import uvicorn
from fastapi import FastAPI, Request, Depends, HTTPException, Form, Body
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field
import litellm
import uuid
import datetime

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(os.path.dirname(__file__), "logs", "server.log")),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("openhands-litellm-proxy")

# Define request models
class Message(BaseModel):
    role: str
    content: str

class ChatCompletionRequest(BaseModel):
    model: str
    messages: List[Message]
    temperature: Optional[float] = 1.0
    max_tokens: Optional[int] = None

class ProviderConfig(BaseModel):
    azure_api_base: Optional[str] = None
    azure_api_key: Optional[str] = None
    azure_api_version: Optional[str] = "2023-07-01-preview"
    anthropic_api_key: Optional[str] = None
    openai_api_key: Optional[str] = None

class APIKeyCreate(BaseModel):
    name: str
    description: Optional[str] = None
    models: List[str] = ["gpt-3.5-turbo", "gpt-4", "claude-3-opus"]

# Create directories if they don't exist
os.makedirs(os.path.join(os.path.dirname(__file__), "logs"), exist_ok=True)
os.makedirs(os.path.join(os.path.dirname(__file__), "keys"), exist_ok=True)
os.makedirs(os.path.join(os.path.dirname(__file__), "static"), exist_ok=True)
os.makedirs(os.path.join(os.path.dirname(__file__), "templates"), exist_ok=True)

# Create FastAPI app
app = FastAPI(
    title="OpenHands LiteLLM Proxy",
    description="LAN-accessible LiteLLM proxy for OpenHands instances",
    version="1.0.0"
)

# Add CORS middleware to allow requests from any origin
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Set up authentication
security = HTTPBearer(auto_error=False)

# Create templates directory and files
templates_dir = os.path.join(os.path.dirname(__file__), "templates")
os.makedirs(templates_dir, exist_ok=True)

# Create static directory for CSS and JS
static_dir = os.path.join(os.path.dirname(__file__), "static")
os.makedirs(static_dir, exist_ok=True)

# Create CSS file
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
            height: 300px;
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

# Create index.html template
index_template = os.path.join(templates_dir, "index.html")
if not os.path.exists(index_template):
    with open(index_template, "w") as f:
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
                                <textarea name="prompt" id="prompt" rows="3">Hello, how are you today?</textarea>
                            </div>
                            <button type="submit">Test Connection</button>
                        </form>
                    </div>
                    
                    {% if test_result %}
                    <div class="card">
                        <h2>Test Result</h2>
                        <div class="alert alert-{{ test_result.status }}">
                            {{ test_result.message }}
                        </div>
                        {% if test_result.response %}
                        <div class="code-block">
                            {{ test_result.response }}
                        </div>
                        {% endif %}
                    </div>
                    {% endif %}
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
                            
                            <button type="submit">Save Configuration</button>
                        </form>
                    </div>
                    
                    <div class="card">
                        <h2>Available Models</h2>
                        <p>Click the button below to fetch available models from the configured providers.</p>
                        <button onclick="fetchAvailableModels()">Fetch Available Models</button>
                        <div id="available-models-container" style="margin-top: 20px; display: none;">
                            <h3>Available Models</h3>
                            <div id="available-models"></div>
                        </div>
                        
                        <script>
                            function fetchAvailableModels() {
                                document.getElementById('available-models-container').style.display = 'block';
                                document.getElementById('available-models').innerHTML = '<p>Fetching models... This may take a few moments.</p>';
                                
                                fetch('/api/available-models')
                                    .then(response => response.json())
                                    .then(data => {
                                        let html = '';
                                        
                                        if (Object.keys(data).length === 0) {
                                            html = '<p>No models found. Please check your API keys and try again.</p>';
                                        } else {
                                            for (const provider in data) {
                                                html += `<h4>${provider.charAt(0).toUpperCase() + provider.slice(1)} Models</h4>`;
                                                html += '<ul>';
                                                
                                                data[provider].forEach(model => {
                                                    html += `<li>${model.name}</li>`;
                                                });
                                                
                                                html += '</ul>';
                                            }
                                        }
                                        
                                        document.getElementById('available-models').innerHTML = html;
                                    })
                                    .catch(error => {
                                        document.getElementById('available-models').innerHTML = `<p>Error fetching models: ${error.message}</p>`;
                                    });
                            }
                        </script>
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
                                    <td><code>{{ key.key }}</code></td>
                                    <td>
                                        {% for model in key.models %}
                                        <span class="badge badge-success">{{ model }}</span>
                                        {% endfor %}
                                    </td>
                                    <td>{{ key.created }}</td>
                                </tr>
                                {% endfor %}
                            </tbody>
                        </table>
                    </div>
                    
                    <div class="card">
                        <h2>Create New API Key</h2>
                        <form action="/create-key" method="post">
                            <div class="form-group">
                                <label for="name">Name</label>
                                <input type="text" name="name" id="name" placeholder="e.g., openhands-instance-1" required>
                            </div>
                            <div class="form-group">
                                <label for="description">Description (Optional)</label>
                                <input type="text" name="description" id="description" placeholder="e.g., OpenHands instance for marketing team">
                            </div>
                            <div class="form-group">
                                <label>Allowed Models</label>
                                {% for model in models %}
                                <div>
                                    <input type="checkbox" name="models" id="model-{{ model }}" value="{{ model }}" checked>
                                    <label for="model-{{ model }}">{{ model }}</label>
                                </div>
                                {% endfor %}
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
                        <button onclick="refreshLogs()">Refresh Logs</button>
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
    return {
        "azure_api_base": os.getenv("AZURE_API_BASE", ""),
        "azure_api_key": os.getenv("AZURE_API_KEY", ""),
        "azure_api_version": os.getenv("AZURE_API_VERSION", "2023-07-01-preview"),
        "anthropic_api_key": os.getenv("ANTHROPIC_API_KEY", ""),
        "openai_api_key": os.getenv("OPENAI_API_KEY", ""),
    }

def save_config(config):
    try:
        with open(CONFIG_FILE, "w") as f:
            json.dump(config, f, indent=2)
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

# Model routing configuration - customize with your API keys
def get_model_config():
    model_config = {}
    
    # Anthropic models
    if config.get("anthropic_api_key"):
        anthropic_models = {
            "claude-3-opus": {
                "model": "anthropic/claude-3-opus-20240229",
                "api_key": config.get("anthropic_api_key", ""),
            },
            "claude-3-sonnet": {
                "model": "anthropic/claude-3-sonnet-20240229",
                "api_key": config.get("anthropic_api_key", ""),
            },
            "claude-3-haiku": {
                "model": "anthropic/claude-3-haiku-20240307",
                "api_key": config.get("anthropic_api_key", ""),
            },
        }
        model_config.update(anthropic_models)
    
    # OpenAI models
    if config.get("openai_api_key"):
        openai_models = {
            "gpt-4o": {
                "model": "openai/gpt-4o",
                "api_key": config.get("openai_api_key", ""),
            },
            "gpt-4-turbo": {
                "model": "openai/gpt-4-turbo",
                "api_key": config.get("openai_api_key", ""),
            },
            "gpt-4": {
                "model": "openai/gpt-4",
                "api_key": config.get("openai_api_key", ""),
            },
            "gpt-3.5-turbo": {
                "model": "openai/gpt-3.5-turbo",
                "api_key": config.get("openai_api_key", ""),
            },
        }
        model_config.update(openai_models)
    
    # If no models are configured, add placeholders
    if not model_config:
        model_config = {
            "gpt-3.5-turbo": {
                "model": "openai/gpt-3.5-turbo",
                "api_key": "",
            },
            "gpt-4": {
                "model": "openai/gpt-4",
                "api_key": "",
            },
            "claude-3-opus": {
                "model": "anthropic/claude-3-opus-20240229",
                "api_key": "",
            },
        }
    
    return model_config

# Function to fetch available models from providers
async def fetch_available_models():
    available_models = {}
    
    # Fetch Anthropic models
    if config.get("anthropic_api_key"):
        try:
            logger.info("Fetching available Anthropic models...")
            # Anthropic doesn't have a list models endpoint, so we use a predefined list
            anthropic_models = [
                {"id": "claude-3-opus-20240229", "name": "claude-3-opus"},
                {"id": "claude-3-sonnet-20240229", "name": "claude-3-sonnet"},
                {"id": "claude-3-haiku-20240307", "name": "claude-3-haiku"},
                {"id": "claude-2.1", "name": "claude-2.1"},
                {"id": "claude-2.0", "name": "claude-2.0"},
                {"id": "claude-instant-1.2", "name": "claude-instant-1.2"}
            ]
            available_models["anthropic"] = anthropic_models
            logger.info(f"Found {len(anthropic_models)} Anthropic models")
        except Exception as e:
            logger.error(f"Error fetching Anthropic models: {str(e)}")
    
    # Fetch OpenAI models
    if config.get("openai_api_key"):
        try:
            logger.info("Fetching available OpenAI models...")
            import openai
            client = openai.OpenAI(api_key=config.get("openai_api_key"))
            models = client.models.list()
            openai_models = [{"id": model.id, "name": model.id} for model in models.data if "gpt" in model.id]
            available_models["openai"] = openai_models
            logger.info(f"Found {len(openai_models)} OpenAI models")
        except Exception as e:
            logger.error(f"Error fetching OpenAI models: {str(e)}")
    
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
def read_logs(n=50):
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

# Web UI routes
@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    global MODEL_CONFIG
    MODEL_CONFIG = get_model_config()
    
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
):
    global config, MODEL_CONFIG
    
    # Update config
    config = {
        "anthropic_api_key": anthropic_api_key,
        "openai_api_key": openai_api_key,
    }
    
    # Save config
    success = save_config(config)
    
    # Update model config
    MODEL_CONFIG = get_model_config()
    
    # Set environment variables
    os.environ["ANTHROPIC_API_KEY"] = anthropic_api_key
    os.environ["OPENAI_API_KEY"] = openai_api_key
    
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
            "message": "Configuration updated successfully" if success else "Error updating configuration",
            "message_type": "success" if success else "danger"
        }
    )

@app.post("/create-key")
async def create_key(
    request: Request,
    name: str = Form(...),
    description: str = Form(""),
    models: List[str] = Form([]),
):
    global API_KEYS
    
    # Generate API key
    api_key = f"sk-{name.lower()}-{uuid.uuid4().hex[:12]}"
    
    # Add to API keys
    API_KEYS[api_key] = {
        "name": name,
        "description": description,
        "models": models,
        "created": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    
    # Save API keys
    success = save_api_keys(API_KEYS)
    
    logger.info(f"API key created: {name}")
    
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
            "message": f"API key created successfully: {api_key}" if success else "Error creating API key",
            "message_type": "success" if success else "danger"
        }
    )

@app.post("/test-connection")
async def test_connection(
    request: Request,
    model: str = Form(...),
    prompt: str = Form(...),
):
    try:
        # Get model config
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
        
        # Check if API keys are set
        if model.startswith("gpt") and (not model_config.get("api_base") or not model_config.get("api_key")):
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
                        "message": "Azure API Base and API Key must be configured"
                    }
                }
            )
        
        if model.startswith("claude") and not model_config.get("api_key"):
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
                        "message": "Anthropic API Key must be configured"
                    }
                }
            )
        
        # Call the model
        messages = [{"role": "user", "content": prompt}]
        
        logger.info(f"Testing connection to {model}")
        
        response = litellm.completion(
            model=model_config["model"],
            messages=messages,
            temperature=0.7,
            max_tokens=100,
            api_key=model_config.get("api_key"),
            api_base=model_config.get("api_base"),
            api_version=model_config.get("api_version"),
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
                    "message": "Connection successful!",
                    "response": response.choices[0].message.content
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
            api_base=model_config.get("api_base"),
            api_version=model_config.get("api_version"),
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

# Run the server
if __name__ == "__main__":
    port = int(os.getenv("PORT", "54658"))
    logger.info(f"Starting OpenHands LiteLLM Proxy on port {port}...")
    logger.info(f"Available models: {', '.join(MODEL_CONFIG.keys())}")
    logger.info(f"Web UI available at http://localhost:{port}")
    uvicorn.run(app, host="0.0.0.0", port=port)