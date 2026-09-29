"""Tests for configuration validation."""

import pytest

from classifai.exceptions import ConfigurationError
from classifai.validation import validate_rule_conditions, validate_rules_against_categories


def test_valid_rules_pass():
    """Rules using known categories validate silently."""
    rules = [{"name": "r1", "action": {"category": "Factures"}}]
    validate_rules_against_categories(rules, ["Factures"])


def test_invalid_rule_category_raises():
    """Unknown categories raise ConfigurationError naming the rule."""
    rules = [{"name": "r1", "action": {"category": "Invoices"}}]

    with pytest.raises(ConfigurationError, match="r1.*Invoices"):
        validate_rules_against_categories(rules, ["Factures"])


def test_unknown_condition_type_raises():
    """Typos in condition types are reported instead of silently never matching."""
    rules = [{"name": "r1", "conditions": [{"type": "filname", "pattern": "*.pdf"}]}]

    with pytest.raises(ConfigurationError, match="filname"):
        validate_rule_conditions(rules)


def test_unknown_metadata_match_type_raises():
    """Unknown metadata match types are reported."""
    rules = [
        {"name": "r1", "conditions": [{"type": "metadata", "field": "a", "pattern": "b", "match": "regex"}]}
    ]

    with pytest.raises(ConfigurationError, match="regex"):
        validate_rule_conditions(rules)


def test_shipped_rules_are_valid():
    """The repository rules.yaml passes validation."""
    from classifai.config import app_config

    validate_rules_against_categories(app_config.rules, app_config.categories)
    validate_rule_conditions(app_config.rules)
