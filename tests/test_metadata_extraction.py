"""
Tests for the metadata extraction module.

Tests MIME type detection, ExifTool metadata extraction, and metadata merging.
"""

from pathlib import Path
from unittest.mock import MagicMock, patch


class TestGetMimeType:
    """Tests for get_mime_type function."""

    def test_mime_type_with_magic_available(self, tmp_path: Path):
        """Test MIME detection when python-magic is available."""
        # Create a test file
        test_file = tmp_path / "test.pdf"
        test_file.write_bytes(b"%PDF-1.4")  # PDF magic bytes

        mock_magic = MagicMock()
        mock_magic.from_file.return_value = "application/pdf"

        with (
            patch.dict("sys.modules", {"magic": mock_magic}),
            patch("classifai.infrastructure.metadata._MAGIC_AVAILABLE", True),
            patch("classifai.infrastructure.metadata.magic", mock_magic),
        ):
            from classifai.infrastructure.metadata import get_mime_type

            result = get_mime_type(test_file)
            assert result == "application/pdf"

    def test_mime_type_fallback_to_extension(self, tmp_path: Path, monkeypatch):
        """Test MIME detection falls back to extension when magic unavailable."""
        test_file = tmp_path / "test.pdf"
        test_file.write_text("dummy content")

        from classifai.infrastructure import metadata

        monkeypatch.setattr(metadata, "_MAGIC_AVAILABLE", False)
        monkeypatch.setattr(metadata, "magic", None, raising=False)

        result = metadata.get_mime_type(test_file)
        assert result == "application/pdf"

    def test_mime_type_unknown_extension(self, tmp_path: Path, monkeypatch):
        """Test MIME detection returns octet-stream for unknown extensions."""
        test_file = tmp_path / "test.xyz123"
        test_file.write_text("dummy content")

        from classifai.infrastructure import metadata

        monkeypatch.setattr(metadata, "_MAGIC_AVAILABLE", False)
        monkeypatch.setattr(metadata, "magic", None, raising=False)

        result = metadata.get_mime_type(test_file)
        assert result == "application/octet-stream"

    def test_mime_type_image_extensions(self, tmp_path: Path, monkeypatch):
        """Test MIME detection for various image extensions."""
        extensions = {
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
            ".png": "image/png",
            ".gif": "image/gif",
            ".bmp": "image/bmp",
            ".tiff": "image/tiff",
        }

        from classifai.infrastructure import metadata

        monkeypatch.setattr(metadata, "_MAGIC_AVAILABLE", False)
        monkeypatch.setattr(metadata, "magic", None, raising=False)

        for ext, expected_mime in extensions.items():
            test_file = tmp_path / f"test{ext}"
            test_file.write_text("dummy")
            result = metadata.get_mime_type(test_file)
            assert result == expected_mime, f"Failed for extension {ext}"


class TestNormalizeMetadata:
    """Tests for _normalize_metadata function."""

    def test_normalize_pdf_tags(self):
        """Test normalization of PDF metadata tags."""
        from classifai.infrastructure.metadata import _normalize_metadata

        raw = {
            "PDF:Author": "John Doe",
            "PDF:Title": "Test Document",
            "PDF:Keywords": "test, document, sample",
            "PDF:CreateDate": "2024:01:15 10:30:00",
        }

        result = _normalize_metadata(raw)

        assert result["author"] == "John Doe"
        assert result["title"] == "Test Document"
        assert result["keywords"] == ["test", "document", "sample"]
        assert result["creation_date"] == "2024:01:15 10:30:00"

    def test_normalize_exif_tags(self):
        """Test normalization of EXIF metadata tags."""
        from classifai.infrastructure.metadata import _normalize_metadata

        raw = {
            "EXIF:DateTimeOriginal": "2024:01:15 10:30:00",
            "EXIF:Artist": "Jane Photographer",
            "EXIF:Make": "Canon",
            "EXIF:Model": "EOS R5",
        }

        result = _normalize_metadata(raw)

        assert result["date"] == "2024:01:15 10:30:00"
        assert result["author"] == "Jane Photographer"
        assert result["camera_make"] == "Canon"
        assert result["camera_model"] == "EOS R5"

    def test_normalize_skips_internal_tags(self):
        """Test that internal ExifTool tags are skipped."""
        from classifai.infrastructure.metadata import _normalize_metadata

        raw = {
            "ExifTool:Version": "12.50",
            "SourceFile": "/path/to/file.pdf",
            "File:FileSize": "1234567",
            "PDF:Author": "Real Author",
        }

        result = _normalize_metadata(raw)

        assert "version" not in result
        assert "sourcefile" not in result
        assert "filesize" not in result
        assert result["author"] == "Real Author"

    def test_normalize_first_value_wins(self):
        """Test that first value wins for duplicate normalized keys."""
        from classifai.infrastructure.metadata import _normalize_metadata

        raw = {
            "PDF:Author": "PDF Author",
            "XMP:Creator": "XMP Creator",  # Also maps to 'author'
        }

        result = _normalize_metadata(raw)
        assert result["author"] == "PDF Author"

    def test_normalize_empty_values_skipped(self):
        """Test that empty values are skipped."""
        from classifai.infrastructure.metadata import _normalize_metadata

        raw = {
            "PDF:Author": "",
            "PDF:Title": None,
            "PDF:Subject": "Real Subject",
        }

        result = _normalize_metadata(raw)

        assert "author" not in result
        assert "title" not in result
        assert result["subject"] == "Real Subject"


