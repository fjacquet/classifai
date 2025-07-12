"""Unit tests for entrypoint_utils helper module."""

from pathlib import Path

import pandas as pd
import pytest
from returns.result import Success

from classifai.entrypoint_utils import generate_file_operations, perform_operations


@pytest.fixture()
def sample_df(tmp_path: Path) -> pd.DataFrame:
    """Return a DataFrame similar to `run_scan` output."""
    src1 = tmp_path / "a.txt"
    src2 = tmp_path / "b.txt"
    # create dummy files
    for p in (src1, src2):
        p.write_text("dummy")
    dest1 = tmp_path / "dest" / "a.txt"
    dest2 = tmp_path / "dest" / "b.txt"
    data = [
        {
            "File Name": "a.txt",
            "Language": "en",
            "Category": "Documents",
            "Issuer": "N/A",
            "New Filename": "a.txt",
            "Destination Path": str(dest1),
            "Source Path": str(src1),
            "Metadata": {},
        },
        {
            "File Name": "b.txt",
            "Language": "en",
            "Category": "Documents",
            "Issuer": "N/A",
            "New Filename": "b.txt",
            "Destination Path": str(dest2),
            "Source Path": str(src2),
            "Metadata": {},
        },
    ]
    return pd.DataFrame(data)


def test_generate_file_operations(sample_df):
    ops = generate_file_operations(sample_df)
    assert len(ops) == 2
    assert ops[0]["source"] == sample_df["Source Path"][0]
    assert ops[0]["destination"] == sample_df["Destination Path"][0]
    assert ops[1]["source"] == sample_df["Source Path"][1]
    assert ops[1]["destination"] == sample_df["Destination Path"][1]


def test_perform_operations_move(monkeypatch, sample_df):
    # Mock transfer_file to avoid touching FS
    processed: list[str] = []

    def fake_transfer(context, operation):
        processed.append(context.source_path)
        return Success(context)

    monkeypatch.setattr("classifai.entrypoint_utils.transfer_file", fake_transfer)

    ops = generate_file_operations(sample_df)
    count = perform_operations(ops, "move")
    assert count == len(ops)
    assert processed == [Path(op["source"]) for op in ops]


def test_perform_operations_copy(monkeypatch, sample_df):
    processed: list[str] = []

    def fake_transfer(context, operation):
        processed.append(context.source_path)
        return Success(context)

    monkeypatch.setattr("classifai.entrypoint_utils.transfer_file", fake_transfer)

    ops = generate_file_operations(sample_df)
    count = perform_operations(ops, "copy")
    assert count == len(ops)
    assert processed == [Path(op["source"]) for op in ops]
