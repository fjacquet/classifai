from returns.maybe import Some
from returns.result import Success
from typer.testing import CliRunner

from classifai.classifai_cli import app

runner = CliRunner()


def test_undo_command(mocker):
    """
    Tests the undo command.
    """
    mocker.patch("shutil.move")
    mocker.patch("pathlib.Path.unlink")
    mock_remove = mocker.patch("classifai.classifai_cli.remove_last_operation")

    # 1. Test move
    mock_get = mocker.patch(
        "classifai.classifai_cli.get_last_operation",
        return_value=Success(Some({"operation": "move", "source": "/fake/src", "destination": "/fake/dest"})),
    )
    result = runner.invoke(app, ["undo"], input="y\n")
    assert result.exit_code == 0
    assert "Moved" in result.stdout
    mock_get.assert_called_once()
    mock_remove.assert_called_once()

    # 2. Test copy
    mock_get.reset_mock()
    mock_remove.reset_mock()
    mock_get.return_value = Success(
        Some({"operation": "copy", "source": "/fake/src", "destination": "/fake/dest"})
    )
    result = runner.invoke(app, ["undo"], input="y\n")
    assert result.exit_code == 0
    assert "Deleted copied file" in result.stdout
    mock_get.assert_called_once()
    mock_remove.assert_called_once()
