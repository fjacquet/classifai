"""
Tests for the knowledge_base_module.
"""

from pathlib import Path

import pytest
import yaml

from classifai.knowledge_base_module import KnowledgeBase


@pytest.fixture
def create_kb_file(tmp_path):
    """Creates a dummy debitors.yaml file."""
    config_dir = tmp_path / "config"
    config_dir.mkdir()
    debitors_file = config_dir / "debitors.yaml"
    debitors_data = {"Test Debitor": "Test Category", "Another Company": "Invoices"}
    with open(debitors_file, "w") as f:
        yaml.dump(debitors_data, f)
    return debitors_file


def test_kb_loading(create_kb_file):
    """Tests that the knowledge base loads and lowercases keys correctly."""
    kb = KnowledgeBase(config_path=create_kb_file)
    assert "test debitor" in kb.debitors
    assert kb.debitors["test debitor"] == "Test Category"
    assert "another company" in kb.debitors


def test_get_sector_for_issuer_exact_match(create_kb_file):
    """Tests a successful exact match for an issuer."""
    kb = KnowledgeBase(config_path=create_kb_file)
    sector = kb.get_sector_for_issuer("Test Debitor")
    assert sector == "Test Category"


def test_get_sector_for_issuer_partial_match(create_kb_file):
    """Tests a successful partial match for an issuer."""
    kb = KnowledgeBase(config_path=create_kb_file)
    sector = kb.get_sector_for_issuer("Some Company called Another Company Inc.")
    assert sector == "Invoices"


def test_get_sector_for_issuer_no_match(create_kb_file):
    """Tests when no match is found for an issuer."""
    kb = KnowledgeBase(config_path=create_kb_file)
    sector = kb.get_sector_for_issuer("Unknown Company")
    assert sector is None


def test_kb_file_not_found():
    """Tests that the knowledge base handles a missing file gracefully."""
    kb = KnowledgeBase(config_path=Path("non_existent_dir/debitors.yaml"))
    assert kb.debitors == {}
    assert kb.get_sector_for_issuer("any issuer") is None
