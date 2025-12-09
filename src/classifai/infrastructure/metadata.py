"""
MIME detection and rich metadata extraction with graceful degradation.

This module provides functions for detecting file MIME types and extracting
rich metadata using python-magic and ExifTool. Both tools are optional -
the module degrades gracefully when they are unavailable.
"""

from pathlib import Path
from typing import Any

from loguru import logger
from tenacity import retry, stop_after_attempt, wait_exponential

# Feature flags for optional dependencies
_MAGIC_AVAILABLE = False
_EXIFTOOL_AVAILABLE = False

try:
    import magic

    _MAGIC_AVAILABLE = True
except ImportError:
    logger.warning("python-magic unavailable. Using extension-based MIME detection.")

try:
    import exiftool

    _EXIFTOOL_AVAILABLE = True
except ImportError:
    logger.warning("pyexiftool unavailable. Rich metadata extraction disabled.")


# Extension to MIME type mapping for fallback
_EXTENSION_TO_MIME: dict[str, str] = {
    # Documents
    ".pdf": "application/pdf",
    ".doc": "application/msword",
    ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    ".xls": "application/vnd.ms-excel",
    ".xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    ".ppt": "application/vnd.ms-powerpoint",
    ".pptx": "application/vnd.openxmlformats-officedocument.presentationml.presentation",
    ".odt": "application/vnd.oasis.opendocument.text",
    ".ods": "application/vnd.oasis.opendocument.spreadsheet",
    ".odp": "application/vnd.oasis.opendocument.presentation",
    ".rtf": "application/rtf",
    ".txt": "text/plain",
    ".csv": "text/csv",
    ".md": "text/markdown",
    ".html": "text/html",
    ".htm": "text/html",
    ".xml": "application/xml",
    ".json": "application/json",
    ".yaml": "application/x-yaml",
    ".yml": "application/x-yaml",
    # Images
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".png": "image/png",
    ".gif": "image/gif",
    ".bmp": "image/bmp",
    ".tiff": "image/tiff",
    ".tif": "image/tiff",
    ".webp": "image/webp",
    ".svg": "image/svg+xml",
    ".ico": "image/x-icon",
    ".heic": "image/heic",
    ".heif": "image/heif",
    # Audio
    ".mp3": "audio/mpeg",
    ".wav": "audio/wav",
    ".flac": "audio/flac",
    ".aac": "audio/aac",
    ".ogg": "audio/ogg",
    ".m4a": "audio/mp4",
    # Video
    ".mp4": "video/mp4",
    ".avi": "video/x-msvideo",
    ".mkv": "video/x-matroska",
    ".mov": "video/quicktime",
    ".wmv": "video/x-ms-wmv",
    ".webm": "video/webm",
    # Archives
    ".zip": "application/zip",
    ".tar": "application/x-tar",
    ".gz": "application/gzip",
    ".bz2": "application/x-bzip2",
    ".7z": "application/x-7z-compressed",
    ".rar": "application/vnd.rar",
    # Email
    ".eml": "message/rfc822",
    ".msg": "application/vnd.ms-outlook",
    # Other
    ".epub": "application/epub+zip",
    ".ppk": "application/x-putty-private-key",
}


# ExifTool tag to normalized key mapping
_TAG_MAPPING: dict[str, str] = {
    # PDF metadata
    "PDF:Author": "author",
    "PDF:Title": "title",
    "PDF:Subject": "subject",
    "PDF:Keywords": "keywords",
    "PDF:Creator": "creator_tool",
    "PDF:Producer": "producer",
    "PDF:CreateDate": "creation_date",
    "PDF:ModifyDate": "modification_date",
    # XMP metadata (common across formats)
    "XMP:Creator": "author",
    "XMP:Title": "title",
    "XMP:Subject": "subject",
    "XMP:Description": "description",
    "XMP:CreateDate": "creation_date",
    "XMP:ModifyDate": "modification_date",
    # EXIF metadata (images)
    "EXIF:DateTimeOriginal": "date",
    "EXIF:CreateDate": "creation_date",
    "EXIF:ModifyDate": "modification_date",
    "EXIF:Artist": "author",
    "EXIF:Copyright": "copyright",
    "EXIF:ImageDescription": "description",
    "EXIF:Make": "camera_make",
    "EXIF:Model": "camera_model",
    # IPTC metadata (images)
    "IPTC:By-line": "author",
    "IPTC:Headline": "title",
    "IPTC:Caption-Abstract": "description",
    "IPTC:Keywords": "keywords",
    "IPTC:DateCreated": "creation_date",
    "IPTC:City": "city",
    "IPTC:Country-PrimaryLocationName": "country",
    # Office document metadata
    "FlashPix:Title": "title",
    "FlashPix:Author": "author",
    "FlashPix:Subject": "subject",
    "FlashPix:Keywords": "keywords",
    "FlashPix:Comments": "comments",
    "FlashPix:CreateDate": "creation_date",
    "FlashPix:ModifyDate": "modification_date",
}


# Tags to skip (internal ExifTool metadata)
_SKIP_TAG_PREFIXES = ("ExifTool:", "SourceFile", "File:", "Composite:")


