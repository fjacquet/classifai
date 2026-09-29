"""
Validation module for ClassifAI.

This module provides functions for validating and correcting data.
"""

from typing import Any

from classifai.core.rules import CONDITION_TYPES, METADATA_MATCH_TYPES
from classifai.exceptions import ConfigurationError


def validate_rules_against_categories(rules: list[dict[str, Any]], categories: list[str]) -> None:
    """
    Validates that all categories used in rules exist in the master categories list.

    Args:
        rules: The list of rules from the configuration.
        categories: The master list of valid categories.

    Raises:
        ConfigurationError: If a rule contains a category that is not in the master list.
    """
    valid_categories = set(categories)
    invalid_rules = []

    for rule in rules:
        rule_category = rule.get("action", {}).get("category")
        if rule_category and rule_category not in valid_categories:
            invalid_rules.append((rule.get("name", "Unnamed Rule"), rule_category))

    if invalid_rules:
        details = "\n".join(
            f"  - Rule '{name}' uses invalid category: '{cat}'" for name, cat in invalid_rules
        )
        raise ConfigurationError(
            "Found rules with invalid categories:\n"
            f"{details}\n"
            "Please correct the categories in 'config/rules.yaml' to match 'config/categories.yaml'.",
        )


def validate_rule_conditions(rules: list[dict[str, Any]]) -> None:
    """
    Validates that every rule condition uses a known type and metadata match type.

    Args:
        rules: The list of rules from the configuration.

    Raises:
        ConfigurationError: If a condition uses an unknown type or match type.
    """
    problems = []
    for rule in rules:
        name = rule.get("name", "Unnamed Rule")
        for condition in rule.get("conditions", []):
            cond_type = condition.get("type")
            if cond_type not in CONDITION_TYPES:
                problems.append(f"  - Rule '{name}' uses unknown condition type: '{cond_type}'")
            elif cond_type == "metadata" and condition.get("match", "contains") not in METADATA_MATCH_TYPES:
                problems.append(f"  - Rule '{name}' uses unknown match type: '{condition.get('match')}'")

    if problems:
        raise ConfigurationError("Found invalid rule conditions:\n" + "\n".join(problems))
