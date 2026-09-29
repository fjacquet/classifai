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


# Default supported file extensions
DEFAULT_SUPPORTED_EXTENSIONS = [
    # Documents
    ".pdf",
    ".docx",
    ".doc",
    ".txt",
    ".rtf",
    ".odt",
    ".md",
    # Spreadsheets
    ".xlsx",
    ".xls",
    ".ods",
    # Presentations
    ".pptx",
    ".ppt",
    ".odp",
    # Images (OCR)
    ".png",
    ".jpg",
    ".jpeg",
    ".tiff",
    ".bmp",
    # Email
    ".msg",
    ".eml",
    # Web
    ".html",
    # E-books
    ".epub",
    # Technical documentation (via Pandoc)
    ".rst",
    ".tex",
    ".latex",
    ".org",
]


@dataclass(frozen=True)
class AppConfig:
    """
    A centralized, immutable configuration object for the application.
    It is initialized once at startup.
    """

    # --- Environment-based settings ---
    ollama_model_name: str
    ollama_api_url: str
    ollama_vision_model_name: str

    # --- YAML-based settings ---
    settings: dict[str, Any]
    categories: list[str]
    rules: list[dict[str, Any]]
    sectors: list[str]
    sector_issuer_mapping: dict[str, Any]  # sector -> issuers, plus an 'aliases' dict

    # --- Path settings ---
    config_dir: Path = field(default=Path("config"))

    # --- Derived settings ---
    generic_text_extensions: list[str] = field(init=False)
    use_vision_model: bool = field(init=False)
    online_geocoding: bool = field(init=False)
    supported_extensions: list[str] = field(init=False)

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
        object.__setattr__(self, "online_geocoding", self.settings.get("online_geocoding", False))
        object.__setattr__(
            self,
            "supported_extensions",
            self.settings.get("supported_extensions", DEFAULT_SUPPORTED_EXTENSIONS),
        )


def load_app_config() -> AppConfig:
    """
    Loads all configurations and returns a frozen AppConfig object.
    """
    config_dir = Path("config")

    raw_settings = _load_yaml_file(config_dir / "settings.yaml")
    settings: dict[str, Any] = raw_settings if isinstance(raw_settings, dict) else {}

    raw_categories = _load_yaml_file(config_dir / "categories.yaml")
    categories: list[str] = raw_categories if isinstance(raw_categories, list) else []

    rules_data = _load_yaml_file(config_dir / "rules.yaml")
    rules = rules_data.get("rules", []) if isinstance(rules_data, dict) else []

    raw_sectors = _load_yaml_file(config_dir / "sectors.yaml")
    sectors: list[str] = raw_sectors if isinstance(raw_sectors, list) else []

    raw_mapping = _load_yaml_file(config_dir / "sector_issuer_mapping.yaml")
    sector_issuer_mapping: dict[str, Any] = raw_mapping if isinstance(raw_mapping, dict) else {}

    return AppConfig(
        # Env vars
        ollama_model_name=os.getenv("OLLAMA_MODEL_NAME", "gemma:2b"),
        ollama_api_url=os.getenv("OLLAMA_API_URL", "http://localhost:11434"),
        ollama_vision_model_name=os.getenv("OLLAMA_VISION_MODEL_NAME", "llava"),
        # YAML files
        settings=settings,
        categories=categories,
        rules=rules,
        sectors=sectors,
        sector_issuer_mapping=sector_issuer_mapping,
        config_dir=config_dir,
    )


# --- Singleton instance of the application configuration ---
app_config = load_app_config()
