#!/bin/bash

uv add \
    python-dotenv \
    langdetect \
    geopy \
    fuzzywuzzy \
    python-docx \
    openpyxl \
    python-pptx \
    PyPDF2 \
    PyMuPDF \
    Pillow \
    opencv-python \
    pytesseract \
    moviepy \
    pydub \
    SpeechRecognition \
    mutagen \
    librosa \
    faker \
    pytest \
    pytest-mock \
    ruff \
    yamlfix \
    loguru \
    typer \
    streamlit \
    litellm \
    pypandoc
uv add beautifulsoup4 striprtf extract-msg

brew install poppler-qt5 antiword tesseract ffmpeg pandoc
