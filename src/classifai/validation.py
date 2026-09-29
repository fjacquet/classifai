"""
Validation module for ClassifAI.

This module provides functions for validating and correcting data.
"""

import sys
from typing import Any

from loguru import logger


def validate_rules_against_categories(rules: list[dict[str, Any]], categories: list[str]) -> None:
    """
    Validates that all categories used in rules exist in the master categories list.

    Args:
        rules: The list of rules from the configuration.
        categories: The master list of valid categories.

    Raises:
        SystemExit: If a rule contains a category that is not in the master list.
    """
    valid_categories = set(categories)
    invalid_rules = []

    for rule in rules:
        rule_category = rule.get("action", {}).get("category")
        if rule_category and rule_category not in valid_categories:
            invalid_rules.append((rule.get("name", "Unnamed Rule"), rule_category))

    if invalid_rules:
        logger.error("Configuration error: Found rules with invalid categories.")
        for rule_name, category in invalid_rules:
            logger.error(f"  - Rule '{rule_name}' uses invalid category: '{category}'")
        logger.error(
            "Please correct the categories in 'config/rules.yaml' to match 'config/categories.yaml'.",
        )
        sys.exit(1)

    logger.success("Rules configuration validated successfully.")
