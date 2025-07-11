"""
Tests for the utils module.
"""

import pytest

from classifai.utils import detect_language


@pytest.mark.parametrize(
    "text, expected_lang",
    [
        ("This is a test sentence in English.", "en"),
        ("Ceci est une phrase de test en français.", "fr"),
        ("Dies ist ein deutscher Testsatz.", "de"),
        ("这是一个中文测试句子。", "zh-cn"),
        ("これは日本語のテスト文です。", "ja"),
        ("Это тестовое предложение на русском языке.", "ru"),
    ],
)
def test_detect_language_success(text, expected_lang):
    """
    Tests that language detection works for various languages.
    """
    assert detect_language(text) == expected_lang


def test_detect_language_empty_input():
    """
    Tests that None is returned for empty or whitespace-only input.
    """
    assert detect_language("") is None
    assert detect_language("   ") is None


def test_detect_language_short_input():
    """
    Tests that language detection handles short, ambiguous text gracefully.
    `langdetect` can be unreliable with very short text.
    """
    # This might return 'en' or fail; we just want to ensure it doesn't crash.
    try:
        detect_language("a")
    except Exception as e:
        pytest.fail(f"detect_language raised an exception on short input: {e}")


def test_detect_language_non_string_input():
    """
    Tests that non-string input is handled correctly.
    """
    assert detect_language(None) is None
    assert detect_language(123) is None
