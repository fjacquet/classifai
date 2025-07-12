"""
Property-based tests for core logic functions.
"""

from pathlib import Path

from hypothesis import given
from hypothesis import strategies as st

from classifai.core.logic import _get_final_filename
from classifai.core.types import FileContext


@given(
    st.builds(
        FileContext,
        source_path=st.builds(
            Path, st.text(min_size=1, alphabet=st.characters(min_codepoint=97, max_codepoint=122))
        ),
        rename_files=st.booleans(),
        ai_results=st.dictionaries(
            keys=st.just("new_filename"),
            values=st.text(min_size=1, alphabet=st.characters(min_codepoint=97, max_codepoint=122)),
        ),
    )
)
def test_get_final_filename_returns_string(context):
    """
    Tests that _get_final_filename always returns a string.
    """
    result = _get_final_filename(context)
    assert isinstance(result, str)


@given(
    st.builds(
        FileContext,
        source_path=st.builds(
            Path, st.text(min_size=1, alphabet=st.characters(min_codepoint=97, max_codepoint=122))
        ),
        rename_files=st.just(False),
    )
)
def test_get_final_filename_returns_original_name_when_rename_is_false(context):
    """
    Tests that the original filename is returned when rename_files is False.
    """
    result = _get_final_filename(context)
    assert result == context.source_path.name
