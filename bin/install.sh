#!/bin/bash

uv pip install \
    python-docx \
    openpyxl \
    python-pptx \
    PyPDF2 \
    PyMuPDF \
    textract \
    Pillow \
    opencv-python \
    pytesseract \
    moviepy \
    pydub \
    SpeechRecognition \
    mutagen \
    librosa

brew install poppler antiword tesseract ffmpeg


# tika-python: Nécessite Java Runtime Environment (JRE) installé sur votre système et le serveur Apache Tika en cours d'exécution.
# Installation de Java : Suivez les instructions pour votre OS.
# Démarrage du serveur Tika : Téléchargez le JAR de Tika (ex: tika-server-x.x.jar) et exécutez-le : java -jar tika-server-x.x.jar. tika-python se connectera à ce serveur.
