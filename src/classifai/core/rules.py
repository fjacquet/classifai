"""
Core logic for the rules engine.

This module contains the pure functions for applying classification rules.
Supports two-phase matching: early rules (filename/path) and full rules (MIME/metadata).
"""

import fnmatch
from pathlib import Path
from typing import Any

from loguru import logger

from classifai.core.types import FileContext

# Condition types that can be evaluated without file parsing
_EARLY_CONDITION_TYPES = {"filename", "path"}

# Condition types that require file parsing (MIME type, metadata)
_FULL_CONDITION_TYPES = {"mime_type", "metadata"}


class RulesEngine:
    """
    A rules engine that classifies files based on a set of rules.

    Supports two-phase matching:
    - Early rules: Only use filename/path conditions (no parsing needed)
    - Full rules: Can use mime_type and metadata conditions (require parsing)
    """

    def __init__(self, rules: list[dict[str, Any]]):
        self.rules = rules
        self.early_rules: list[dict[str, Any]] = []
        self.full_rules: list[dict[str, Any]] = []

        # Separate rules into early and full categories
        for rule in self.rules:
            if self._is_early_rule(rule):
                self.early_rules.append(rule)
            else:
                self.full_rules.append(rule)

        if self.rules:
            logger.info(
                f"Loaded {len(self.rules)} rules: {len(self.early_rules)} early, {len(self.full_rules)} full"
            )

    def _is_early_rule(self, rule: dict[str, Any]) -> bool:
        """
        Determine if a rule can be evaluated early (without file parsing).

        A rule is "early" if all its conditions are filename or path based.
        """
        conditions = rule.get("conditions", [])
        for condition in conditions:
            cond_type = condition.get("type", "")
            if cond_type in _FULL_CONDITION_TYPES:
                return False
        return True

    def match_category_early(self, file_path: str | Path) -> str | None:
        """
        Match file against early rules (filename/path only).

        This can be called before file parsing for quick categorization
        of files that match simple pattern rules.

        Args:
            file_path: Path to the file

        Returns:
            Category string if matched, None otherwise
        """
        if not self.early_rules:
            return None

        p_file_path = Path(file_path)
        file_name = p_file_path.name
        file_path_str = str(p_file_path.resolve())

        for rule in self.early_rules:
            if self._check_conditions_early(rule, file_name, file_path_str):
                action = rule.get("action", {})
                if action.get("type") == "categorize":
                    category = action.get("category")
                    logger.debug(
                        f"Early matched rule '{rule.get('name')}' for '{file_name}'. Category: {category}",
                    )
                    return category
        return None

    def match_category_full(self, context: FileContext) -> str | None:
        """
        Match file against full rules (can use MIME type and metadata).

        This should be called after file parsing when FileContext has
        mime_type and metadata populated.

        Args:
            context: FileContext with mime_type and metadata populated

        Returns:
            Category string if matched, None otherwise
        """
        if not self.full_rules:
            return None

        file_name = context.source_path.name
        file_path_str = str(context.source_path.resolve())

        for rule in self.full_rules:
            if self._check_conditions_full(rule, file_name, file_path_str, context):
                action = rule.get("action", {})
                if action.get("type") == "categorize":
                    category = action.get("category")
                    logger.debug(
                        f"Full matched rule '{rule.get('name')}' for '{file_name}'. Category: {category}",
                    )
                    return category
        return None

    def match_category(self, file_path: str | Path) -> str | None:
        """
        Legacy method: Matches a file path against early rules only.

        For full rule matching with MIME/metadata, use match_category_full().

        Args:
            file_path: Path to the file

        Returns:
            Category string if matched, None otherwise
        """
        return self.match_category_early(file_path)

    def _check_conditions_early(self, rule: dict[str, Any], file_name: str, file_path: str) -> bool:
        """
        Check if a file meets all conditions for an early rule.
        Only evaluates filename and path conditions.
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
                    return False
            elif cond_type == "path":
                if not fnmatch.fnmatch(file_path, pattern):
                    return False
            else:
                # Unknown or full condition type in early check
                logger.warning(f"Unexpected condition type in early rule '{rule.get('name')}': {cond_type}")
                return False

        return True

    def _check_conditions_full(
        self,
        rule: dict[str, Any],
        file_name: str,
        file_path: str,
        context: FileContext,
    ) -> bool:
        """
        Check if a file meets all conditions for a full rule.
        Evaluates filename, path, mime_type, and metadata conditions.
        """
        conditions = rule.get("conditions", [])
        if not conditions:
            return False

        for condition in conditions:
            cond_type = condition.get("type")
            pattern = condition.get("pattern", "")

            if cond_type == "filename":
                if pattern and not fnmatch.fnmatch(file_name, pattern):
                    return False

            elif cond_type == "path":
                if pattern and not fnmatch.fnmatch(file_path, pattern):
                    return False

            elif cond_type == "mime_type":
                if not self._check_mime_condition(context.mime_type, pattern):
                    return False

            elif cond_type == "metadata":
                if not self._check_metadata_condition(context.metadata, condition):
                    return False

            else:
                logger.warning(f"Unknown condition type in rule '{rule.get('name')}': {cond_type}")
                return False

        return True

    def _check_mime_condition(self, mime_type: str, pattern: str) -> bool:
        """
        Check if a MIME type matches a pattern.

        Supports:
        - Exact match: "application/pdf"
        - Prefix match: "image/*" matches any image type
        """
        if not pattern:
            return True

        if pattern.endswith("/*"):
            # Prefix match (e.g., "image/*" matches "image/png")
            prefix = pattern[:-2]
            return mime_type.startswith(prefix + "/")
        # Exact match
        return mime_type == pattern

    def _check_metadata_condition(self, metadata: dict[str, Any], condition: dict[str, Any]) -> bool:
        """
        Check if metadata matches a condition.

        Condition format:
        {
            "type": "metadata",
            "field": "author",
            "pattern": "UBS",
            "match": "contains"  # exact|contains|startswith|endswith|glob
        }
        """
        field = condition.get("field", "")
        pattern = condition.get("pattern", "")
        match_type = condition.get("match", "contains")

        if not field or not pattern:
            return True

        # Get field value from metadata
        value = metadata.get(field)
        if value is None:
            return False

        # Convert to string for comparison
        value_str = str(value).lower()
        pattern_lower = pattern.lower()

        if match_type == "exact":
            return value_str == pattern_lower
        if match_type == "contains":
            return pattern_lower in value_str
        if match_type == "startswith":
            return value_str.startswith(pattern_lower)
        if match_type == "endswith":
            return value_str.endswith(pattern_lower)
        if match_type == "glob":
            return fnmatch.fnmatch(value_str, pattern_lower)
        logger.warning(f"Unknown match type: {match_type}")
        return False


def apply_early_rules(context: FileContext, rules_engine: RulesEngine) -> FileContext:
    """
    Apply early rules (filename/path only) to the file context.

    This should be called before file parsing.

    Args:
        context: The file context to process
        rules_engine: The rules engine to use for matching

    Returns:
        Updated FileContext with rule_match_category set if a rule matched
    """
    category = rules_engine.match_category_early(str(context.source_path.absolute()))
    if category:
        return context.model_copy(update={"rule_match_category": category})
    return context


def apply_full_rules(context: FileContext, rules_engine: RulesEngine) -> FileContext:
    """
    Apply full rules (including MIME/metadata) to the file context.

    This should be called after file parsing when mime_type and metadata
    are populated in the context.

    Args:
        context: The file context with mime_type and metadata populated
        rules_engine: The rules engine to use for matching

    Returns:
        Updated FileContext with rule_match_category set if a rule matched
    """
    category = rules_engine.match_category_full(context)
    if category:
        return context.model_copy(update={"rule_match_category": category})
    return context


def apply_rules(context: FileContext, rules_engine: RulesEngine) -> FileContext:
    """
    Legacy function: Apply early rules only.

    For two-phase matching, use apply_early_rules() and apply_full_rules().

    Args:
        context: The file context to process
        rules_engine: The rules engine to use for matching

    Returns:
        Updated FileContext with rule_match_category set if a rule matched
    """
    return apply_early_rules(context, rules_engine)
