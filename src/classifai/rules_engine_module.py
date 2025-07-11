"""
Rules Engine for ClassifAI.

This module implements a simple rules engine to classify files based on
their filename and path.
"""

import fnmatch
from pathlib import Path

import yaml
from loguru import logger

RULES_FILE_PATH = Path("config/rules.yaml")


class RulesEngine:
    """
    A simple rules engine that classifies files based on a set of rules
    defined in a YAML file.
    """

    def __init__(self):
        self.rules = self._load_rules()

    def _load_rules(self) -> list:
        """
        Loads the classification rules from the YAML file.
        """
        if not RULES_FILE_PATH.exists():
            logger.debug(f"Rules file not found at {RULES_FILE_PATH}, skipping.")
            return []

        try:
            with open(RULES_FILE_PATH) as f:
                data = yaml.safe_load(f)
                if data and "rules" in data:
                    logger.info(f"Successfully loaded {len(data['rules'])} rules.")
                    return data["rules"]
                return []
        except Exception as e:
            logger.error(f"Error loading rules from {RULES_FILE_PATH}: {e}")
            return []

    def match_category(self, file_path: str | Path) -> str | None:
        """
        Matches a file path against the loaded rules and returns a category
        if a rule is matched.

        Args:
            file_path (str | Path): The path to the file.

        Returns:
            str | None: The matched category or None if no rule matches.
        """
        if not self.rules:
            return None

        p_file_path = Path(file_path)
        file_name = p_file_path.name
        file_path_str = str(p_file_path.resolve())

        for rule in self.rules:
            if self._check_conditions(rule, file_name, file_path_str):
                action = rule.get("action", {})
                if action.get("type") == "categorize":
                    category = action.get("category")
                    logger.debug(
                        f"Matched rule '{rule.get('name')}' for file '{file_name}'. Category: {category}"
                    )
                    return category
        return None

    def _check_conditions(self, rule: dict, file_name: str, file_path: str) -> bool:
        """
        Checks if a file meets all conditions for a given rule.
        """
        conditions = rule.get("conditions", [])
        if not conditions:
            return False

        for condition in conditions:
            cond_type = condition.get("type")
            pattern = condition.get("pattern")

            if not pattern:
                continue

            if cond_type == "filename":
                if not fnmatch.fnmatch(file_name, pattern):
                    return False  # Condition not met
            elif cond_type == "path":
                if not fnmatch.fnmatch(file_path, pattern):
                    return False  # Condition not met
            else:
                logger.warning(f"Unknown condition type in rule '{rule.get('name')}': {cond_type}")
                return False

        return True  # All conditions met
