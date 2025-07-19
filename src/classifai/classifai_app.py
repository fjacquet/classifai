"""
Streamlit web application for ClassifAI.

This module provides a graphical user interface for the ClassifAI tool,
allowing users to select directories, preview classifications, and run the
organization process in a user-friendly way.
"""

from pathlib import Path

import pandas as pd
import streamlit as st
from returns.result import Success

from classifai.config import app_config
from classifai.entrypoint_utils import generate_file_operations
from classifai.infrastructure.file_system import transfer_file
from classifai.pipeline import run_scan

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


def execute_file_operations(df: pd.DataFrame, operation: str):
    """Wrapper around perform_operations with a Streamlit progress bar."""
    if operation not in {"move", "copy"}:
        st.error("Invalid operation specified.")
        return

    ops = generate_file_operations(df)
    total_ops = len(ops)
    progress_bar = st.progress(0)
    success_count = 0

    for i, op in enumerate(ops):
        file_name = Path(op["source"]).name
        progress_bar.progress((i + 1) / total_ops, text=f"{operation.capitalize()}ing: {file_name}")
        result = transfer_file(op["context"], operation)
        if isinstance(result, Success):
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
    ollama_url = st.text_input("Ollama API URL", value=app_config.ollama_api_url)
    model_name = st.text_input("Completion Model", value=app_config.ollama_model_name)

    categories_text = st.text_area(
        "Categories (one per line)",
        value="\n".join(app_config.categories),
        height=200,
        help="Enter the categories to classify files into, one per line.",
    )
    categories = [cat.strip() for cat in categories_text.split("\n") if cat.strip()]

    # --- Other Options ---
    st.subheader("⚙️ Other Options")
    recursive = st.checkbox("Recursive Scan", value=True, help="Scan subdirectories recursively.")
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
        value=app_config.use_vision_model,
        help="Enable image analysis with a vision-capable model for more accurate classification.",
    )

    # --- Action Button ---
    st.divider()
    if st.button("Scan Directory", type="primary", use_container_width=True):
        with st.spinner("Scanning directory..."):
            st.session_state.scan_results = run_scan(
                st.session_state.source_dir,
                st.session_state.destination_dir,
                rename_files,
                use_vision,
                language_subfolders,
                recursive,
                categories,
            )


# --- Main Content Area ---
st.header("Results")

if not st.session_state.scan_results.empty:
    st.info(
        f"Found {len(st.session_state.scan_results)} files to classify. Review the proposed changes below.",
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
            execute_file_operations(edited_df, "copy")

    with col3:
        if st.button("Move Files", type="primary", use_container_width=True):
            execute_file_operations(edited_df, "move")

else:
    st.info("Click 'Scan Directory' in the sidebar to begin.")
