"""
Tests for the embedding_module.
"""

import pytest

from classifai.embedding_module import cosine_similarity, get_embedding


def test_get_embedding_success(mocker):
    """
    Tests successful embedding generation.
    """
    mock_response = mocker.MagicMock()
    mock_response.data = [{"embedding": [0.1, 0.2, 0.3]}]
    mocker.patch("classifai.embedding_module.embedding", return_value=mock_response)

    embedding = get_embedding("test text")
    assert embedding == [0.1, 0.2, 0.3]


def test_get_embedding_api_error(mocker):
    """
    Tests the handling of an API error during embedding generation.
    """
    mocker.patch(
        "classifai.embedding_module.embedding",
        side_effect=Exception("API Error"),
    )

    embedding = get_embedding("test text")
    assert embedding == []


def test_cosine_similarity():
    """
    Tests the cosine similarity calculation.
    """
    vec1 = [1, 2, 3]
    vec2 = [1, 2, 3]
    assert cosine_similarity(vec1, vec2) == pytest.approx(1.0)

    vec3 = [1, 0, 0]
    vec4 = [0, 1, 0]
    assert cosine_similarity(vec3, vec4) == 0.0
