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
        return_value={"operation": "move", "source": "/fake/src", "destination": "/fake/dest"},
    )
    result = runner.invoke(app, ["undo"], input="y\n")
    assert result.exit_code == 0
    assert "Moved" in result.stdout
    mock_get.assert_called_once()
    mock_remove.assert_called_once()

    # 2. Test copy
    mock_get.reset_mock()
    mock_remove.reset_mock()
    mock_get.return_value = {"operation": "copy", "source": "/fake/src", "destination": "/fake/dest"}
    result = runner.invoke(app, ["undo"], input="y\n")
    assert result.exit_code == 0
    assert "Deleted copied file" in result.stdout
    mock_get.assert_called_once()
    mock_remove.assert_called_once()


def test_kb_list_unknown_reads_recorded_format(tmp_path):
    """kb-list-unknown must read the dict format written by record_unknown_issuer."""
    unknown_file = tmp_path / "unknown.yaml"
    unknown_file.write_text(
        "ubs ag:\n"
        "  original_name: UBS AG\n"
        "  count: 11\n"
        "  first_seen: '2026-01-01T00:00:00+00:00'\n"
        "  last_seen: '2026-02-01T00:00:00+00:00'\n",
    )

    result = runner.invoke(app, ["kb-list-unknown", "--file", str(unknown_file)])

    assert result.exit_code == 0, result.output
    assert "UBS AG" in result.stdout
    assert "11" in result.stdout


def test_watch_passes_complete_scan_config(mocker, tmp_path):
    """watch must hand the pipeline every scan_config key it reads."""
    mock_start = mocker.patch("classifai.classifai_cli.start_watcher")

    result = runner.invoke(
        app,
        ["watch", "-s", str(tmp_path), "-d", str(tmp_path / "out"), "--rename-files", "-ai", "llama3"],
    )

    assert result.exit_code == 0, result.output
    scan_config = mock_start.call_args.args[3]
    assert scan_config["rename_files"] is True
    assert scan_config["ollama_model"] == "llama3"
    for key in ("use_vision", "language_subfolders", "ollama_url"):
        assert key in scan_config


def test_run_forwards_ollama_overrides(mocker, tmp_path):
    """--ollama-model / --ollama-url must reach run_scan."""
    import pandas as pd

    mock_scan = mocker.patch("classifai.classifai_cli.run_scan", return_value=pd.DataFrame())

    result = runner.invoke(app, ["run", "-s", str(tmp_path), "-ai", "llama3", "-url", "http://h:1"])

    assert result.exit_code == 0, result.output
    assert mock_scan.call_args.kwargs["ollama_model"] == "llama3"
    assert mock_scan.call_args.kwargs["ollama_url"] == "http://h:1"


def test_watch_refuses_invalid_rules(mocker, tmp_path):
    """watch validates the configuration like run does, before watching anything."""
    from classifai.exceptions import ConfigurationError

    mocker.patch("classifai.classifai_cli.validate_app_config", side_effect=ConfigurationError("bad rule"))
    mock_start = mocker.patch("classifai.classifai_cli.start_watcher")

    result = runner.invoke(app, ["watch", "-s", str(tmp_path), "-d", str(tmp_path / "out")])

    assert result.exit_code == 1
    mock_start.assert_not_called()
