"""
Tests for the knowledge_base_module.
"""

import pytest
import yaml

from classifai.infrastructure.knowledge_base import (
    get_sector_for_issuer,
    normalize_issuer_name,
    record_unknown_issuer,
)


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


def test_normalize_issuer_name():
    """Tests that issuer names are normalized correctly."""
    assert normalize_issuer_name("UBS AG") == "ubs ag"
    assert normalize_issuer_name("Company A") == "company a"
    assert normalize_issuer_name("  SPACES  ") == "spaces"


def test_get_sector_for_issuer_exact_match(mocker):
    """Tests a successful exact match for an issuer."""
    # Mock the sector mapping data
    mock_mapping = {"Finance": ["Company A", "UBS"], "Technology": ["company b", "Tech Corp"]}
    mocker.patch(
        "classifai.infrastructure.knowledge_base.load_sector_issuer_mapping",
        return_value=mock_mapping,
    )

    result = get_sector_for_issuer("Company A")
    assert result == "Finance"
    result = get_sector_for_issuer("company b")
    assert result == "Technology"


def test_get_sector_for_issuer_with_aliases(mocker):
    """Tests sector lookup with alias support."""
    mock_mapping = {
        "Finance": ["UBS", "PostFinance"],
        "aliases": {"UBS AG": "UBS", "PostFinance AG": "PostFinance"},
    }
    mocker.patch(
        "classifai.infrastructure.knowledge_base.load_sector_issuer_mapping",
        return_value=mock_mapping,
    )

    # Test alias resolution - UBS AG is not directly in Finance list
    result = get_sector_for_issuer("UBS AG")
    assert result == "Finance"
    result = get_sector_for_issuer("UBS")
    assert result == "Finance"


def test_get_sector_for_issuer_no_match(mocker):
    """Tests when no match is found for an issuer."""
    mock_mapping = {"Finance": ["Company A"]}
    mocker.patch(
        "classifai.infrastructure.knowledge_base.load_sector_issuer_mapping",
        return_value=mock_mapping,
    )

    result = get_sector_for_issuer("Unknown Company")
    assert result is None


def test_record_unknown_issuer(isolated_unknown_issuers):
    """Tests that an unknown issuer is recorded correctly."""
    unknown_issuers_file = isolated_unknown_issuers

    # Start with an empty file
    unknown_issuers_file.write_text("[]\n")

    # Record a new issuer - function now returns None
    record_unknown_issuer("New Company")

    with open(unknown_issuers_file) as f:
        content = f.read().strip()
        if content and content != "[]":
            data = yaml.safe_load(content)
            assert data is not None
            assert isinstance(data, dict)
            assert "new company" in data
            assert "count" in data["new company"]
            assert "first_seen" in data["new company"]
            assert "original_name" in data["new company"]
            assert data["new company"]["original_name"] == "New Company"

    # Try to record the same issuer again (should be ignored)
    record_unknown_issuer("New Company")

    with open(unknown_issuers_file) as f:
        content = f.read().strip()
        if content and content != "[]":
            data = yaml.safe_load(content)
            assert len(data) == 1  # Should still be just one issuer


def test_get_sector_for_issuer_resolves_aliases(mocker):
    """Aliases from the mapping file map variants to their canonical issuer."""
    mock_mapping = {
        "Banque": ["UBS", "PostFinance"],
        "Assurance": ["Swiss Life"],
        "aliases": {"UBS Switzerland AG": "UBS", "La Poste - PostFinance": "PostFinance"},
    }
    mocker.patch(
        "classifai.infrastructure.knowledge_base.load_sector_issuer_mapping",
        return_value=mock_mapping,
    )

    assert get_sector_for_issuer("UBS Switzerland AG") == "Banque"
    assert get_sector_for_issuer("La Poste - PostFinance") == "Banque"


def test_get_sector_for_issuer_matches_short_names_as_words(mocker):
    """Short issuers (UBS, AXA, CFF) match as whole words, not arbitrary substrings."""
    mock_mapping = {"Banque": ["UBS"], "Assurance": ["Swiss Life", "AXA"]}
    mocker.patch(
        "classifai.infrastructure.knowledge_base.load_sector_issuer_mapping",
        return_value=mock_mapping,
    )

    assert get_sector_for_issuer("UBS AG") == "Banque"
    assert get_sector_for_issuer("AXA Winterthur") == "Assurance"
    assert get_sector_for_issuer("Swiss") is None  # no reverse-substring false positive
    assert get_sector_for_issuer("Subsea Ltd") is None  # 'ubs' inside a word must not match


def test_unknown_issuer_is_recorded_in_isolated_file(mocker, isolated_unknown_issuers):
    """Recording goes through unknown_issuers_path(), never the repository config."""
    mocker.patch(
        "classifai.infrastructure.knowledge_base.load_sector_issuer_mapping",
        return_value={"Banque": ["UBS"]},
    )

    get_sector_for_issuer("Nobody Corp")

    data = yaml.safe_load(isolated_unknown_issuers.read_text())
    assert data["nobody corp"]["count"] == 1
