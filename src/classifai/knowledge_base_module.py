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

    def get_sector_for_issuer(self, issuer_name: str) -> str | None:
        """
        Finds the business sector for a given issuer name.

        Args:
            issuer_name (str): The name of the issuer to look up.

        Returns:
            The corresponding business sector or None if no match is found.
        """
        if not self.debitors or not issuer_name:
            return None

        issuer_lower = issuer_name.lower()
        # First, try for an exact match
        if issuer_lower in self.debitors:
            return self.debitors[issuer_lower]

        # If no exact match, try for a partial match (e.g., "amazon" in "amazon web services")
        for debitor, sector in self.debitors.items():
            if debitor in issuer_lower:
                logger.info(
                    f"Found partial knowledge base match: '{issuer_name}' contains '{debitor}' -> '{sector}'"
                )
                return sector
        return None
