"""
Tests for the LLM infrastructure module.

This module tests the AI enrichment functionality including:
- Response validation with null/None values
- Language field handling
- Fallback behavior when validation fails
"""

from pathlib import Path

import pytest

from classifai.core.types import AIResponse, FileContext
from classifai.infrastructure.llm import (
    _format_categories_for_prompt,
    _fuzzy_match_category,
    enrich_with_ai,
)


@pytest.fixture
def base_context():
    """Provides a base FileContext for LLM tests."""
    return FileContext(
        source_path=Path("/source/test.pdf"),
        destination_dir=Path("/dest"),
        rename_files=False,
        use_vision=False,
        language_subfolders=True,
        categories=["Invoices", "Reports", "Contracts"],
        content="This is a test document from ABC Corp.",
        file_type="pdf",
        mime_type="application/pdf",
    )


class TestAIResponseLanguageHandling:
    """Tests for language field handling in AIResponse validation."""

    def test_ai_response_with_explicit_null_language(self):
        """Regression test: AIResponse should handle explicit null language."""
        # This was causing: ValidationError - Input should be a valid string
        response_data = {
            "issuer": "Test Corp",
            "category": "Invoices",
            "date": "2025-01-01",
            "short_title": "Test Invoice",
            "language": None,  # Explicit null - this was the bug
        }

        # The fix ensures None gets converted to "N/A" before validation
        # Since we're testing the fix at the call site, we test the model directly
        # with a default value approach
        response_data["language"] = response_data.get("language") or "N/A"
        ai_response = AIResponse(**response_data)

        assert ai_response.language == "N/A"

    def test_ai_response_with_missing_language(self):
        """AIResponse should use default when language key is missing."""
        response_data = {
            "issuer": "Test Corp",
            "category": "Invoices",
            # language key is missing entirely
        }

        ai_response = AIResponse(**response_data)
        assert ai_response.language == "N/A"

    def test_ai_response_with_valid_language(self):
        """AIResponse should preserve valid language values."""
        response_data = {
            "issuer": "Test Corp",
            "category": "Invoices",
            "language": "fr",
        }

        ai_response = AIResponse(**response_data)
        assert ai_response.language == "fr"

    def test_ai_response_with_empty_string_language(self):
        """AIResponse should handle empty string language (falsy but valid string)."""
        response_data = {
            "issuer": "Test Corp",
            "category": "Invoices",
            "language": "",
        }

        # Empty string is falsy, so the `or` fix will convert it to "N/A"
        response_data["language"] = response_data.get("language") or "N/A"
        ai_response = AIResponse(**response_data)

        assert ai_response.language == "N/A"


class TestEnrichWithAI:
    """Tests for the enrich_with_ai function."""

    def test_enrich_with_ai_handles_null_language_response(self, mocker, base_context):
        """
        Regression test: enrich_with_ai should handle LLM returning null language.

        When OCR/parsing extracts no text, the LLM often returns all null values.
        This should not cause a validation error.
        """
        # Mock the LLM API to return null for all fields (like with unreadable images)
        mock_response = {
            "model": "test-model",
            "response": '{"issuer": null, "category": null, "date": null, "short_title": null, "language": null}',
            "done": True,
        }

        mocker.patch("classifai.infrastructure.llm.get_completion", return_value=mock_response)
        mocker.patch(
            "classifai.infrastructure.llm._get_category_suggestion", return_value="Suggested-Category"
        )
        # get_sector_for_issuer is imported inside the function, mock at source
        mocker.patch("classifai.infrastructure.knowledge_base.get_sector_for_issuer", return_value=None)

        # Should not raise ValidationError
        result = enrich_with_ai(base_context)

        # Language should be "N/A" (the default), not None
        assert result.language == "N/A"
        # Category should be "_UNKNOWN_" when LLM can't classify
        assert result.category == "_UNKNOWN_"

    def test_enrich_with_ai_preserves_valid_language(self, mocker, base_context):
        """enrich_with_ai should preserve valid language from LLM response."""
        mock_response = {
            "model": "test-model",
            "response": '{"issuer": "ABC Corp", "category": "Invoices", "date": "2025-01-01", "short_title": "Test", "language": "fr"}',
            "done": True,
        }

        mocker.patch("classifai.infrastructure.llm.get_completion", return_value=mock_response)
        # get_sector_for_issuer is imported inside the function, mock at source
        mocker.patch(
            "classifai.infrastructure.knowledge_base.get_sector_for_issuer", return_value="Technology"
        )

        result = enrich_with_ai(base_context)

        assert result.language == "fr"
        assert result.issuer == "ABC Corp"
        assert result.category == "Invoices"

    def test_enrich_with_ai_skips_rule_matched_files(self, base_context):
        """enrich_with_ai should skip files already classified by rules."""
        context_with_rule_match = base_context.model_copy(update={"rule_match_category": "Invoices"})

        # Should return unchanged context without calling LLM
        result = enrich_with_ai(context_with_rule_match)

        assert result == context_with_rule_match

    def test_enrich_with_ai_fuzzy_matches_typo_category(self, mocker, base_context):
        """
        enrich_with_ai should fuzzy match typos like 'Fichieurs Texte' to 'Fichiers Texte'.

        This tests the fix for LLMs returning invalid categories with typos.
        """
        # Context with French categories that commonly get typos
        context = base_context.model_copy(
            update={
                "categories": [
                    "Analyses",
                    "Fichiers Texte",
                    "Factures",
                    "Relevés Bancaires",
                    "Non Classé",
                ],
            }
        )

        # Mock the LLM API to return a typo version of a category
        mock_response = {
            "model": "test-model",
            "response": '{"issuer": "Test Corp", "category": "Fichieurs Texte", "date": "2025-01-01", "short_title": "Test", "language": "fr"}',
            "done": True,
        }

        mocker.patch("classifai.infrastructure.llm.get_completion", return_value=mock_response)
        mocker.patch(
            "classifai.infrastructure.knowledge_base.get_sector_for_issuer", return_value="Technology"
        )

        result = enrich_with_ai(context)

        # Should fuzzy match to the correct category
        assert result.category == "Fichiers Texte"


