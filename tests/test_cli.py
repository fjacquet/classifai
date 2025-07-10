"""
Tests for the ClassifAI CLI.
"""

from contextlib import contextmanager
from pathlib import Path
import tempfile

import pytest
from typer.testing import CliRunner

from classifai.classifai_cli import app

runner = CliRunner()


@pytest.fixture
def setup_test_logger():
    """
    Initializes the logger for the tests.
    """
    from classifai.logging_module import setup_logger

    return setup_logger()


@contextmanager
def create_test_files_for_cli():
    """
    Creates test files in a temporary directory for CLI testing.
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        source_dir = Path(tmpdir) / "cli_source"
        source_dir.mkdir()
        (source_dir / "test.txt").write_text(
            "This is a text file for the CLI test."
        )
        (source_dir / "document.pdf").write_text(
            "This is a PDF for the CLI test."
        )  # Simplified for testing
        yield source_dir


def test_cli_dry_run(mocker, setup_test_logger):
    """
    Tests the CLI in dry-run mode.
    """
    with create_test_files_for_cli() as source_dir:
        # Mock the classification to avoid actual API calls
        mocker.patch(
            "classifai.classifai_cli.classify_content",
            return_value="Documents",
        )

        result = runner.invoke(app, ["--source-dir", str(source_dir)])

        assert result.exit_code == 0
        assert "Classification Preview" in result.stdout
        assert "test.txt" in result.stdout
        assert "document.pdf" in result.stdout
        assert "Documents" in result.stdout


def test_cli_move(mocker, setup_test_logger):
    """
    Tests the CLI in move mode.
    """
    with create_test_files_for_cli() as source_dir:
        dest_dir = source_dir.parent / "cli_dest"

        mocker.patch(
            "classifai.classifai_cli.classify_content",
            return_value="Documents",
        )

        result = runner.invoke(
            app,
            [
                "--source-dir",
                str(source_dir),
                "--destination-dir",
                str(dest_dir),
                "--mode",
                "move",
            ],
            input="y\n",
        )

        assert result.exit_code == 0
        assert (dest_dir / "Documents" / "test.txt").exists()
        assert not (source_dir / "test.txt").exists()