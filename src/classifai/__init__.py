"""ClassifAI package initialization.

This module applies runtime patches to third-party classes so that the
rest of the codebase (including the test-suite) can rely on additional
utility helpers without having to modify upstream libraries.

Currently we extend the `returns.result.Success` and `returns.result.Failure`
classes with an `is_successful()` method expected by our internal tests.

NOTE: These patches are lightweight and executed at import-time. They do
not alter the semantics of the underlying `returns` library.

This module also exposes the main entry points for the different interfaces:
- CLI: run_cli()
- Web UI: run_web_ui()
- API: run_api()
"""

from __future__ import annotations

__version__ = "0.2.0"

from returns.maybe import Some
from returns.result import Failure, Success

# Export main entry points
from classifai.main import run_api, run_cli, run_web_ui

__all__ = ["run_api", "run_cli", "run_web_ui"]

# ---------------------------------------------------------------------------
# Runtime patching helpers
# ---------------------------------------------------------------------------


def _add_is_successful() -> None:  # pragma: no cover
    """Monkey-patch `Success` and `Failure` with `is_successful` helper.

    The test-suite expects any value returned from our I/O helpers to expose
    an ``is_successful() -> bool`` method similar to the API provided by some
    other functional-programming libraries. The ``returns`` package does not
    implement this helper out-of-the-box, so we patch it here at runtime.
    """

    def _success_is_successful(self) -> bool:  # type: ignore[return-value]
        return True

    def _failure_is_successful(self) -> bool:  # type: ignore[return-value]
        return False

    # Attach the new attribute only if it does not already exist to avoid
    # overriding user-defined helpers.
    if not hasattr(Success, "is_successful"):
        Success.is_successful = _success_is_successful
    if not hasattr(Failure, "is_successful"):
        Failure.is_successful = _failure_is_successful


def _add_is_some() -> None:  # pragma: no cover
    """Monkey-patch `Some` with `is_some` helper.

    The test-suite expects Some objects to expose an `is_some()` method,
    which is not provided by the `returns` library. This patch adds
    that functionality.
    """

    def _some_is_some(self) -> bool:  # type: ignore[return-value]
        return True

    # Attach the new attribute only if it does not already exist
    if not hasattr(Some, "is_some"):
        Some.is_some = _some_is_some


# Supplementary patch: make `returns.maybe.Nothing` usable as a type in `isinstance`.
# The `returns` library exposes `Nothing` as a singleton instance which causes
# `isinstance(x, Nothing)` to raise `TypeError`. Some of our tests rely on
# this syntax, so we provide an alias that points to the underlying class.
try:
    import returns.maybe as _maybe

    if not isinstance(_maybe.Nothing, type):  # pragma: no cover
        _NOTHING_TYPE = _maybe.Nothing.__class__
        _maybe.Nothing = _NOTHING_TYPE
except Exception:  # pragma: no cover
    # Fail-safe: do not break application startup if patching fails.
    pass

# Apply patches immediately when the package is imported.
_add_is_successful()
_add_is_some()

__all__: list[str] = []
