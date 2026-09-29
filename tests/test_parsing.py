"""Tests for text extraction robustness (encodings, OCR, subprocess limits)."""

import shutil
import subprocess
import zipfile

import pytest

from classifai.infrastructure import parsing


def test_generic_text_prefers_cp1252_over_latin1(tmp_path):
    """Windows-1252 files (common for Swiss/French exports) decode the euro sign."""
    path = tmp_path / "export.csv"
    path.write_bytes("Montant: 12 €".encode("cp1252"))

    text, _ = parsing.parse_generic_text(str(path))

    assert text == "Montant: 12 €"


def test_eml_html_only_body_with_declared_charset(tmp_path):
    """HTML-only emails are decoded with their charset and keep subject/sender."""
    path = tmp_path / "mail.eml"
    path.write_bytes(
        b"From: Swisscom <billing@swisscom.ch>\r\n"
        b"Subject: Votre facture\r\n"
        b"MIME-Version: 1.0\r\n"
        b"Content-Type: text/html; charset=iso-8859-1\r\n"
        b"Content-Transfer-Encoding: 8bit\r\n\r\n"
        b"<html><body><p>Facture d'\xe9t\xe9</p></body></html>\r\n",
    )

    text, metadata = parsing.parse_eml(str(path))

    assert "Facture d'été" in text
    assert "Subject: Votre facture" in text
    assert metadata["sender"].startswith("Swisscom")


def test_html_honours_declared_charset(tmp_path):
    """HTML is decoded from bytes so the declared charset is respected."""
    path = tmp_path / "page.html"
    path.write_bytes(b'<html><head><meta charset="iso-8859-1"></head><body>Re\xe7u</body></html>')

    text, _ = parsing.parse_html(str(path))

    assert "Reçu" in text


def test_archive_listing_does_not_extract(mocker, tmp_path):
    """Archive member names are listed without writing their content to disk."""
    path = tmp_path / "bundle.zip"
    with zipfile.ZipFile(path, "w") as zf:
        zf.writestr("docs/a.pdf", "x")
        zf.writestr("b.txt", "y")
    open_spy = mocker.spy(zipfile.ZipFile, "open")

    text, _ = parsing.parse_archive(str(path))

    assert "--- File: docs/a.pdf ---" in text
    assert "--- File: b.txt ---" in text
    open_spy.assert_not_called()


def test_external_tools_have_a_timeout(mocker, tmp_path):
    """A hung pandoc must not block the scan or the watcher."""
    run = mocker.patch(
        "classifai.infrastructure.parsing.subprocess.run",
        side_effect=subprocess.TimeoutExpired("pandoc", 60),
    )

    text, _ = parsing.parse_with_pandoc(str(tmp_path / "doc.rst"))

    assert text == ""
    assert run.call_args.kwargs["timeout"] > 0


def test_ocr_languages_prefer_french_and_english(mocker):
    """OCR uses French + English (+ German) when installed, instead of English only."""
    parsing._ocr_languages.cache_clear()
    mocker.patch(
        "classifai.infrastructure.parsing.pytesseract.get_languages",
        return_value=["eng", "fra", "deu", "osd"],
    )

    assert parsing._ocr_languages() == "fra+eng+deu"
    parsing._ocr_languages.cache_clear()


@pytest.mark.skipif(shutil.which("tesseract") is None, reason="tesseract not installed")
def test_scanned_pdf_falls_back_to_ocr(tmp_path):
    """A PDF with no text layer is rendered and OCRed instead of returning nothing."""
    import fitz
    from PIL import Image, ImageDraw, ImageFont

    image_path = tmp_path / "scan.png"
    image = Image.new("RGB", (1200, 300), "white")
    ImageDraw.Draw(image).text(
        (40, 100), "FACTURE SWISSCOM", fill="black", font=ImageFont.load_default(size=72)
    )
    image.save(image_path)
    pdf_path = tmp_path / "scan.pdf"
    with fitz.open() as doc:
        page = doc.new_page(width=600, height=150)
        page.insert_image(page.rect, filename=str(image_path))
        doc.save(pdf_path)

    text, _ = parsing.parse_pdf(str(pdf_path))

    assert "SWISSCOM" in text.upper()
