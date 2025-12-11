"""
Configuration file for VirtualRAG server
"""

import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Server Configuration
SERVER_HOST = "0.0.0.0"  # Listen on all interfaces
SERVER_PORT = 8765
WEBSOCKET_PATH = "/ws"

# Authentication
PASSWORD = os.getenv("SERVER_PASSWORD", "changeme123")  # Set via .env file

# LLM Configuration
LLM_MODEL = os.getenv("LLM_MODEL", "llama2")  # Ollama model name
LLM_BASE_URL = os.getenv("LLM_BASE_URL", "http://localhost:11434")  # Ollama default
LLM_TEMPERATURE = 0.7
LLM_MAX_TOKENS = 2048

# RAG Configuration
VECTOR_DB_PATH = os.path.join(os.path.dirname(__file__), "RAG_Database", "chroma_db")
CHUNK_SIZE = 500
CHUNK_OVERLAP = 50
TOP_K_RESULTS = 3  # Number of similar documents to retrieve

# Document Configuration
SUPPORTED_EXTENSIONS = [".pdf", ".txt"]
MAX_FILE_SIZE_MB = 50

# Chat Configuration
MAX_CHAT_HISTORY = 100  # Maximum messages to keep in history
