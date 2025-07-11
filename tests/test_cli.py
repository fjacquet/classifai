from typer.testing import CliRunner

from classifai.classifai_cli import app
from classifai.history_module import log_operation

runner = CliRunner()


def test_embedding_model_not_found(mocker):
    """
    Tests that the CLI exits gracefully when the embedding model is not found.
    """
    from classifai.embedding_module import EmbeddingModelNotFoundError

    mocker.patch(
        "classifai.classifai_cli.get_embedding",
        side_effect=EmbeddingModelNotFoundError("Model not found"),
    )

    result = runner.invoke(
        app, ["run", "--source-dir", ".", "--classification-mode", "embedding"]
    )
    assert result.exit_code == 1
    assert "Error" in result.stdout
    assert "Model not found" in result.stdout


def test_undo_command(mocker, tmp_path):
    """
    Tests the undo command.
    """
    # 1. Create a fake file and log a move operation
    source_file = tmp_path / "source.txt"
    dest_file = tmp_path / "dest.txt"
    source_file.write_text("test")
    mocker.patch("shutil.move")
    mocker.patch("pathlib.Path.unlink")

    # Log a move operation
    log_operation("move", str(source_file), str(dest_file))

    # 2. Run the undo command
    result = runner.invoke(app, ["undo"], input="y\n")
    assert result.exit_code == 0
    assert "Moved" in result.stdout
    assert "back to" in result.stdout

    # 3. Log a copy operation
    log_operation("copy", str(source_file), str(dest_file))

    # 4. Run the undo command for the copy
    result = runner.invoke(app, ["undo"], input="y\n")
    assert result.exit_code == 0
    assert "Deleted copied file" in result.stdout
