"""
Tests for the archive parsing functions.
"""

import tarfile
import zipfile
from io import BytesIO

import pytest

from classifai.infrastructure.parsing import parse_archive


@pytest.fixture
def mock_zip_file(tmp_path):
    """
    Creates a temporary zip file for testing.
    """
    zip_path = tmp_path / "test.zip"
    with zipfile.ZipFile(zip_path, "w") as zf:
        zf.writestr("test.txt", "This is a text file.")
        zf.writestr("another.txt", "This is another text file.")
        zf.writestr("empty.txt", "")
    return zip_path


@pytest.fixture
def mock_tar_file(tmp_path):
    """
    Creates a temporary tar.gz file for testing.
    """
    tar_path = tmp_path / "test.tar.gz"
    with tarfile.open(tar_path, "w:gz") as tf:
        # Add a text file
        text_content = b"This is a text file in a tarball."
        tarinfo = tarfile.TarInfo(name="test.txt")
        tarinfo.size = len(text_content)
        tf.addfile(tarinfo, BytesIO(text_content))

        # Add another file
        more_text = b"More text here."
        tarinfo2 = tarfile.TarInfo(name="another.txt")
        tarinfo2.size = len(more_text)
        tf.addfile(tarinfo2, BytesIO(more_text))
    return tar_path


def test_parse_zip_archive(mock_zip_file):
    """
    Tests that the archive parser correctly extracts content from a zip file.
    """
    text, metadata = parse_archive(str(mock_zip_file))
    assert "--- File: test.txt ---" in text
    assert "--- File: another.txt ---" in text
    assert "--- File: empty.txt ---" in text
    assert metadata == {}


def test_parse_tar_archive(mock_tar_file):
    """
    Tests that the archive parser correctly extracts content from a tar.gz file.
    """
    text, metadata = parse_archive(str(mock_tar_file))
    assert "--- File: test.txt ---" in text
    assert "--- File: another.txt ---" in text
    assert metadata == {}


def test_parse_archive_bad_file():
    """
    Tests that the archive parser handles a non-archive file gracefully.
    """
    text, metadata = parse_archive("not_an_archive.txt")
    assert text == ""
    assert metadata == {}
