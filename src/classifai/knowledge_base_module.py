"""
Knowledge Base module for ClassifAI.

This module handles loading and querying the debitors.yaml knowledge base.
"""

from pathlib import Path

import yaml
from loguru import logger


class KnowledgeBase:
    def __init__(self, config_path: Path = Path("config/debitors.yaml")):
        self.config_path = config_path
        self.debitors = self._load_debitors()

    def _load_debitors(self):
        """Loads the debitors from the YAML file."""
        if not self.config_path.exists():
            logger.info(
                f"Knowledge base file not found at {self.config_path}. Skipping rule-based classification."
            )
            return {}
        try:
            with open(self.config_path) as f:
                # Convert keys to lowercase for case-insensitive matching
                return {k.lower(): v for k, v in yaml.safe_load(f).items()}
        except yaml.YAMLError as e:
            logger.error(f"Error parsing debitors.yaml: {e}")
            return {}

    def match_category(self, text_content: str) -> str | None:
        """
        Matches text content against the knowledge base to find a category.

        Args:
            text_content (str): The text content of the document.

        Returns:
            str | None: The matched category or None if no match is found.
        """
        if not self.debitors:
            return None

        text_content_lower = text_content.lower()
        for debitor, category in self.debitors.items():
            if debitor in text_content_lower:
                logger.info(f"Found knowledge base match: '{debitor}' -> '{category}'")
                return category
        return None
