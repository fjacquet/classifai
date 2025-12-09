"""
Tests for MIME type and metadata rule conditions in the rules engine.

Tests the two-phase rule matching system with early rules (filename/path)
and full rules (MIME type, metadata).
"""

from pathlib import Path

import pytest

from classifai.core.rules import (
    RulesEngine,
    apply_early_rules,
    apply_full_rules,
)
from classifai.core.types import FileContext


@pytest.fixture
def sample_categories() -> list[str]:
    """Sample categories for testing."""
    return ["Documents PDF", "Images", "Factures", "Contrats"]


@pytest.fixture
def base_context(tmp_path: Path, sample_categories: list[str]) -> FileContext:
    """Create a base FileContext for testing."""
    test_file = tmp_path / "test.pdf"
    test_file.write_text("dummy content")

    return FileContext(
        source_path=test_file,
        destination_dir=tmp_path / "dest",
        rename_files=False,
        use_vision=False,
        language_subfolders=True,
        categories=sample_categories,
    )


class TestRulesEngineSeparation:
    """Tests for rule separation into early and full rules."""

    def test_early_rules_only_filename_path(self):
        """Test that rules with only filename/path are classified as early."""
        rules = [
            {
                "name": "Invoice PDF",
                "conditions": [{"type": "filename", "pattern": "invoice_*.pdf"}],
                "action": {"type": "categorize", "category": "Factures"},
            },
            {
                "name": "Path based",
                "conditions": [{"type": "path", "pattern": "*/invoices/*"}],
                "action": {"type": "categorize", "category": "Factures"},
            },
        ]

        engine = RulesEngine(rules)

        assert len(engine.early_rules) == 2
        assert len(engine.full_rules) == 0

    def test_full_rules_with_mime_type(self):
        """Test that rules with mime_type are classified as full."""
        rules = [
            {
                "name": "All PDFs",
                "conditions": [{"type": "mime_type", "pattern": "application/pdf"}],
                "action": {"type": "categorize", "category": "Documents PDF"},
            },
        ]

        engine = RulesEngine(rules)

        assert len(engine.early_rules) == 0
        assert len(engine.full_rules) == 1

    def test_full_rules_with_metadata(self):
        """Test that rules with metadata are classified as full."""
        rules = [
            {
                "name": "UBS Invoices",
                "conditions": [
                    {"type": "metadata", "field": "author", "pattern": "UBS", "match": "contains"},
                ],
                "action": {"type": "categorize", "category": "Factures"},
            },
        ]

        engine = RulesEngine(rules)

        assert len(engine.early_rules) == 0
        assert len(engine.full_rules) == 1

    def test_mixed_conditions_classified_as_full(self):
        """Test that rules with both early and full conditions are full."""
        rules = [
            {
                "name": "PDF with author",
                "conditions": [
                    {"type": "filename", "pattern": "*.pdf"},
                    {"type": "mime_type", "pattern": "application/pdf"},
                ],
                "action": {"type": "categorize", "category": "Documents PDF"},
            },
        ]

        engine = RulesEngine(rules)

        assert len(engine.early_rules) == 0
        assert len(engine.full_rules) == 1


class TestMatchCategoryEarly:
    """Tests for early rule matching (filename/path only)."""

    def test_filename_pattern_match(self, tmp_path: Path):
        """Test filename pattern matching."""
        rules = [
            {
                "name": "Invoice PDF",
                "conditions": [{"type": "filename", "pattern": "invoice_*.pdf"}],
                "action": {"type": "categorize", "category": "Factures"},
            },
        ]
        engine = RulesEngine(rules)

        test_file = tmp_path / "invoice_2024.pdf"
        test_file.touch()

        result = engine.match_category_early(test_file)
        assert result == "Factures"

    def test_filename_pattern_no_match(self, tmp_path: Path):
        """Test filename pattern not matching."""
        rules = [
            {
                "name": "Invoice PDF",
                "conditions": [{"type": "filename", "pattern": "invoice_*.pdf"}],
                "action": {"type": "categorize", "category": "Factures"},
            },
        ]
        engine = RulesEngine(rules)

        test_file = tmp_path / "receipt_2024.pdf"
        test_file.touch()

        result = engine.match_category_early(test_file)
        assert result is None

    def test_path_pattern_match(self, tmp_path: Path):
        """Test path pattern matching."""
        invoices_dir = tmp_path / "documents" / "invoices"
        invoices_dir.mkdir(parents=True)
        test_file = invoices_dir / "test.pdf"
        test_file.touch()

        rules = [
            {
                "name": "Invoices folder",
                "conditions": [{"type": "path", "pattern": "*invoices*"}],
                "action": {"type": "categorize", "category": "Factures"},
            },
        ]
        engine = RulesEngine(rules)

        result = engine.match_category_early(test_file)
        assert result == "Factures"


