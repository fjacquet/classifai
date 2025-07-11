
"""
Parsing module for ClassifAI.

This module encapsulates the logic for extracting content from various file types
using a hierarchical strategy.
"""

import fitz  # PyMuPDF
import openpyxl
import pytesseract
import subprocess
from PIL import Image, UnidentifiedImageError
from PIL.ExifTags import TAGS
from docx import Document
from loguru import logger
from bs4 import BeautifulSoup
from striprtf.striprtf import rtf_to_text
import email

from classifai.config import GENERIC_TEXT_EXTENSIONS
from classifai.geocoding_module import get_location_from_gps


def _get_exif_data(image: Image) -> dict:
    """Extracts and decodes EXIF data from an image."""
    exif_data = {}
    if hasattr(image, "_getexif"):
        exif_info = image._getexif()
        if exif_info:
            for tag, value in exif_info.items():
                decoded = TAGS.get(tag, tag)
                exif_data[decoded] = value
    return exif_data


def _convert_gps_to_decimal(gps_coords, gps_ref):
    """Converts GPS coordinates from DMS to decimal degrees."""
    decimal_degrees = gps_coords[0] + (gps_coords[1] / 60) + (gps_coords[2] / 3600)
    if gps_ref in ["S", "W"]:
        decimal_degrees = -decimal_degrees
    return decimal_degrees


def parse_image(file_path: str) -> tuple[str, dict]:
    """
    Extracts text and metadata from an image file.

    Returns:
        A tuple containing the text content and a dictionary of metadata.
    """
    metadata = {}
    try:
        with Image.open(file_path) as img:
            # Extract text with OCR
            text = pytesseract.image_to_string(img)
            if not text.strip():
                logger.info(f"OCR returned no text for image: {file_path}")

            # Extract EXIF data
            exif_data = _get_exif_data(img)
            if "DateTimeOriginal" in exif_data:
                metadata["date"] = exif_data["DateTimeOriginal"]
            if "GPSInfo" in exif_data:
                gps_info = exif_data["GPSInfo"]
                lat = _convert_gps_to_decimal(gps_info[2], gps_info[1])
                lon = _convert_gps_to_decimal(gps_info[4], gps_info[3])
                metadata["location"] = get_location_from_gps(lat, lon)

            return text, metadata

    except (UnidentifiedImageError, ValueError):
        logger.warning(f"Cannot identify image file: {file_path}")
        return "", {}
    except pytesseract.TesseractNotFoundError:
        logger.error("Tesseract is not installed or not in your PATH.")
        raise
    except Exception as e:
        logger.error(f"Error performing OCR on image file {file_path}: {e}")
        return "", {}


def parse_pdf(file_path: str) -> tuple[str, dict]:
    """Extracts text content from a PDF file."""
    try:
        with fitz.open(file_path) as doc:
            text = "".join(page.get_text() for page in doc)
        if not text.strip():
            logger.info(f"PyMuPDF found no text in {file_path}. Trying pdftotext.")
            try:
                result = subprocess.run(
                    ["pdftotext", file_path, "-"],
                    capture_output=True,
                    text=True,
                    check=True,
                )
                return result.stdout, {}
            except (subprocess.CalledProcessError, FileNotFoundError) as e:
                logger.warning(
                    f"pdftotext fallback failed for {file_path}: {e}. "
                    "Ensure 'poppler-utils' is installed."
                )
                return "", {}
        return text, {}
    except Exception as e:
        logger.error(f"Error parsing PDF file {file_path}: {e}")
        return "", {}


def parse_docx(file_path: str) -> tuple[str, dict]:
    """Extracts text content from a DOCX file."""
    try:
        doc = Document(file_path)
        return "\n".join([paragraph.text for paragraph in doc.paragraphs]), {}
    except Exception as e:
        logger.error(f"Error parsing DOCX file {file_path}: {e}")
        return "", {}


def parse_xlsx(file_path: str) -> tuple[str, dict]:
    """Extracts text content from an XLSX file."""
    try:
        workbook = openpyxl.load_workbook(file_path)
        text = []
        for sheet in workbook.worksheets:
            for row in sheet.iter_rows():
                for cell in row:
                    if cell.value:
                        text.append(str(cell.value))
        return "\n".join(text), {}
    except Exception as e:
        logger.error(f"Error parsing XLSX file {file_path}: {e}")
        return "", {}


def parse_html(file_path: str) -> tuple[str, dict]:
    """Extracts text from an HTML file."""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            soup = BeautifulSoup(f, "html.parser")
            return soup.get_text(), {}
    except Exception as e:
        logger.error(f"Error parsing HTML file {file_path}: {e}")
        return "", {}


def parse_rtf(file_path: str) -> tuple[str, dict]:
    """Extracts text from an RTF file."""
    try:
        with open(file_path, "r") as f:
            return rtf_to_text(f.read()), {}
    except Exception as e:
        logger.error(f"Error parsing RTF file {file_path}: {e}")
        return "", {}


def parse_eml(file_path: str) -> tuple[str, dict]:
    """Extracts text from an EML file."""
    try:
        with open(file_path, "r") as f:
            msg = email.message_from_file(f)
            body = ""
            if msg.is_multipart():
                for part in msg.walk():
                    if part.get_content_type() == "text/plain":
                        body = part.get_payload(decode=True).decode()
                        break
            else:
                body = msg.get_payload(decode=True).decode()
            return body, {}
    except Exception as e:
        logger.error(f"Error parsing EML file {file_path}: {e}")
        return "", {}


def parse_generic_text(file_path: str) -> tuple[str, dict]:
    """Extracts content from a generic text file, trying various encodings."""
    encodings = ["utf-8", "latin-1", "iso-8859-1"]
    for encoding in encodings:
        try:
            with open(file_path, "r", encoding=encoding) as f:
                return f.read(), {}
        except UnicodeDecodeError:
            continue
    logger.warning(
        f"Could not decode file {file_path} with any of the default encodings."
    )
    return "", {}


def parse_with_pandoc(file_path: str) -> tuple[str, dict]:
    """Uses Pandoc as a fallback to convert a document to plain text."""
    try:
        result = subprocess.run(
            ["pandoc", file_path, "-t", "plain"],
            capture_output=True,
            text=True,
            check=True,
        )
        return result.stdout, {}
    except FileNotFoundError:
        logger.error(
            "Pandoc is not installed or not in your PATH. "
            "Please install it for advanced document parsing."
        )
        # Re-raise to avoid repeated attempts
        raise
    except subprocess.CalledProcessError as e:
        logger.warning(f"Pandoc failed to parse {file_path}: {e.stderr}")
        return "", {}


def get_parser(file_extension: str):
    """
    Returns the appropriate parser function for a given file extension using
    a hierarchical strategy.
    """
    specific_parsers = {
        ".pdf": parse_pdf,
        ".docx": parse_docx,
        ".xlsx": parse_xlsx,
        ".png": parse_image,
        ".jpg": parse_image,
        ".jpeg": parse_image,
        ".tiff": parse_image,
        ".bmp": parse_image,
        ".html": parse_html,
        ".htm": parse_html,
        ".rtf": parse_rtf,
        ".eml": parse_eml,
    }
    if file_extension in specific_parsers:
        return specific_parsers[file_extension]

    if file_extension in GENERIC_TEXT_EXTENSIONS:
        return parse_generic_text

    if not file_extension:
        return parse_generic_text

    # As a last resort for document-like files, try Pandoc
    pandoc_supported = [".odt", ".epub", ".md"]  # Add more as needed
    if file_extension in pandoc_supported:
        return parse_with_pandoc

    return None
