"""
Tests for the Streamlit web application's interaction with the core logic.
"""

from pathlib import Path

import pytest

from classifai.core.types import FileContext


@pytest.fixture
def mock_pipeline(mocker):
    """
    Mocks the entire process_file_pipeline to isolate the run_scan function.
    """
    # This mock will be the return value for each call to the pipeline

    mock_context = FileContext(
        source_path=Path("/dummy/source.txt"),  # Will be updated by the mock side_effect
        destination_dir=Path("/dummy/dest"),
        rename_files=False,
        use_vision=False,
        language_subfolders=False,
        categories=["Documents", "Images"],
        ai_results={"category": "Documents"},
        final_destination_path=Path("/sorted/Documents/file.txt"),
    )

    def pipeline_side_effect(file_path, *args, **kwargs):
        # Create a new context for each file processed and return directly
        return mock_context.__class__(
            **{
                **mock_context.__dict__,
                "source_path": file_path,
                "final_destination_path": f"/sorted/Documents/{file_path.name}",
            },
        )

    # Patch the pipeline function within the run_scan's module scope
    return mocker.patch(
        "classifai.pipeline.process_file_pipeline",
        side_effect=pipeline_side_effect,
    )


# def test_run_scan(tmp_path, mock_pipeline):
#     """
#     Tests the run_scan function to ensure it correctly calls the pipeline
#     and formats the results into a DataFrame.
#     """
#     # Create some dummy files
#     (tmp_path / "file1.txt").write_text("test")
#     (tmp_path / "file2.pdf").write_text("test")

#     df = run_scan(
#         source_dir_str=str(tmp_path),
#         dest_dir_str=str(tmp_path / "sorted"),
#         rename_files=False,
#         use_vision=False,
#         language_subfolders=False,
#         recursive=False,
#         categories=["Documents", "Images"],
#     )

#     assert isinstance(df, pd.DataFrame)
#     assert len(df) == 2
#     assert mock_pipeline.call_count == 2
#     assert "File Name" in df.columns
#     assert "Category" in df.columns
#     assert df["Category"].iloc[0] == "Documents"
#     assert df["File Name"].iloc[0] == "file1.txt"
#     assert df["Destination Path"].iloc[1] == "/sorted/Documents/file2.pdf"
