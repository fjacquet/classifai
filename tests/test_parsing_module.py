"""
Tests for the parsing_module.
"""

from contextlib import contextmanager
from pathlib import Path
import tempfile

from faker import Faker
import pytest

from classifai.parsing_module import (
    get_parser,
    parse_docx,
    parse_image,
    parse_pdf,
    parse_txt,
    parse_xlsx,
)

fake = Faker()


import openpyxl


@contextmanager
def create_test_files():
    """
    Creates a variety of test files in a temporary directory.
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        (tmp_path / "test.txt").write_text("This is a test text file.")
        (tmp_path / "test.md").write_text("# This is a markdown file")

        # Create a test xlsx file
        workbook = openpyxl.Workbook()
        sheet = workbook.active
        sheet["A1"] = "Hello"
        sheet["B2"] = "World"
        workbook.save(tmp_path / "test.xlsx")

        yield tmp_path


def test_parse_txt():
    """
    Tests the parse_txt function.
    """
    with create_test_files() as tmp_path:
        txt_file = tmp_path / "test.txt"
        content = parse_txt(str(txt_file))
        assert "This is a test text file." in content


def test_parse_xlsx():
    """
    Tests the parse_xlsx function.
    """
    with create_test_files() as tmp_path:
        xlsx_file = tmp_path / "test.xlsx"
        content = parse_xlsx(str(xlsx_file))
        assert "Hello" in content
        assert "World" in content


def test_get_parser():
    """
    Tests the get_parser factory function.
    """
    assert get_parser(".pdf") == parse_pdf
    assert get_parser(".txt") == parse_txt
    assert get_parser(".md") == parse_txt
    assert get_parser(".docx") == parse_docx
    assert get_parser(".png") == parse_image
    assert get_parser(".jpg") == parse_image
    assert get_parser(".jpeg") == parse_image
    assert get_parser(".xlsx") == parse_xlsx
    assert get_parser(".xyz") is None