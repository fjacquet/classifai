"""
Parsing module for ClassifAI.

This module encapsulates the logic for extracting content from various file types.
"""

import docx
import fitz  # PyMuPDF
import pytesseract
from loguru import logger
from PIL import Image


def parse_pdf(file_path: str) -> str:
    """
    Extracts text content from a PDF file.

    Args:
        file_path (str): The absolute path to the PDF file.

    Returns:
        str: The extracted text content, or an empty string if parsing fails.
    """
    try:
        with fitz.open(file_path) as doc:
            text = ""
            for page in doc:
                text += page.get_text()
            return text
    except Exception as e:
        logger.error(f"Error parsing PDF file {file_path}: {e}")
        return ""


def parse_txt(file_path: str) -> str:
    """
    Extracts content from a plain text file.

    Args:
        file_path (str): The absolute path to the text file.

    Returns:
        str: The file content, or an empty string if reading fails.
    """
    try:
        with open(file_path, encoding="utf-8") as f:
            return f.read()
    except Exception as e:
        logger.error(f"Error reading text file {file_path}: {e}")
        return ""


def parse_docx(file_path: str) -> str:
    """
    Extracts text content from a DOCX file.

    Args:
        file_path (str): The absolute path to the DOCX file.

    Returns:
        str: The extracted text content, or an empty string if parsing fails.
    """
    try:
        doc = docx.Document(file_path)
        return "\n".join([paragraph.text for paragraph in doc.paragraphs])
    except Exception as e:
        logger.error(f"Error parsing DOCX file {file_path}: {e}")
        return ""


def parse_image(file_path: str) -> str:
    """
    Extracts text from an image file using OCR.

    Args:
        file_path (str): The absolute path to the image file.

    Returns:
        str: The extracted text, or an empty string if OCR fails.
    """
    try:
        return pytesseract.image_to_string(Image.open(file_path))
    except Exception as e:
        logger.error(f"Error performing OCR on image file {file_path}: {e}")
        return ""


import openpyxl


def parse_xlsx(file_path: str) -> str:
    """
    Extracts text content from an XLSX file.

    Args:
        file_path (str): The absolute path to the XLSX file.

    Returns:
        str: The extracted text content from all cells.
    """
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


def get_parser(file_extension: str):
    """
    Returns the appropriate parser function for a given file extension.

    Args:
        file_extension (str): The file extension (e.g., ".pdf", ".txt").

    Returns:
        function: The parser function, or None if no parser is available.
    """
    parsers = {
        ".pdf": parse_pdf,
        ".txt": parse_txt,
        ".md": parse_txt,
        ".docx": parse_docx,
        ".png": parse_image,
        ".jpg": parse_image,
        ".jpeg": parse_image,
        ".xlsx": parse_xlsx,
    }
    return parsers.get(file_extension.lower())
