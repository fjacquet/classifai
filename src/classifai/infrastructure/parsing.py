"""Impure parsing functions for ClassifAI."""

import email
import functools
import subprocess
import tarfile
import zipfile
from email import policy
from email.message import EmailMessage
from typing import cast

import extract_msg

try:
    import fitz  # PyMuPDF
except ImportError:
    fitz = None

import openpyxl
import pytesseract
from bs4 import BeautifulSoup
from docx import Document
from loguru import logger
from PIL import Image, UnidentifiedImageError
from PIL.ExifTags import TAGS
from striprtf.striprtf import rtf_to_text

from classifai.infrastructure.geocoding import get_location_from_gps

SUBPROCESS_TIMEOUT = 60  # seconds, for pdftotext / pandoc
OCR_PREFERRED_LANGUAGES = ("fra", "eng", "deu")
OCR_MAX_PDF_PAGES = 3  # scanned PDFs: OCR the first pages only
OCR_DPI = 200


@functools.cache
def _ocr_languages() -> str | None:
    """Tesseract language string from the preferred languages that are installed."""
    try:
        installed = set(pytesseract.get_languages(config=""))
    except pytesseract.TesseractNotFoundError:
        return None
    available = [lang for lang in OCR_PREFERRED_LANGUAGES if lang in installed]
    return "+".join(available) or None


def _ocr(image: Image.Image) -> str:
    """OCR an image with the preferred languages."""
    return pytesseract.image_to_string(image, lang=_ocr_languages())


# --- Decorator for Exception Handling ---
def parsing_handler(func):
    """
    A decorator to handle common exceptions for parser functions.
    It logs errors and ensures the function returns a default value.
    """

    @functools.wraps(func)
    def wrapper(file_path: str, *args, **kwargs) -> tuple[str, dict]:
        try:
            return func(file_path, *args, **kwargs)
        except (UnidentifiedImageError, ValueError) as e:
            logger.warning(f"Cannot identify or process file '{file_path}': {e}")
        except pytesseract.TesseractNotFoundError:
            logger.error("Tesseract is not installed or not in your PATH.")
            raise  # Re-raise as this is a critical setup issue
        except FileNotFoundError:
            logger.error(f"File not found: {file_path}")
        except (zipfile.BadZipFile, tarfile.ReadError) as e:
            logger.error(f"Could not read archive {file_path}: {e}")
        except Exception as e:
            logger.error(f"An unexpected error occurred in '{func.__name__}' for file '{file_path}': {e}")
        return "", {}

    return wrapper


# --- Specific Parsers ---
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


@parsing_handler
def parse_image(file_path: str) -> tuple[str, dict]:
    """Extracts text and metadata from an image file."""
    metadata = {}
    with Image.open(file_path) as img:
        text = _ocr(img)
        if not text.strip():
            logger.info(f"OCR returned no text for image: {file_path}")

        exif_data = _get_exif_data(img)
        if "DateTimeOriginal" in exif_data:
            metadata["date"] = exif_data["DateTimeOriginal"]
        if "GPSInfo" in exif_data:
            gps_info = exif_data["GPSInfo"]
            lat = _convert_gps_to_decimal(gps_info[2], gps_info[1])
            lon = _convert_gps_to_decimal(gps_info[4], gps_info[3])
            metadata["location"] = get_location_from_gps(lat, lon)

        return text, metadata


def _pdftotext(file_path: str) -> str:
    """Text layer via poppler's pdftotext; empty if the tool is missing."""
    try:
        result = subprocess.run(
            ["pdftotext", file_path, "-"],
            capture_output=True,
            text=True,
            check=True,
            timeout=SUBPROCESS_TIMEOUT,
        )
    except FileNotFoundError:
        logger.warning("pdftotext is not installed; skipping it.")
        return ""
    return result.stdout


def _ocr_pdf_pages(doc) -> str:
    """Render the first pages of a scanned PDF and OCR them."""
    texts = []
    for page in doc.pages(0, min(OCR_MAX_PDF_PAGES, doc.page_count)):
        pix = page.get_pixmap(dpi=OCR_DPI)
        image = Image.frombytes("RGBA" if pix.alpha else "RGB", (pix.width, pix.height), pix.samples)
        texts.append(_ocr(image))
    return "\n\f".join(texts)


@parsing_handler
def parse_pdf(file_path: str) -> tuple[str, dict]:
    """Extracts text from a PDF: text layer first, OCR for scanned documents."""
    if not fitz:
        logger.warning("PyMuPDF (fitz) is not installed. Falling back to pdftotext.")
        return _pdftotext(file_path), {}

    with fitz.open(file_path) as doc:
        text = "\n\f".join(page.get_text() for page in doc)
        if text.strip():
            return text, {}
        text = _pdftotext(file_path)
        if text.strip():
            return text, {}
        logger.info(f"No text layer in {file_path}; running OCR.")
        return _ocr_pdf_pages(doc), {}


