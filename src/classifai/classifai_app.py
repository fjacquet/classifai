"""
Streamlit web application for ClassifAI.

This module provides a graphical user interface for the ClassifAI tool,
allowing users to select directories, preview classifications, and run the
organization process in a user-friendly way.
"""

from pathlib import Path

import pandas as pd
import streamlit as st

from classifai.config import (
    OLLAMA_API_URL,
    OLLAMA_EMBEDDING_MODEL_NAME,
    OLLAMA_MODEL_NAME,
    USE_VISION_MODEL,
)
from classifai.core_logic import run_scan
from classifai.file_operations_module import copy_file, move_file

# --- Page Configuration ---
st.set_page_config(
    page_title="ClassifAI",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded",
)

# --- Session State Initialization ---
if "scan_results" not in st.session_state:
    st.session_state.scan_results = pd.DataFrame()
if "source_dir" not in st.session_state:
    st.session_state.source_dir = str(Path.home() / "Downloads")
if "destination_dir" not in st.session_state:
    st.session_state.destination_dir = str(Path.home() / "Documents" / "Classified")


def execute_file_operations(df: pd.DataFrame, operation: str, language_subfolders: bool, rename_files: bool):
    """
    Executes the file operations (move or copy) based on the DataFrame.
    """
    if operation not in ["move", "copy"]:
        st.error("Invalid operation specified.")
        return

    total_ops = len(df)
    progress_bar = st.progress(0)
    success_count = 0

    for i, row in df.iterrows():
        source_path = row["Source Path"]
        dest_path = Path(row["Destination Path"])
        dest_dir = dest_path.parent
        metadata = row["Metadata"]
        language = row["Language"]
        new_filename = row["New Filename"]
        issuer = row["Issuer"]

        progress_bar.progress((i + 1) / total_ops, text=f"{operation.capitalize()}ing: {row['File Name']}")

        if operation == "move":
            result = move_file(
                source_path,
                str(dest_dir.parent.parent),
                metadata,
                language if language_subfolders else None,
                new_filename if rename_files else None,
                issuer,
            )
        else:
            result = copy_file(
                source_path,
                str(dest_dir.parent.parent),
                metadata,
                language if language_subfolders else None,
                new_filename if rename_files else None,
                issuer,
            )

        if result:
            success_count += 1

    progress_bar.empty()
    st.success(f"Successfully {operation}ed {success_count} out of {total_ops} files.")
    st.session_state.scan_results = pd.DataFrame()  # Clear results


# --- Main UI ---
st.title("🤖 ClassifAI")
st.write("Welcome to ClassifAI! Select your directories and settings below to start organizing your files.")

# --- Configuration Sidebar ---
with st.sidebar:
    st.header("Configuration")

    # --- Directory Selection ---
    st.subheader("📁 Directory Settings")
    st.session_state.source_dir = st.text_input(
        "Source Directory",
        value=st.session_state.source_dir,
        help="The directory containing the files you want to organize.",
    )
    st.session_state.destination_dir = st.text_input(
        "Destination Directory",
        value=st.session_state.destination_dir,
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

    # --- Other Options ---
    st.subheader("⚙️ Other Options")
    language_subfolders = st.checkbox(
        "Create Language Subfolders",
        value=False,
        help="Organize files into subfolders based on detected language (e.g., /en, /fr).",
    )
    rename_files = st.checkbox(
        "Enable AI-Powered Renaming",
        value=False,
        help="Allow the AI to suggest new, descriptive filenames.",
    )
    use_vision = st.checkbox(
        "Use Vision Model for Images",
        value=USE_VISION_MODEL,
        help="Enable image analysis with a vision-capable model for more accurate classification.",
    )

    # --- Action Button ---
    st.divider()
    if st.button("Scan Directory", type="primary", use_container_width=True):
        with st.spinner("Scanning directory..."):
            st.session_state.scan_results = run_scan(
                st.session_state.source_dir,
                st.session_state.destination_dir,
                classification_mode,
                model_name,
                ollama_url,
                language_subfolders,
                rename_files,
                use_vision,
            )


# --- Main Content Area ---
st.header("Results")

if not st.session_state.scan_results.empty:
    st.info(
        f"Found {len(st.session_state.scan_results)} files to classify. Review the proposed changes below."
    )

    # Make the DataFrame editable
    edited_df = st.data_editor(
        st.session_state.scan_results,
        use_container_width=True,
        num_rows="dynamic",
        key="data_editor",
    )

    col1, col2, col3 = st.columns([0.6, 0.2, 0.2])

    with col2:
        if st.button("Copy Files", use_container_width=True):
            execute_file_operations(edited_df, "copy", language_subfolders, rename_files)

    with col3:
        if st.button("Move Files", type="primary", use_container_width=True):
            execute_file_operations(edited_df, "move", language_subfolders, rename_files)

else:
    st.info("Click 'Scan Directory' in the sidebar to begin.")
