"""
Configuration module for ClassifAI.

This module handles the loading of environment variables from a .env file
and provides centralized access to configuration settings.
"""

import os
from pathlib import Path

import yaml
from dotenv import load_dotenv
from loguru import logger

# Load environment variables from .env file
load_dotenv()

# --- Environment Variables ---
OLLAMA_MODEL_NAME = os.getenv("OLLAMA_MODEL_NAME", "gemma3n")
OLLAMA_EMBEDDING_MODEL_NAME = os.getenv("OLLAMA_EMBEDDING_MODEL_NAME", "mxbai-embed-large")
OLLAMA_API_URL = os.getenv("OLLAMA_API_URL", "http://localhost:11434")


# --- YAML Configuration ---
def load_yaml_config():
    """Loads configuration from the settings.yaml file."""
    config_path = Path("config/settings.yaml")
    if not config_path.exists():
        logger.warning("config/settings.yaml not found. Using default settings.")
        return {}
    try:
        with open(config_path) as f:
            return yaml.safe_load(f)
    except yaml.YAMLError as e:
        logger.error(f"Error parsing config/settings.yaml: {e}")
        return {}


# Load the YAML config
_yaml_config = load_yaml_config()

# --- Application Settings ---
GENERIC_TEXT_EXTENSIONS = _yaml_config.get("generic_text_extensions", [])
