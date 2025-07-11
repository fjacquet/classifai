"""
Tests for the Streamlit web application.

These tests focus on the data processing and logic functions within the
Streamlit app, not the UI rendering itself.
"""

import pandas as pd
import pytest

from classifai.classifai_app import run_scan


@pytest.fixture
def mock_backend(mocker):
    """Mocks all the backend functions called by the Streamlit app."""
    mocker.patch("classifai.core_logic.get_parser", return_value=lambda x: ("dummy content", {}))
    mocker.patch(
        "classifai.core_logic.classify_content",
        return_value={"category": "Documents", "new_filename": "new_name.txt"},
    )
    mocker.patch("classifai.core_logic.get_embedding", return_value=[0.1, 0.2, 0.3])
    mocker.patch("classifai.core_logic.cosine_similarity", return_value=0.9)
    mocker.patch("classifai.file_operations_module.move_file")
    mocker.patch("classifai.file_operations_module.copy_file")


def test_run_scan_completion_mode(tmp_path, mock_backend):
    """
    Tests the run_scan function in 'completion' mode.
    """
    # Create some dummy files
    (tmp_path / "file1.txt").write_text("test")
    (tmp_path / "file2.pdf").write_text("test")

    df = run_scan(
        source_dir_str=str(tmp_path),
        dest_dir_str=str(tmp_path / "sorted"),
        class_mode="completion",
        model="gemma3n",
        rename_files=False,
        use_vision=False,
        language_subfolders=False,
        recursive=False,
    )

    assert isinstance(df, pd.DataFrame)
    assert len(df) == 2
    assert "File Name" in df.columns
    assert "Category" in df.columns
    assert df["Category"].iloc[0] == "Documents"


def test_run_scan_embedding_mode(tmp_path, mock_backend):
    """
    Tests the run_scan function in 'embedding' mode.
    """
    # Create some dummy files
    (tmp_path / "file1.txt").write_text("test")
    (tmp_path / "file2.pdf").write_text("test")

    df = run_scan(
        source_dir_str=str(tmp_path),
        dest_dir_str=str(tmp_path / "sorted"),
        class_mode="embedding",
        model="mxbai-embed-large",
        rename_files=False,
        use_vision=False,
        language_subfolders=False,
        recursive=False,
    )

    assert isinstance(df, pd.DataFrame)
    assert len(df) == 2
    # In embedding mode, the category will be the one with the highest similarity
    # which we can't know for sure without more complex mocking,
    # but we can assert that a category was assigned.
    assert not df["Category"].isnull().any()
