"""
Parsing module for ClassifAI.

This module encapsulates the logic for extracting content from various file types.
"""

import fitz  # PyMuPDF
import openpyxl
import pytesseract
from docx import Document
from loguru import logger
from PIL import Image, UnidentifiedImageError

from classifai.config import GENERIC_TEXT_EXTENSIONS


def parse_txt(file_path: str) -> str:
    """Extracts content from a plain text file."""
    return parse_generic_text(file_path)


def parse_pdf(file_path: str) -> str:
    """Extracts text content from a PDF file."""
    try:
        with fitz.open(file_path) as doc:
            return "".join(page.get_text() for page in doc)
    except Exception as e:
        logger.error(f"Error parsing PDF file {file_path}: {e}")
        return ""


def parse_docx(file_path: str) -> str:
    """Extracts text content from a DOCX file."""
    try:
        doc = Document(file_path)
        return "\n".join([paragraph.text for paragraph in doc.paragraphs])
    except Exception as e:
        logger.error(f"Error parsing DOCX file {file_path}: {e}")
        return ""


def parse_xlsx(file_path: str) -> str:
    """Extracts text content from an XLSX file."""
    try:
        workbook = openpyxl.load_workbook(file_path)
        text = []
        for sheet in workbook.worksheets:
            for row in sheet.iter_rows():
                for cell in row:
                    if cell.value:
                        text.append(str(cell.value))
        return "\n".join(text)
    except Exception as e:
        logger.error(f"Error parsing XLSX file {file_path}: {e}")
        return ""


def parse_image(file_path: str) -> str:
    """Extracts text from an image file using OCR."""
    try:
        text = pytesseract.image_to_string(Image.open(file_path))
        if not text.strip():
            logger.info(f"OCR returned no text for image: {file_path}")
        return text
    except UnidentifiedImageError:
        logger.warning(f"Cannot identify image file: {file_path}")
        return ""
    except pytesseract.TesseractNotFoundError:
        logger.error("Tesseract is not installed or not in your PATH.")
        # Re-raise the error as this is a fatal setup issue
        raise
    except Exception as e:
        logger.error(f"Error performing OCR on image file {file_path}: {e}")
        return ""


def parse_generic_text(file_path: str) -> str:
    """Extracts content from a generic text file, trying various encodings."""
    encodings = ["utf-8", "latin-1", "iso-8859-1"]
    for encoding in encodings:
        try:
            with open(file_path, encoding=encoding) as f:
                return f.read()
        except UnicodeDecodeError:
            continue
    logger.warning(f"Could not decode file {file_path} with any of the default encodings.")
    return ""


def get_parser(file_extension: str):
    """
    Returns the appropriate parser function for a given file extension using
    a hierarchical strategy.
    """
    # 1. Specific, high-priority parsers
    specific_parsers = {
        ".pdf": parse_pdf,
        ".docx": parse_docx,
        ".xlsx": parse_xlsx,
        ".png": parse_image,
        ".jpg": parse_image,
        ".jpeg": parse_image,
        ".tiff": parse_image,
        ".bmp": parse_image,
    }
    if file_extension in specific_parsers:
        return specific_parsers[file_extension]

    # 2. Generic text-based parser for a list of known extensions
    if file_extension in GENERIC_TEXT_EXTENSIONS:
        return parse_generic_text

    # 3. Fallback for files with no extension
    if not file_extension:
        return parse_generic_text

    # 4. No parser found
    return None
