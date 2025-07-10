"""
Streamlit web application for ClassifAI.

This module provides a graphical user interface for the ClassifAI tool,
allowing users to select directories, preview classifications, and run the
organization process in a user-friendly way.
"""

from pathlib import Path

import pandas as pd
import streamlit as st
from loguru import logger

from classifai.classifai_cli import (
    classify_content,
    copy_file,
    cosine_similarity,
    get_embedding,
    get_parser,
    move_file,
)
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

# --- Session State Initialization ---
if "scan_results" not in st.session_state:
    st.session_state.scan_results = pd.DataFrame()
if "source_dir" not in st.session_state:
    st.session_state.source_dir = str(Path.home() / "Downloads")
if "destination_dir" not in st.session_state:
    st.session_state.destination_dir = str(Path.home() / "Documents" / "Classified")


def run_scan(
    source_dir_str: str,
    dest_dir_str: str,
    class_mode: str,
    model: str,
    url: str,
):
    """
    Scans the source directory, classifies files, and returns a DataFrame.
    """
    source_path = Path(source_dir_str)
    dest_path = Path(dest_dir_str)
    results = []

    if not source_path.is_dir():
        st.error(f"Source directory not found: {source_path}")
        return pd.DataFrame()

    # Default categories for now, will be configurable later
    categories = [
        "Documents",
        "Images",
        "Videos",
        "Audio",
        "Archives",
        "Scripts",
        "Misc",
    ]

    category_embeddings = {}
    if class_mode == "embedding":
        with st.spinner("Generating category embeddings..."):
            for category in categories:
                category_embeddings[category] = get_embedding(category, model=model)

    progress_bar = st.progress(0)
    files = [f for f in source_path.iterdir() if f.is_file()]
    total_files = len(files)

    for i, item in enumerate(files):
        progress_bar.progress((i + 1) / total_files, text=f"Processing: {item.name}")
        parser = get_parser(item.suffix)
        if parser:
            content = parser(str(item.absolute()))
            if not content.strip():
                content = item.name  # Fallback to filename

            if class_mode == "embedding":
                content_embedding = get_embedding(content, model=model)
                if content_embedding:
                    similarities = {
                        cat: cosine_similarity(content_embedding, emb)
                        for cat, emb in category_embeddings.items()
                    }
                    category = max(similarities, key=similarities.get)
                else:
                    category = "Unknown"
            else:
                category = classify_content(content, categories, logger)

            results.append(
                {
                    "File Name": item.name,
                    "Category": category,
                    "Destination Path": str(dest_path / category / item.name),
                    "Source Path": str(item.absolute()),
                }
            )
    progress_bar.empty()
    return pd.DataFrame(results)


def execute_file_operations(df: pd.DataFrame, operation: str):
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

        progress_bar.progress((i + 1) / total_ops, text=f"{operation.capitalize()}ing: {row['File Name']}")

        if operation == "move":
            result = move_file(source_path, str(dest_dir))
        else:
            result = copy_file(source_path, str(dest_dir))

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
            execute_file_operations(edited_df, "copy")

    with col3:
        if st.button("Move Files", type="primary", use_container_width=True):
            execute_file_operations(edited_df, "move")

else:
    st.info("Click 'Scan Directory' in the sidebar to begin.")
