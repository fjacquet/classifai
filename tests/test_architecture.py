"""
Architecture tests: entry points import cleanly and stay lightweight.
"""

import subprocess
import sys


def test_cli_importable():
    """The CLI entry point can be imported."""
    from classifai.classifai_cli import app

    assert app is not None


def test_package_import_does_not_load_ui_frameworks():
    """Importing the package must not pull in Streamlit or web frameworks."""
    code = "import sys, classifai; print(any(m in sys.modules for m in ('streamlit', 'fastapi')))"
    result = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True, check=True)

    assert result.stdout.strip() == "False"
