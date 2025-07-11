"""
Tests for the parsing_module.
"""

import tempfile
from contextlib import contextmanager
from pathlib import Path

import openpyxl
import pytest
from PIL import ExifTags, Image

from classifai.parsing_module import (
    _convert_gps_to_decimal,
    parse_image,
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
        (tmp_path / "test.html").write_text("<h1>Title</h1><p>Paragraph</p>")
        (tmp_path / "test.rtf").write_text(
            "{\rtf1\ansi{\fonttbl\f0\fswiss Helvetica;}\f0\\pard\nThis is RTF text.\\par}"
        )
        (tmp_path / "test.eml").write_text(
            "From: sender@example.com\nTo: receiver@example.com\nSubject: Test\n\nThis is the body."
        )

        # Create a test xlsx file
        workbook = openpyxl.Workbook()
        sheet = workbook.active
        sheet["A1"] = "Hello"
        sheet["B2"] = "World"
        workbook.save(tmp_path / "test.xlsx")

        # Create a blank image
        Image.new("RGB", (60, 30), color="red").save(tmp_path / "blank.png")

        # Create an image with EXIF data
        img_with_exif = Image.new("RGB", (60, 30), color="blue")
        exif = img_with_exif.getexif()
        exif[ExifTags.Base.DateTimeOriginal] = "2025:07:11 10:30:00"
        exif[ExifTags.Base.GPSInfo] = {
            1: b"N",
            2: (48, 51, 29.99),
            3: b"E",
            4: (2, 17, 40.2),
        }
        img_with_exif.save(tmp_path / "exif.jpg", exif=exif.tobytes())

        yield tmp_path


def test_exif_extraction():
    """Tests that EXIF data is extracted correctly."""
    with create_test_files() as tmp_path:
        _, metadata = parse_image(str(tmp_path / "exif.jpg"))
        assert metadata["date"] == "2025:07:11 10:30:00"
        assert "location" in metadata


def test_gps_conversion():
    """Tests the GPS coordinate conversion."""
    lat = _convert_gps_to_decimal((48, 51, 30), "N")
    lon = _convert_gps_to_decimal((2, 17, 40), "E")
    assert lat == pytest.approx(48.858333)
    assert lon == pytest.approx(2.294444)
