"""
Configuration module for ClassifAI.

This module handles the loading of environment variables and YAML files,
providing a centralized, immutable configuration object for the application.
"""

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml
from dotenv import load_dotenv
from loguru import logger

# Load environment variables from .env file
load_dotenv()


def _load_yaml_file(path: Path) -> dict | list | None:
    """Safely loads a single YAML file."""
    if not path.exists():
        logger.warning(f"Configuration file not found: {path}")
        return None
    try:
        with open(path) as f:
            return yaml.safe_load(f)
    except yaml.YAMLError as e:
        logger.error(f"Error parsing YAML file {path}: {e}")
        return None


@dataclass(frozen=True)
class AppConfig:
    """
    A centralized, immutable configuration object for the application.
    It is initialized once at startup.
    """

    # --- Environment-based settings ---
    ollama_model_name: str
    ollama_embedding_model_name: str
    ollama_api_url: str
    ollama_vision_model_name: str

    # --- YAML-based settings ---
    settings: dict[str, Any]
    categories: list[str]
    rules: list[dict[str, Any]]
    debitors: dict[str, str]

    # --- Derived settings ---
    generic_text_extensions: list[str] = field(init=False)
    use_vision_model: bool = field(init=False)

    def __post_init__(self):
        """
        Initializes derived configuration fields after the main object is created.
        """
        # Use object.__setattr__ because the dataclass is frozen
        object.__setattr__(
            self,
            "generic_text_extensions",
            self.settings.get("generic_text_extensions", []),
        )
        object.__setattr__(self, "use_vision_model", self.settings.get("use_vision_model", False))


def _load_debitors(data: dict | None) -> dict[str, str]:
    """Loads debitors from the YAML data, handling aliases."""
    if not data:
        return {}

    debitors_map = {}
    for issuer, value in data.items():
        issuer_lower = issuer.lower()
        if isinstance(value, str):  # Simple format: Issuer: Sector
            debitors_map[issuer_lower] = value
        elif isinstance(value, dict):  # Complex format with aliases
            sector = value.get("sector")
            if sector:
                debitors_map[issuer_lower] = sector
                for alias in value.get("aliases", []):
                    debitors_map[alias.lower()] = sector
    return debitors_map


def load_app_config() -> AppConfig:
    """
    Loads all configurations and returns a frozen AppConfig object.
    """
    # Load YAML files
    settings = _load_yaml_file(Path("config/settings.yaml")) or {}
    categories = _load_yaml_file(Path("config/categories.yaml")) or []
    rules_data = _load_yaml_file(Path("config/rules.yaml"))
    debitors_data = _load_yaml_file(Path("config/debitors.yaml"))

    # Process YAML data
    rules = rules_data.get("rules", []) if isinstance(rules_data, dict) else []
    debitors = _load_debitors(debitors_data)

    return AppConfig(
        # Env vars
        ollama_model_name=os.getenv("OLLAMA_MODEL_NAME", "gemma3n"),
        ollama_embedding_model_name=os.getenv("OLLAMA_EMBEDDING_MODEL_NAME", "mxbai-embed-large"),
        ollama_api_url=os.getenv("OLLAMA_API_URL", "http://127.0.0.1:11434"),
        ollama_vision_model_name=os.getenv("OLLAMA_VISION_MODEL_NAME", "llava"),
        # YAML files
        settings=settings,
        categories=categories,
        rules=rules,
        debitors=debitors,
    )


# --- Singleton instance of the application configuration ---
app_config = load_app_config()
