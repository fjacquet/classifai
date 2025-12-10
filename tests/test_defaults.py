"""
Tests for shared defaults consistency.

This module ensures CLI and Streamlit use the same default values.
"""

from classifai.defaults import (
    DEFAULT_LANGUAGE_SUBFOLDERS,
    DEFAULT_LOG_FILE,
    DEFAULT_QUIET_LLM,
    DEFAULT_RECURSIVE,
    DEFAULT_RENAME_FILES,
    DEFAULT_VERBOSE,
)


class TestDefaults:
    """Tests for shared default values."""

    def test_recursive_default_is_false(self):
        """Recursive scanning should default to False for safety."""
        assert DEFAULT_RECURSIVE is False

    def test_rename_files_default_is_false(self):
        """File renaming should default to False."""
        assert DEFAULT_RENAME_FILES is False

    def test_language_subfolders_default_is_false(self):
        """Language subfolders should default to False."""
        assert DEFAULT_LANGUAGE_SUBFOLDERS is False

    def test_verbose_default_is_false(self):
        """Verbose logging should default to False."""
        assert DEFAULT_VERBOSE is False

    def test_quiet_llm_default_is_false(self):
        """Quiet LLM should default to False for consistency."""
        assert DEFAULT_QUIET_LLM is False

    def test_log_file_default_path(self):
        """Log file should have a default path."""
        assert str(DEFAULT_LOG_FILE) == "logs/main.log"


class TestDefaultsImportedByEntrypoints:
    """Tests that entrypoints import and use shared defaults."""

    def test_cli_imports_defaults(self):
        """CLI should import from defaults module."""
        # This test verifies the import works without errors
        from classifai.classifai_cli import (
            DEFAULT_LANGUAGE_SUBFOLDERS as CLI_LANG,
        )
        from classifai.classifai_cli import (
            DEFAULT_LOG_FILE as CLI_LOG,
        )
        from classifai.classifai_cli import (
            DEFAULT_QUIET_LLM as CLI_QUIET,
        )
        from classifai.classifai_cli import (
            DEFAULT_RECURSIVE as CLI_REC,
        )
        from classifai.classifai_cli import (
            DEFAULT_RENAME_FILES as CLI_RENAME,
        )
        from classifai.classifai_cli import (
            DEFAULT_VERBOSE as CLI_VERBOSE,
        )

        # Verify they match the source
        assert CLI_REC == DEFAULT_RECURSIVE
        assert CLI_RENAME == DEFAULT_RENAME_FILES
        assert CLI_LANG == DEFAULT_LANGUAGE_SUBFOLDERS
        assert CLI_VERBOSE == DEFAULT_VERBOSE
        assert CLI_QUIET == DEFAULT_QUIET_LLM
        assert CLI_LOG == DEFAULT_LOG_FILE

    def test_streamlit_imports_defaults(self):
        """Streamlit app should import from defaults module."""
        # Import the module to verify imports work
        # Note: We can't fully test Streamlit without running it,
        # but we can verify the imports are present
        import classifai.classifai_app as app_module

        # Check that the module has access to defaults
        assert hasattr(app_module, "DEFAULT_RECURSIVE")
        assert hasattr(app_module, "DEFAULT_RENAME_FILES")
        assert hasattr(app_module, "DEFAULT_LANGUAGE_SUBFOLDERS")
        assert hasattr(app_module, "DEFAULT_VERBOSE")
        assert hasattr(app_module, "DEFAULT_QUIET_LLM")
        assert hasattr(app_module, "DEFAULT_LOG_FILE")
