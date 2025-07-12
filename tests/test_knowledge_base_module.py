"""
Tests for the knowledge_base_module.
"""

from unittest.mock import patch

import pytest
import yaml

from classifai.config import _load_debitors
from classifai.infrastructure.knowledge import KnowledgeBase, record_unknown_issuer


@pytest.fixture
def debitors_data():
    """Provides sample debitors data."""
    return {
        "Company A": "Finance",
        "company b": "Technology",
        "Another Company Inc.": "Retail",
    }


@pytest.fixture
def debitors_with_aliases_data():
    """Provides sample debitors data with aliases."""
    return {
        "Company A": {"sector": "Finance", "aliases": ["companya", "a corp"]},
        "Company B": "Technology",
    }


def test_kb_loading(debitors_data):
    """Tests that the knowledge base loads and lowercases keys correctly."""
    debitors = _load_debitors(debitors_data)
    kb = KnowledgeBase(debitors=debitors)
    assert kb.debitors["company a"] == "Finance"
    assert kb.debitors["company b"] == "Technology"


def test_kb_loading_with_aliases(debitors_with_aliases_data):
    """Tests that the knowledge base loads aliases correctly."""
    debitors = _load_debitors(debitors_with_aliases_data)
    kb = KnowledgeBase(debitors=debitors)
    assert kb.debitors["companya"] == "Finance"
    assert kb.debitors["a corp"] == "Finance"
    assert kb.debitors["company b"] == "Technology"


def test_get_sector_for_issuer_exact_match(debitors_data):
    """Tests a successful exact match for an issuer."""
    debitors = _load_debitors(debitors_data)
    kb = KnowledgeBase(debitors=debitors)
    assert kb.get_sector_for_issuer("Company A") == "Finance"
    assert kb.get_sector_for_issuer("company b") == "Technology"


def test_get_sector_for_issuer_partial_match(debitors_data):
    """Tests a successful partial match for an issuer."""
    debitors = _load_debitors(debitors_data)
    kb = KnowledgeBase(debitors=debitors)
    assert kb.get_sector_for_issuer("Some Company called Another Company Inc.") == "Retail"


def test_get_sector_for_issuer_no_match(debitors_data):
    """Tests when no match is found for an issuer."""
    debitors = _load_debitors(debitors_data)
    kb = KnowledgeBase(debitors=debitors)
    assert kb.get_sector_for_issuer("Unknown Company") is None


def test_kb_file_not_found():
    """Tests that the knowledge base handles missing data gracefully."""
    kb = KnowledgeBase(debitors={})
    assert kb.get_sector_for_issuer("Any Issuer") is None


def test_record_unknown_issuer(tmp_path):
    """Tests that an unknown issuer and its sector are recorded exactly once."""
    unknown_issuers_file = tmp_path / "unknown_issuers.yaml"
    # Ensure the global path is patched for the test
    with patch("classifai.infrastructure.knowledge.UNKNOWN_ISSUERS_PATH", unknown_issuers_file):
        # Start with an empty file
        unknown_issuers_file.touch()

        # Record a new issuer
        record_unknown_issuer("New Company", "AI Sector")
        with open(unknown_issuers_file) as f:
            data = yaml.safe_load(f)
            assert len(data) == 1
            assert data[0] == {"issuer": "new company", "sector": "AI Sector"}

        # Try to record the same issuer again (should be ignored)
        record_unknown_issuer("New Company", "AI Sector")
        with open(unknown_issuers_file) as f:
            data = yaml.safe_load(f)
            assert len(data) == 1