class TestMatchCategoryFull:
    """Tests for full rule matching (MIME type, metadata)."""

    def test_exact_mime_type_match(self, base_context: FileContext):
        """Test exact MIME type matching."""
        rules = [
            {
                "name": "PDF documents",
                "conditions": [{"type": "mime_type", "pattern": "application/pdf"}],
                "action": {"type": "categorize", "category": "Documents PDF"},
            },
        ]
        engine = RulesEngine(rules)

        context = base_context.model_copy(update={"mime_type": "application/pdf"})

        result = engine.match_category_full(context)
        assert result == "Documents PDF"

    def test_mime_type_prefix_match(self, base_context: FileContext):
        """Test MIME type prefix matching with wildcard."""
        rules = [
            {
                "name": "All images",
                "conditions": [{"type": "mime_type", "pattern": "image/*"}],
                "action": {"type": "categorize", "category": "Images"},
            },
        ]
        engine = RulesEngine(rules)

        context = base_context.model_copy(update={"mime_type": "image/png"})

        result = engine.match_category_full(context)
        assert result == "Images"

    def test_mime_type_prefix_no_match(self, base_context: FileContext):
        """Test MIME type prefix not matching different type."""
        rules = [
            {
                "name": "All images",
                "conditions": [{"type": "mime_type", "pattern": "image/*"}],
                "action": {"type": "categorize", "category": "Images"},
            },
        ]
        engine = RulesEngine(rules)

        context = base_context.model_copy(update={"mime_type": "application/pdf"})

        result = engine.match_category_full(context)
        assert result is None

    def test_metadata_contains_match(self, base_context: FileContext):
        """Test metadata contains matching."""
        rules = [
            {
                "name": "UBS documents",
                "conditions": [
                    {"type": "metadata", "field": "author", "pattern": "UBS", "match": "contains"},
                ],
                "action": {"type": "categorize", "category": "Factures"},
            },
        ]
        engine = RulesEngine(rules)

        context = base_context.model_copy(
            update={"metadata": {"author": "UBS Switzerland AG"}}
        )

        result = engine.match_category_full(context)
        assert result == "Factures"

    def test_metadata_exact_match(self, base_context: FileContext):
        """Test metadata exact matching."""
        rules = [
            {
                "name": "Specific author",
                "conditions": [
                    {"type": "metadata", "field": "author", "pattern": "John Doe", "match": "exact"},
                ],
                "action": {"type": "categorize", "category": "Contrats"},
            },
        ]
        engine = RulesEngine(rules)

        context = base_context.model_copy(update={"metadata": {"author": "john doe"}})

        result = engine.match_category_full(context)
        assert result == "Contrats"

    def test_metadata_startswith_match(self, base_context: FileContext):
        """Test metadata startswith matching."""
        rules = [
            {
                "name": "Invoice titles",
                "conditions": [
                    {"type": "metadata", "field": "title", "pattern": "Invoice", "match": "startswith"},
                ],
                "action": {"type": "categorize", "category": "Factures"},
            },
        ]
        engine = RulesEngine(rules)

        context = base_context.model_copy(
            update={"metadata": {"title": "Invoice #12345 - January 2024"}}
        )

        result = engine.match_category_full(context)
        assert result == "Factures"

    def test_metadata_endswith_match(self, base_context: FileContext):
        """Test metadata endswith matching."""
        rules = [
            {
                "name": "Contract files",
                "conditions": [
                    {"type": "metadata", "field": "title", "pattern": "Contract", "match": "endswith"},
                ],
                "action": {"type": "categorize", "category": "Contrats"},
            },
        ]
        engine = RulesEngine(rules)

        context = base_context.model_copy(
            update={"metadata": {"title": "Employment Contract"}}
        )

        result = engine.match_category_full(context)
        assert result == "Contrats"

    def test_metadata_glob_match(self, base_context: FileContext):
        """Test metadata glob pattern matching."""
        rules = [
            {
                "name": "Invoice files",
                "conditions": [
                    {"type": "metadata", "field": "title", "pattern": "*invoice*", "match": "glob"},
                ],
                "action": {"type": "categorize", "category": "Factures"},
            },
        ]
        engine = RulesEngine(rules)

        context = base_context.model_copy(
            update={"metadata": {"title": "Monthly invoice statement"}}
        )

        result = engine.match_category_full(context)
        assert result == "Factures"

    def test_metadata_missing_field(self, base_context: FileContext):
        """Test metadata condition with missing field."""
        rules = [
            {
                "name": "Author required",
                "conditions": [
                    {"type": "metadata", "field": "author", "pattern": "John", "match": "contains"},
                ],
                "action": {"type": "categorize", "category": "Documents PDF"},
            },
        ]
        engine = RulesEngine(rules)

        context = base_context.model_copy(update={"metadata": {}})

        result = engine.match_category_full(context)
        assert result is None

    def test_combined_mime_and_metadata(self, base_context: FileContext):
        """Test combined MIME type and metadata conditions."""
        rules = [
            {
                "name": "UBS PDF",
                "conditions": [
                    {"type": "mime_type", "pattern": "application/pdf"},
                    {"type": "metadata", "field": "author", "pattern": "UBS", "match": "contains"},
                ],
                "action": {"type": "categorize", "category": "Factures"},
            },
        ]
        engine = RulesEngine(rules)

        context = base_context.model_copy(
            update={
                "mime_type": "application/pdf",
                "metadata": {"author": "UBS AG"},
            }
        )

        result = engine.match_category_full(context)
        assert result == "Factures"

    def test_combined_conditions_partial_match_fails(self, base_context: FileContext):
        """Test combined conditions require all to match."""
        rules = [
            {
                "name": "UBS PDF",
                "conditions": [
                    {"type": "mime_type", "pattern": "application/pdf"},
                    {"type": "metadata", "field": "author", "pattern": "UBS", "match": "contains"},
                ],
                "action": {"type": "categorize", "category": "Factures"},
            },
        ]
        engine = RulesEngine(rules)

        # MIME matches but author doesn't
        context = base_context.model_copy(
            update={
                "mime_type": "application/pdf",
                "metadata": {"author": "Credit Suisse"},
            }
        )

        result = engine.match_category_full(context)
        assert result is None