def get_mime_type(file_path: Path) -> str:
    """
    Detect the MIME type of a file.

    Uses python-magic if available for accurate content-based detection,
    otherwise falls back to extension-based detection.

    Args:
        file_path: Path to the file

    Returns:
        MIME type string (e.g., "application/pdf", "image/jpeg")
    """
    if _MAGIC_AVAILABLE:
        try:
            mime_type = magic.from_file(str(file_path), mime=True)
            if mime_type:
                logger.debug(f"Detected MIME type via magic: {mime_type} for {file_path.name}")
                return mime_type
        except Exception as e:
            logger.debug(f"magic.from_file failed for {file_path.name}: {e}")

    # Fallback to extension-based detection
    extension = file_path.suffix.lower()
    mime_type = _EXTENSION_TO_MIME.get(extension, "application/octet-stream")
    logger.debug(f"Using extension-based MIME type: {mime_type} for {file_path.name}")
    return mime_type


def _normalize_metadata(raw: dict[str, Any]) -> dict[str, Any]:
    """
    Normalize ExifTool tags to standard keys.

    Converts ExifTool's verbose tag names (e.g., "PDF:Author") to
    simple normalized keys (e.g., "author").

    Args:
        raw: Raw metadata dictionary from ExifTool

    Returns:
        Normalized metadata dictionary with standard keys
    """
    normalized: dict[str, Any] = {}

    for key, value in raw.items():
        # Skip internal ExifTool tags
        if any(key.startswith(prefix) for prefix in _SKIP_TAG_PREFIXES):
            continue

        # Skip empty values
        if value is None or value == "":
            continue

        # Map to normalized key if known
        if key in _TAG_MAPPING:
            norm_key = _TAG_MAPPING[key]
            # Only set if not already set (first value wins for duplicates)
            if norm_key not in normalized:
                normalized[norm_key] = value
        else:
            # Keep unknown tags with simplified key
            # Convert "Category:Tag" to just "tag" (lowercase)
            simple_key = key.split(":")[-1].lower() if ":" in key else key.lower()

            if simple_key not in normalized:
                normalized[simple_key] = value

    # Post-process keywords to list format
    if "keywords" in normalized and isinstance(normalized["keywords"], str):
        normalized["keywords"] = [k.strip() for k in normalized["keywords"].split(",") if k.strip()]

    return normalized


@retry(stop=stop_after_attempt(2), wait=wait_exponential(min=1, max=5))
def extract_rich_metadata(file_path: Path) -> dict[str, Any]:
    """
    Extract rich metadata from a file using ExifTool.

    Returns an empty dictionary if ExifTool is unavailable or extraction fails.
    Uses retry logic to handle transient failures.

    Args:
        file_path: Path to the file

    Returns:
        Dictionary of normalized metadata, or empty dict if unavailable
    """
    if not _EXIFTOOL_AVAILABLE:
        return {}

    try:
        with exiftool.ExifToolHelper() as et:
            result = et.get_metadata(str(file_path))
            if result and len(result) > 0:
                normalized = _normalize_metadata(result[0])
                logger.debug(f"Extracted {len(normalized)} metadata fields for {file_path.name}")
                return normalized
            return {}
    except Exception as e:
        logger.debug(f"ExifTool extraction failed for {file_path.name}: {e}")
        return {}


def merge_metadata(
    parser_metadata: dict[str, Any],
    exif_metadata: dict[str, Any],
) -> dict[str, Any]:
    """
    Intelligently merge metadata from parser and ExifTool.

    Merging strategy:
    - Non-empty values are preferred over empty ones
    - For overlapping keys, prefer the more specific/detailed value
    - ExifTool metadata generally has more detail for media files

    Args:
        parser_metadata: Metadata extracted by file parsers
        exif_metadata: Metadata extracted by ExifTool

    Returns:
        Merged metadata dictionary
    """
    merged: dict[str, Any] = {}

    # Start with parser metadata
    for key, value in parser_metadata.items():
        if value is not None and value != "" and value != []:
            merged[key] = value

    # Overlay ExifTool metadata (overwrites if non-empty)
    for key, value in exif_metadata.items():
        if value is None or value == "" or value == []:
            continue

        # If key doesn't exist or existing value is empty, use ExifTool value
        if key not in merged or merged[key] is None or merged[key] == "" or merged[key] == []:
            merged[key] = value
        else:
            # Both have values - prefer longer/more detailed string
            existing = merged[key]
            if isinstance(existing, str) and isinstance(value, str):
                # Prefer longer string (more detail)
                if len(value) > len(existing):
                    merged[key] = value
            elif isinstance(existing, list) and isinstance(value, list):
                # Merge lists, remove duplicates
                merged[key] = list(set(existing + value))
            # Otherwise keep existing value

    return merged


def is_magic_available() -> bool:
    """Check if python-magic is available."""
    return _MAGIC_AVAILABLE


def is_exiftool_available() -> bool:
    """Check if ExifTool is available."""
    return _EXIFTOOL_AVAILABLE