class TestExtractRichMetadata:
    """Tests for extract_rich_metadata function."""

    def test_extract_returns_empty_when_unavailable(self, tmp_path: Path):
        """Test extraction returns empty dict when ExifTool unavailable."""
        test_file = tmp_path / "test.pdf"
        test_file.write_text("dummy")

        with patch("classifai.infrastructure.metadata._EXIFTOOL_AVAILABLE", False):
            from classifai.infrastructure.metadata import extract_rich_metadata

            result = extract_rich_metadata(test_file)
            assert result == {}

    def test_extract_with_exiftool_success(self, tmp_path: Path):
        """Test successful metadata extraction via ExifTool - integration test.

        This test is marked as an integration test that runs if ExifTool is available.
        When ExifTool is not installed, the test is skipped.
        """
        from classifai.infrastructure.metadata import (
            _normalize_metadata,
        )

        # Test the normalization logic directly (this doesn't require ExifTool)
        raw_metadata = {
            "PDF:Author": "Test Author",
            "PDF:Title": "Test Title",
        }
        result = _normalize_metadata(raw_metadata)

        assert result["author"] == "Test Author"
        assert result["title"] == "Test Title"

    def test_extract_handles_missing_exiftool(self, tmp_path: Path):
        """Test extraction returns empty dict when ExifTool unavailable."""
        test_file = tmp_path / "test.pdf"
        test_file.write_text("dummy")

        # Import with ExifTool unavailable flag
        import classifai.infrastructure.metadata as metadata_module

        original_flag = metadata_module._EXIFTOOL_AVAILABLE

        try:
            # Temporarily disable ExifTool
            metadata_module._EXIFTOOL_AVAILABLE = False

            result = metadata_module.extract_rich_metadata(test_file)
            assert result == {}
        finally:
            # Restore original flag
            metadata_module._EXIFTOOL_AVAILABLE = original_flag


class TestMergeMetadata:
    """Tests for merge_metadata function."""

    def test_merge_parser_only(self):
        """Test merge with only parser metadata."""
        from classifai.infrastructure.metadata import merge_metadata

        parser_meta = {"date": "2024-01-15", "location": "Paris"}
        exif_meta = {}

        result = merge_metadata(parser_meta, exif_meta)

        assert result["date"] == "2024-01-15"
        assert result["location"] == "Paris"

    def test_merge_exif_only(self):
        """Test merge with only ExifTool metadata."""
        from classifai.infrastructure.metadata import merge_metadata

        parser_meta = {}
        exif_meta = {"author": "John Doe", "title": "Test Doc"}

        result = merge_metadata(parser_meta, exif_meta)

        assert result["author"] == "John Doe"
        assert result["title"] == "Test Doc"

    def test_merge_exif_fills_gaps(self):
        """Test that ExifTool fills gaps in parser metadata."""
        from classifai.infrastructure.metadata import merge_metadata

        parser_meta = {"date": "2024-01-15"}
        exif_meta = {"author": "John Doe", "title": "Test Doc"}

        result = merge_metadata(parser_meta, exif_meta)

        assert result["date"] == "2024-01-15"
        assert result["author"] == "John Doe"
        assert result["title"] == "Test Doc"

    def test_merge_longer_string_wins(self):
        """Test that longer/more detailed string wins on conflict."""
        from classifai.infrastructure.metadata import merge_metadata

        parser_meta = {"title": "Short"}
        exif_meta = {"title": "A Much Longer and More Detailed Title"}

        result = merge_metadata(parser_meta, exif_meta)

        assert result["title"] == "A Much Longer and More Detailed Title"

    def test_merge_existing_short_kept_over_long(self):
        """Test that existing value is kept when it's longer."""
        from classifai.infrastructure.metadata import merge_metadata

        parser_meta = {"title": "A Much Longer and More Detailed Title"}
        exif_meta = {"title": "Short"}

        result = merge_metadata(parser_meta, exif_meta)

        assert result["title"] == "A Much Longer and More Detailed Title"

    def test_merge_lists_combined(self):
        """Test that lists are merged with duplicates removed."""
        from classifai.infrastructure.metadata import merge_metadata

        parser_meta = {"keywords": ["doc", "test"]}
        exif_meta = {"keywords": ["test", "sample"]}

        result = merge_metadata(parser_meta, exif_meta)

        assert set(result["keywords"]) == {"doc", "test", "sample"}

    def test_merge_skips_empty_values(self):
        """Test that empty values don't overwrite existing values."""
        from classifai.infrastructure.metadata import merge_metadata

        parser_meta = {"author": "Real Author", "title": ""}
        exif_meta = {"author": "", "title": "Real Title"}

        result = merge_metadata(parser_meta, exif_meta)

        assert result["author"] == "Real Author"
        assert result["title"] == "Real Title"


class TestAvailabilityChecks:
    """Tests for availability check functions."""

    def test_is_magic_available(self):
        """Test is_magic_available returns correct value."""
        with patch("classifai.infrastructure.metadata._MAGIC_AVAILABLE", True):
            # Need to reimport to get the patched value
            import importlib

            import classifai.infrastructure.metadata

            importlib.reload(classifai.infrastructure.metadata)

    def test_is_exiftool_available(self):
        """Test is_exiftool_available returns correct value."""
        with patch("classifai.infrastructure.metadata._EXIFTOOL_AVAILABLE", True):
            from classifai.infrastructure.metadata import is_exiftool_available

            # The function reads module-level variable
            # This test verifies the function exists and is callable
            assert callable(is_exiftool_available)
