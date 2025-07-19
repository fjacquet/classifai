"""
Validation module for ClassifAI.

This module provides functions for validating and correcting data.
"""

import difflib
import sys
from typing import Any

from loguru import logger


def validate_category(category: str, valid_categories: list[str]) -> str:
    """
    Validates and corrects a category name by matching it to the closest valid category.

    Args:
        category: The category name to validate
        valid_categories: List of valid category names

    Returns:
        A valid category name from the list
    """
    if not category or not valid_categories:
        return category

    # If the category is already valid, return it
    if category in valid_categories:
        return category

    # Find the closest match using difflib
    matches = difflib.get_close_matches(category, valid_categories, n=1, cutoff=0.6)

    # If we found a close match, return it
    if matches:
        return matches[0]

    # If no close match, return the original (will be handled by translation)
    return category


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