class TestApplyEarlyRules:
    """Tests for apply_early_rules function."""

    def test_apply_early_rules_match(self, base_context: FileContext, tmp_path: Path):
        """Test apply_early_rules updates context on match."""
        # Create file with matching name
        test_file = tmp_path / "invoice_2024.pdf"
        test_file.touch()

        context = base_context.model_copy(update={"source_path": test_file})

        rules = [
            {
                "name": "Invoice PDF",
                "conditions": [{"type": "filename", "pattern": "invoice_*.pdf"}],
                "action": {"type": "categorize", "category": "Factures"},
            },
        ]
        engine = RulesEngine(rules)

        result = apply_early_rules(context, engine)

        assert result.rule_match_category == "Factures"

    def test_apply_early_rules_no_match(self, base_context: FileContext):
        """Test apply_early_rules returns unchanged context on no match."""
        rules = [
            {
                "name": "Invoice PDF",
                "conditions": [{"type": "filename", "pattern": "invoice_*.pdf"}],
                "action": {"type": "categorize", "category": "Factures"},
            },
        ]
        engine = RulesEngine(rules)

        result = apply_early_rules(base_context, engine)

        assert result.rule_match_category is None


class TestApplyFullRules:
    """Tests for apply_full_rules function."""

    def test_apply_full_rules_match(self, base_context: FileContext):
        """Test apply_full_rules updates context on match."""
        context = base_context.model_copy(
            update={
                "mime_type": "application/pdf",
                "metadata": {"author": "UBS"},
            }
        )

        rules = [
            {
                "name": "UBS PDF",
                "conditions": [
                    {"type": "mime_type", "pattern": "application/pdf"},
                    {"type": "metadata", "field": "author", "pattern": "UBS", "match": "contains"},
                ],
                "action": {"type": "categorize", "category": "Factures"},
            },
        ]
        engine = RulesEngine(rules)

        result = apply_full_rules(context, engine)

        assert result.rule_match_category == "Factures"

    def test_apply_full_rules_no_match(self, base_context: FileContext):
        """Test apply_full_rules returns unchanged context on no match."""
        context = base_context.model_copy(
            update={
                "mime_type": "image/png",
                "metadata": {},
            }
        )

        rules = [
            {
                "name": "PDF only",
                "conditions": [{"type": "mime_type", "pattern": "application/pdf"}],
                "action": {"type": "categorize", "category": "Documents PDF"},
            },
        ]
        engine = RulesEngine(rules)

        result = apply_full_rules(context, engine)

        assert result.rule_match_category is None


class TestLegacyCompatibility:
    """Tests for legacy API compatibility."""

    def test_match_category_returns_early_match(self, tmp_path: Path):
        """Test legacy match_category still works for early rules."""
        rules = [
            {
                "name": "Invoice PDF",
                "conditions": [{"type": "filename", "pattern": "invoice_*.pdf"}],
                "action": {"type": "categorize", "category": "Factures"},
            },
        ]
        engine = RulesEngine(rules)

        test_file = tmp_path / "invoice_2024.pdf"
        test_file.touch()

        result = engine.match_category(test_file)
        assert result == "Factures"
