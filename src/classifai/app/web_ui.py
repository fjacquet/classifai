"""
Web UI interface for ClassifAI.

This module provides a Streamlit-based web interface for ClassifAI.
It allows users to upload files, configure classification options,
and view classification results.
"""

import os
import tempfile
from pathlib import Path

import streamlit as st
from loguru import logger
from returns.result import Success

from classifai.config import app_config
from classifai.core.workflow import process_single_file
from classifai.logging_module import setup_logging


def setup_streamlit_page():
    """Configure the Streamlit page."""
    st.set_page_config(
        page_title="ClassifAI - Document Classification",
        page_icon="📄",
        layout="wide",
    )
    st.title("ClassifAI - Document Classification")
    st.markdown(
        """
        Upload documents to classify them using AI.
        ClassifAI will analyze the content and organize files based on their content.
        """,
    )


def display_classification_options():
    """Display and collect classification options."""
    st.subheader("Classification Options")

    col1, col2 = st.columns(2)

    with col1:
        rename_files = st.checkbox(
            "Rename files based on content",
            value=False,
            help="Rename files using information extracted by AI",
        )

        use_vision = st.checkbox(
            "Use vision model for images",
            value=False,
            help="Use vision model to analyze images (slower but more accurate for images)",
        )

    with col2:
        language_subfolders = st.checkbox(
            "Create language subfolders",
            value=True,
            help="Organize files in language-specific subfolders",
        )

        dest_dir = st.text_input(
            "Destination Directory",
            value=str(Path.home() / "ClassifAI_Output"),
            help="Directory where classified files will be saved",
        )

    # Ensure destination directory exists
    Path(dest_dir).mkdir(parents=True, exist_ok=True)

    return {
        "rename_files": rename_files,
        "use_vision": use_vision,
        "language_subfolders": language_subfolders,
        "dest_dir": Path(dest_dir),
    }


def handle_file_upload():
    """Handle file upload and classification."""
    uploaded_file = st.file_uploader(
        "Upload a file to classify",
        type=app_config.supported_extensions,
        help="Select a file to classify",
    )

    if uploaded_file is not None:
        # Create a temporary file to process
        with tempfile.NamedTemporaryFile(delete=False, suffix=Path(uploaded_file.name).suffix) as tmp_file:
            tmp_file.write(uploaded_file.getvalue())
            tmp_path = Path(tmp_file.name)

        st.info(f"Processing file: {uploaded_file.name}")

        return tmp_path, uploaded_file.name

    return None, None


def display_classification_results(result, original_filename, options):
    """Display classification results."""
    if isinstance(result, Success):
        context = result.unwrap()

        st.success("File classified successfully!")

        col1, col2 = st.columns(2)

        with col1:
            st.subheader("Classification Results")
            st.write(f"**Original File:** {original_filename}")
            st.write(f"**Category:** {context.category or 'Unknown'}")
            st.write(f"**Issuer:** {context.issuer or 'Unknown'}")
            st.write(f"**Sector:** {context.sector or 'Unknown'}")
            st.write(f"**Language:** {context.language or 'Unknown'}")

        with col2:
            st.subheader("File Destination")
            final_path = context.final_destination_path
            if final_path:
                st.write(f"**Final Path:** {final_path}")
                st.write(f"**Filename:** {final_path.name}")
            else:
                st.warning("File was not moved to a destination.")

        # Display AI results if available
        if context.ai_results:
            st.subheader("AI Analysis")
            for key, value in context.ai_results.items():
                if key not in ["category", "issuer", "sector", "language"]:
                    st.write(f"**{key.capitalize()}:** {value}")
    else:
        error = result.failure()
        st.error(f"Classification failed: {error}")


def main():
    """Main entry point for the Streamlit app."""
    setup_logging()
    setup_streamlit_page()

    options = display_classification_options()
    tmp_path, original_filename = handle_file_upload()

    if tmp_path and st.button("Classify Document"):
        with st.spinner("Classifying document..."):
            result = process_single_file(
                file_path=tmp_path,
                dest_dir=options["dest_dir"],
                rename_files=options["rename_files"],
                use_vision=options["use_vision"],
                language_subfolders=options["language_subfolders"],
            )

            display_classification_results(result, original_filename, options)

            # Clean up temporary file
            try:
                os.unlink(tmp_path)
            except Exception as e:
                logger.error(f"Failed to delete temporary file: {e}")


if __name__ == "__main__":
    main()