@parsing_handler
def parse_docx(file_path: str) -> tuple[str, dict]:
    """Extracts text content from a DOCX file."""
    doc = Document(file_path)
    return "\n".join([paragraph.text for paragraph in doc.paragraphs]), {}


@parsing_handler
def parse_xlsx(file_path: str) -> tuple[str, dict]:
    """Extracts text content from an XLSX file."""
    workbook = openpyxl.load_workbook(file_path, read_only=True, data_only=True)
    try:
        text = [
            str(value)
            for sheet in workbook.worksheets
            for row in sheet.iter_rows(values_only=True)
            for value in row
            if value
        ]
    finally:
        workbook.close()
    return "\n".join(text), {}


@parsing_handler
def parse_html(file_path: str) -> tuple[str, dict]:
    """Extracts text from an HTML file, honouring its declared charset."""
    with open(file_path, "rb") as f:
        soup = BeautifulSoup(f.read(), "html.parser")
    return soup.get_text(), {}


@parsing_handler
def parse_rtf(file_path: str) -> tuple[str, dict]:
    """Extracts text from an RTF file (7-bit ASCII with escapes; tolerate stray bytes)."""
    with open(file_path, encoding="cp1252", errors="replace") as f:
        return rtf_to_text(f.read()), {}


@parsing_handler
def parse_eml(file_path: str) -> tuple[str, dict]:
    """Extracts headers and body (plain text preferred, HTML otherwise) from an EML file."""
    with open(file_path, "rb") as f:
        # policy.default makes the parser build EmailMessage objects (with get_body)
        msg = cast(EmailMessage, email.message_from_binary_file(f, policy=policy.default))

    metadata = {
        "subject": str(msg.get("Subject", "")),
        "sender": str(msg.get("From", "")),
        "date": str(msg.get("Date", "")),
        "to": str(msg.get("To", "")),
    }
    body = ""
    part = msg.get_body(preferencelist=("plain", "html"))
    if part is not None:
        body = part.get_content()
        if part.get_content_type() == "text/html":
            body = BeautifulSoup(body, "html.parser").get_text()

    header = f"Subject: {metadata['subject']}\nFrom: {metadata['sender']}\nDate: {metadata['date']}\n\n"
    return header + body, metadata


@parsing_handler
def parse_msg(file_path: str) -> tuple[str, dict]:
    """Extracts text and metadata from an MSG file."""
    with extract_msg.openMsg(file_path) as msg:
        # Extract basic content
        body = msg.body or ""

        # Extract metadata
        metadata = {
            "subject": msg.subject or "",
            "sender": msg.sender or "",
            "date": msg.date or "",
            "to": msg.to or "",
            "cc": msg.cc or "",
        }

        # Add attachment information if available
        if msg.attachments:
            attachment_names = [att.longFilename or att.shortFilename for att in msg.attachments]
            metadata["attachments"] = ", ".join(attachment_names)

        # Combine header information with body for better context
        header = f"Subject: {metadata['subject']}\nFrom: {metadata['sender']}\nTo: {metadata['to']}\nDate: {metadata['date']}\n\n"
        full_content = header + body

        logger.debug(f"Extracted metadata from MSG file: {metadata}")
        return full_content, metadata


@parsing_handler
def parse_generic_text(file_path: str) -> tuple[str, dict]:
    """Extracts content from a generic text file: UTF-8, then Windows-1252, then Latin-1."""
    for encoding in ("utf-8", "cp1252"):
        try:
            with open(file_path, encoding=encoding) as f:
                return f.read(), {}
        except UnicodeDecodeError:
            continue
    # Latin-1 maps every byte, so it always succeeds
    with open(file_path, encoding="latin-1") as f:
        return f.read(), {}


@parsing_handler
def parse_with_pandoc(file_path: str) -> tuple[str, dict]:
    """Uses Pandoc as a fallback to convert a document to plain text."""
    try:
        result = subprocess.run(
            ["pandoc", file_path, "-t", "plain"],
            capture_output=True,
            text=True,
            check=True,
            timeout=SUBPROCESS_TIMEOUT,
        )
        return result.stdout, {}
    except FileNotFoundError:
        logger.error(
            "Pandoc is not installed or not in your PATH. Please install it for advanced document parsing.",
        )
        raise
    except subprocess.CalledProcessError as e:
        logger.warning(f"Pandoc failed to parse {file_path}: {e.stderr}")
        return "", {}


@parsing_handler
def parse_archive(file_path: str) -> tuple[str, dict]:
    """
    Lists the names of files within a ZIP or TAR archive without extracting them.
    """
    file_path_lower = file_path.lower()
    if file_path_lower.endswith(".zip"):
        with zipfile.ZipFile(file_path, "r") as zip_archive:
            names = [info.filename for info in zip_archive.infolist() if not info.is_dir()]
    elif file_path_lower.endswith((".tar", ".gz", ".bz2", ".xz")):
        with tarfile.open(file_path, "r:*") as tar_archive:
            names = [member.name for member in tar_archive.getmembers() if member.isreg()]
    else:
        return "", {}
    return "\n".join(f"--- File: {name} ---" for name in names), {}
