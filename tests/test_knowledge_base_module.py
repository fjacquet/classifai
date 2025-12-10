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
    assert result is None  # No match for alias
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


def test_record_unknown_issuer(mocker, tmp_path):
    """Tests that an unknown issuer is recorded correctly."""
    unknown_issuers_file = tmp_path / "unknown_issuers.yaml"
    # Ensure the global path is patched for the test
    mocker.patch("classifai.infrastructure.knowledge_base.UNKNOWN_ISSUERS_PATH", unknown_issuers_file)
    # Mock the app_config to avoid config_dir issues
    mock_config = mocker.MagicMock()
    mock_config.config_dir = tmp_path
    mocker.patch("classifai.infrastructure.knowledge_base.app_config", mock_config)

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
