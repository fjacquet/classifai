"""
Tests for the parsing_module.
"""

import tempfile
from contextlib import contextmanager
from pathlib import Path

import openpyxl
from PIL import Image

from classifai.parsing_module import (
    get_parser,
    parse_generic_text,
    parse_image,
    parse_pdf,
    parse_txt,
    parse_xlsx,
)


@contextmanager
def create_test_files():
    """
    Creates a variety of test files in a temporary directory.
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        (tmp_path / "test.txt").write_text("This is a test text file.")
        (tmp_path / "test.log").write_text("This is a log file.")
        (tmp_path / "no_extension").write_text("File with no extension.")

        # Create a test xlsx file
        workbook = openpyxl.Workbook()
        sheet = workbook.active
        sheet["A1"] = "Hello"
        sheet["B2"] = "World"
        workbook.save(tmp_path / "test.xlsx")

        # Create a blank image
        Image.new("RGB", (60, 30), color="red").save(tmp_path / "blank.png")

        yield tmp_path


def test_parse_txt():
    """Tests the parse_txt function."""
    with create_test_files() as tmp_path:
        txt_file = tmp_path / "test.txt"
        content = parse_txt(str(txt_file))
        assert "This is a test text file." in content


def test_parse_xlsx():
    """Tests the parse_xlsx function."""
    with create_test_files() as tmp_path:
        xlsx_file = tmp_path / "test.xlsx"
        content = parse_xlsx(str(xlsx_file))
        assert "Hello" in content
        assert "World" in content


def test_image_parser_handles_no_text(mocker):
    """Tests that the image parser returns empty string for image with no text."""
    with create_test_files() as tmp_path:
        blank_image = tmp_path / "blank.png"
        # Mock tesseract to return nothing
        mocker.patch("pytesseract.image_to_string", return_value="")
        content = parse_image(str(blank_image))
        assert content == ""


def test_get_parser_hierarchical():
    """
    Tests the get_parser factory function's hierarchical logic.
    """
    # 1. Specific parsers
    assert get_parser(".pdf") == parse_pdf
    assert get_parser(".xlsx") == parse_xlsx
    assert get_parser(".png") == parse_image

    # 2. Generic text parser for extensions in the config list
    assert get_parser(".log") == parse_generic_text
    assert get_parser(".csv") == parse_generic_text

    # 3. Fallback for files with no extension
    assert get_parser("") == parse_generic_text

    # 4. No parser found
    assert get_parser(".xyz") is None