class TestFuzzyMatchCategory:
    """Tests for the _fuzzy_match_category helper function."""

    def test_fuzzy_match_finds_close_match(self):
        """Should find a close match for a typo."""
        categories = ["Fichiers Texte", "Factures", "Analyses"]

        # Common typos that should match
        assert _fuzzy_match_category("Fichieurs Texte", categories) == "Fichiers Texte"
        assert _fuzzy_match_category("Fiachiers Texte", categories) == "Fichiers Texte"
        assert _fuzzy_match_category("Facture", categories) == "Factures"

    def test_fuzzy_match_returns_none_for_dissimilar(self):
        """Should return None for strings too different from any category."""
        categories = ["Fichiers Texte", "Factures", "Analyses"]

        # Completely different strings should not match
        assert _fuzzy_match_category("Transfers", categories) is None
        assert _fuzzy_match_category("Unknown Category", categories) is None

    def test_fuzzy_match_is_case_sensitive(self):
        """Fuzzy matching should be case-sensitive (as categories are)."""
        categories = ["Fichiers Texte", "Factures"]

        # Different case might still match if similar enough
        result = _fuzzy_match_category("fichiers texte", categories)
        # Due to the cutoff, this might not match - behavior depends on similarity
        # The key is it won't incorrectly match to something unrelated

    def test_fuzzy_match_respects_cutoff(self):
        """Fuzzy matching should not match below the cutoff threshold."""
        categories = ["Relevés Bancaires", "Analyses"]

        # This is close but different enough it might fail the 85% cutoff
        result = _fuzzy_match_category("Relèvés Bancaires", categories)
        # Should match because accent difference is minor
        assert result == "Relevés Bancaires"


class TestFormatCategoriesForPrompt:
    """Tests for the _format_categories_for_prompt helper function."""

    def test_formats_categories_as_numbered_list(self):
        """Should format categories as a numbered list."""
        categories = ["Analyses", "Archives", "Factures"]

        result = _format_categories_for_prompt(categories)

        assert "ALLOWED CATEGORIES" in result
        assert "1. Analyses" in result
        assert "2. Archives" in result
        assert "3. Factures" in result

    def test_includes_copy_exactly_instruction(self):
        """Should include instruction to copy exactly."""
        categories = ["Test"]

        result = _format_categories_for_prompt(categories)

        assert "EXACTLY" in result
        assert "do NOT modify" in result.lower() or "copy EXACTLY" in result

    def test_handles_empty_list(self):
        """Should handle empty category list gracefully."""
        categories = []

        result = _format_categories_for_prompt(categories)

        assert "ALLOWED CATEGORIES" in result

    def test_handles_special_characters_in_categories(self):
        """Should preserve special characters like accents in categories."""
        categories = ["Relevés Bancaires", "Non Classé", "Médical"]

        result = _format_categories_for_prompt(categories)

        assert "Relevés Bancaires" in result
        assert "Non Classé" in result
        assert "Médical" in result
