"""Pure parsing logic for ClassifAI."""

from collections.abc import Callable

from classifai.config import app_config
from classifai.infrastructure.parsing import (
    parse_archive,
    parse_docx,
    parse_eml,
    parse_generic_text,
    parse_html,
    parse_image,
    parse_msg,
    parse_pdf,
    parse_rtf,
    parse_with_pandoc,
    parse_xlsx,
)


def get_parser(file_extension: str) -> Callable | None:
    """
    Returns the appropriate parser function for a given file extension using
    a hierarchical strategy. This is a pure function.
    """
    specific_parsers = {
        # Text & Documents
        ".pdf": parse_pdf,
        ".docx": parse_docx,
        ".xlsx": parse_xlsx,
        ".html": parse_html,
        ".htm": parse_html,
        ".rtf": parse_rtf,
        ".eml": parse_eml,
        ".msg": parse_msg,
        # Images
        ".png": parse_image,
        ".jpg": parse_image,
        ".jpeg": parse_image,
        ".tiff": parse_image,
        ".bmp": parse_image,
        # Archives
        ".zip": parse_archive,
        ".tar": parse_archive,
        ".gz": parse_archive,
        ".bz2": parse_archive,
        ".xz": parse_archive,
    }
    if file_extension in specific_parsers:
        return specific_parsers[file_extension]

    if file_extension in app_config.generic_text_extensions:
        return parse_generic_text

    if not file_extension:
        return parse_generic_text

    # As a last resort for document-like files, try Pandoc
    pandoc_supported = [
        # Current
        ".odt",      # OpenDocument Text
        ".epub",     # E-books
        ".md",       # Markdown
        # Presentations
        ".pptx",     # PowerPoint 2007+
        ".ppt",      # Legacy PowerPoint
        ".odp",      # OpenDocument Presentation
        # Technical documentation
        ".rst",      # reStructuredText
        ".tex",      # LaTeX
        ".latex",    # LaTeX (alt extension)
        # Wiki/markup formats
        ".wiki",     # MediaWiki
        ".org",      # Emacs Org-mode
        ".textile",  # Textile
    ]
    if file_extension in pandoc_supported:
        return parse_with_pandoc

    return None
