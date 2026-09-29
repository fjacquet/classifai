"""Shared pytest fixtures."""

import pytest


@pytest.fixture(autouse=True)
def isolated_unknown_issuers(tmp_path, mocker):
    """Redirect unknown-issuer recording to a temp file so tests never touch config/."""
    path = tmp_path / "unknown_issuers.yaml"
    mocker.patch("classifai.infrastructure.knowledge_base.unknown_issuers_path", return_value=path)
    return path
