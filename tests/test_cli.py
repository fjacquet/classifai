from typer.testing import CliRunner

from classifai.classifai_cli import app

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

    result = runner.invoke(app, ["--source-dir", ".", "--classification-mode", "embedding"])
    assert result.exit_code == 1
    assert "Error" in result.stdout
    assert "Model not found" in result.stdout
