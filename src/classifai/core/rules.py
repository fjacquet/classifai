"""
Core logic for the rules engine.

This module contains the pure functions for applying classification rules.
"""

import fnmatch
from pathlib import Path
from typing import Any

from loguru import logger
from returns.result import Result, Success

from classifai.core.types import FileContext


class RulesEngine:
    """
    A simple rules engine that classifies files based on a set of rules.
    The rules are passed in during initialization.
    """

    def __init__(self, rules: list[dict[str, Any]]):
        self.rules = rules
        if self.rules:
            logger.info(f"Successfully loaded {len(self.rules)} rules.")

    def match_category(self, file_path: str | Path) -> str | None:
        """
        Matches a file path against the loaded rules and returns a category
        if a rule is matched.
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


def apply_rules(context: FileContext, rules_engine: RulesEngine) -> Result[FileContext, str]:
    """
    Applies the rules engine to the file path.
    This is a pure function that returns an updated context in a Result.
    """
    category = rules_engine.match_category(str(context.source_path.absolute()))
    if category:
        updated_context = context.__class__(**{**context.__dict__, "rule_match_category": category})
        return Success(updated_context)
    return Success(context)
