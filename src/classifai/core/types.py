"""
Core data types for the functional pipeline in ClassifAI.

This module defines immutable data structures using frozen dataclasses,
ensuring that data is not modified during the classification process.
"""

from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field


class AIResponse(BaseModel):
    """
    Pydantic model for AI response structure.
    This ensures consistent typing and validation of AI results.
    """

    issuer: str | None = None
    category: str | None = None
    date: str | None = None
    short_title: str | None = None
    language: str = Field(default="N/A")
    category_suggestion: str | None = None  # For _UNKNOWN_ workflow


class FileContext(BaseModel):
    """
    A Pydantic model to hold all information about a file as it's processed.
    This promotes immutability, as each step of the pipeline returns a new
    or updated instance of this context.
    """

    # Configuration for immutability
    class Config:
        frozen = True

    # Required initialization fields
    source_path: Path
    destination_dir: Path
    rename_files: bool
    use_vision: bool
    language_subfolders: bool
    categories: list[str]

    # --- Fields populated during the pipeline ---
    content: str = ""
    file_type: str = ""
    mime_type: str = ""  # True MIME type from python-magic or extension fallback
    metadata: dict[str, Any] = Field(default_factory=dict)
    language: str = "N/A"
    category: str | None = None
    rule_match_category: str | None = None
    ai_results: dict[str, Any] = Field(default_factory=dict)
    issuer: str | None = None
    sector: str | None = None
    final_destination_path: Path | None = None
