"""
Streamlit web application for ClassifAI.

This module provides a graphical user interface for the ClassifAI tool,
allowing users to select directories, preview classifications, and run the
organization process in a user-friendly way.
"""

from pathlib import Path

import streamlit as st

from classifai.config import (
    OLLAMA_API_URL,
    OLLAMA_EMBEDDING_MODEL_NAME,
    OLLAMA_MODEL_NAME,
)

# --- Page Configuration ---
st.set_page_config(
    page_title="ClassifAI",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded",
)

# --- Main UI ---
st.title("🤖 ClassifAI")
st.write("Welcome to ClassifAI! Select your directories and settings below to start organizing your files.")

# --- Configuration Sidebar ---
with st.sidebar:
    st.header("Configuration")

    # --- Directory Selection ---
    st.subheader("📁 Directory Settings")
    source_dir = st.text_input(
        "Source Directory",
        value=str(Path.home() / "Downloads"),
        help="The directory containing the files you want to organize.",
    )
    destination_dir = st.text_input(
        "Destination Directory",
        value=str(Path.home() / "Documents" / "Classified"),
        help="The root directory where classified subfolders will be created.",
    )

    # --- Model Selection ---
    st.subheader("🧠 AI & Model Settings")
    ollama_url = st.text_input("Ollama API URL", value=OLLAMA_API_URL)

    classification_mode = st.selectbox(
        "Classification Mode",
        ["embedding", "completion"],
        index=0,
        help="Choose 'embedding' for speed or 'completion' for more detailed analysis.",
    )

    if classification_mode == "embedding":
        model_name = st.text_input("Embedding Model", value=OLLAMA_EMBEDDING_MODEL_NAME)
    else:
        model_name = st.text_input("Completion Model", value=OLLAMA_MODEL_NAME)

    # --- Action Button ---
    st.divider()
    scan_button = st.button("Scan Directory", type="primary", use_container_width=True)


# --- Main Content Area ---
st.header("Results")

if scan_button:
    st.info(f"Scanning {source_dir}...")
    # Placeholder for the main logic to be called
    # This will eventually display the classification preview table.
    st.write("Scanning is not yet implemented.")

else:
    st.info("Click 'Scan Directory' in the sidebar to begin.")
