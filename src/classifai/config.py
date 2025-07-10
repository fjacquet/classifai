"""
Configuration module for ClassifAI.

This module handles the loading of environment variables from a .env file
and provides centralized access to configuration settings.
"""

import os

from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Ollama Configuration
OLLAMA_MODEL_NAME = os.getenv("OLLAMA_MODEL_NAME", "gemma3n")
OLLAMA_EMBEDDING_MODEL_NAME = os.getenv(
    "OLLAMA_EMBEDDING_MODEL_NAME", "mxbai-embed-large"
)
OLLAMA_API_URL = os.getenv("OLLAMA_API_URL", "http://localhost:11434")

