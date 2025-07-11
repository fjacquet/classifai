"""
Tests for the rules_engine_module.
"""

from pathlib import Path

import pytest
import yaml

from classifai.rules_engine_module import RulesEngine


@pytest.fixture
def mock_rules_file(tmp_path: Path) -> Path:
    """
    Creates a temporary rules YAML file for testing.
    """
    rules_content = {
        "rules": [
            {
                "name": "Invoice Rule",
                "conditions": [{"type": "filename", "pattern": "invoice_*.pdf"}],
                "action": {"type": "categorize", "category": "Invoices"},
            },
            {
                "name": "Receipt Rule",
                "conditions": [{"type": "filename", "pattern": "*receipt*.*"}],
                "action": {"type": "categorize", "category": "Receipts"},
            },
            {
                "name": "Project Rule",
                "conditions": [{"type": "path", "pattern": "*/projects/classifai/*"}],
                "action": {"type": "categorize", "category": "Work/Classifai"},
            },
            {
                "name": "Multi-condition Rule",
                "conditions": [
                    {"type": "filename", "pattern": "*.jpg"},
                    {"type": "path", "pattern": "*/personal/*"},
                ],
                "action": {"type": "categorize", "category": "Personal/Images"},
            },
        ]
    }
    rules_file = tmp_path / "rules.yaml"
    with open(rules_file, "w") as f:
        yaml.dump(rules_content, f)
    return rules_file


def test_load_rules(mocker, mock_rules_file: Path):
    """
    Tests that rules are loaded correctly from the YAML file.
    """
    mocker.patch("classifai.rules_engine_module.RULES_FILE_PATH", mock_rules_file)
    engine = RulesEngine()
    assert len(engine.rules) == 4
    assert engine.rules[0]["name"] == "Invoice Rule"


def test_no_rules_file(mocker):
    """
    Tests that the engine handles a missing rules file gracefully.
    """
    mocker.patch("classifai.rules_engine_module.RULES_FILE_PATH", Path("non_existent_file.yaml"))
    engine = RulesEngine()
    assert engine.rules == []


def test_match_category_filename(mocker, mock_rules_file: Path):
    """
    Tests category matching based on a filename rule.
    """
    mocker.patch("classifai.rules_engine_module.RULES_FILE_PATH", mock_rules_file)
    engine = RulesEngine()
    assert engine.match_category("invoice_123.pdf") == "Invoices"
    assert engine.match_category("my_receipt_image.jpg") == "Receipts"
    assert engine.match_category("document.txt") is None


def test_match_category_path(mocker, mock_rules_file: Path):
    """
    Tests category matching based on a path rule.
    """
    mocker.patch("classifai.rules_engine_module.RULES_FILE_PATH", mock_rules_file)
    engine = RulesEngine()
    project_file = Path.home() / "projects" / "classifai" / "main.py"
    assert engine.match_category(project_file) == "Work/Classifai"


def test_match_category_multi_condition(mocker, mock_rules_file: Path):
    """
    Tests a rule with multiple conditions.
    """
    mocker.patch("classifai.rules_engine_module.RULES_FILE_PATH", mock_rules_file)
    engine = RulesEngine()
    personal_image = Path.home() / "personal" / "vacation.jpg"
    work_image = Path.home() / "work" / "report.jpg"

    assert engine.match_category(personal_image) == "Personal/Images"
    assert engine.match_category(work_image) is None


def test_no_match(mocker, mock_rules_file: Path):
    """
    Tests that None is returned when no rules match.
    """
    mocker.patch("classifai.rules_engine_module.RULES_FILE_PATH", mock_rules_file)
    engine = RulesEngine()
    assert engine.match_category("random_file.zip") is None
