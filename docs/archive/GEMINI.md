> **⚠️ ARCHIVED — Superseded.** This Gemini CLI guideline doc mandates the `returns` library, which was removed (see `CHANGELOG.md` Unreleased "BREAKING"). Current agent guidance lives in `CLAUDE.md` at the repo root. Kept for historical reference.

# Gemini CLI Agent Guidelines for ClassifAI Project

This document outlines the specific guidelines and best practices for the Gemini CLI agent when interacting with the ClassifAI project codebase. Adhering to these principles ensures consistency, quality, and maintainability, with a strong emphasis on functional programming.

## General Principles

* **Adhere to Project Conventions:** Always analyze surrounding code, tests, and configuration to understand and mimic existing style, structure, framework choices, typing, and architectural patterns.
* **Proactive Problem Solving:** Fulfill user requests thoroughly, including reasonable, directly implied follow-up actions.
* **Self-Verification:** Utilize unit tests, output logs, and debug statements for self-verification during problem-solving.

## Functional Programming Principles

Your development logic must strictly adhere to these principles:

* **Pure Functions:** The majority of functions you write must be pure. Their output depends *only* on their input arguments, and they have *no observable side effects* (no modification of global variables, no database writes, no logs, no network calls, etc.). For the same input, they must always return the same output.
* **Immutability:** Data structures must not be modified after creation. Prefer `tuple` over `list` and `frozenset` over `set` for immutable collections. When modifying a structure, create a new instance with updated values instead of modifying in place.
* **Function Composition:** Build the application by combining simple functions into more complex ones. The data flow should be clear and follow a pipeline logic: `output_function_A -> input_function_B -> output_function_B`.
* **Higher-Order Functions:** Make extensive use of functions that take other functions as arguments or return functions (e.g., `map`, `filter`, `functools.reduce`, decorators).
* **Strict Separation of Core Logic and Side Effects:** The main business logic (the "pure core") must be completely isolated from code interacting with the external world (I/O, databases, APIs, etc.). Side effects must be confined to the periphery of the application.

## Python Code Quality & Style

* **PEP 8 & PEP 257:** All Python code modifications must strictly adhere to [PEP 8](https://www.python.org/dev/peps/pep-0008/) for style and [PEP 257](https://www.python.org/dev/peps/pep-0008/) for docstring conventions.
* **Automated Formatting & Linting:** After any code modification, run `uv run ruff check --fix` to ensure adherence to style and quality standards. For YAML files, run `uv run yamlfix src`.
* **Type Hinting:** Use type hints extensively (`typing` module, `Callable`, `TypeVar`) to improve code clarity, enable static analysis, and ensure all function signatures are fully typed. Consider `mypy` for static type checking.
* **Single Responsibility Principle (SRP):** Ensure functions and classes are small, focused, and perform a single, well-defined task.
* **High-Level Libraries:** Prefer robust, high-level third-party libraries (e.g., `IMAPClient`, `httpx`, `requests`) for complex protocols over low-level standard library equivalents.
* **Resource Management:** Use the `contextlib` module (`@contextmanager`, `closing`, `suppress`) for effective and reliable resource management.
* **Logging:** Use the `loguru` library for all logging purposes, ensuring appropriate logging levels (DEBUG, INFO, WARNING, ERROR, CRITICAL).
* **Functional Programming Tools:** Systematically use `functools` (`partial`, `reduce`, `wraps`) and `itertools` for efficient iterable manipulation.
* **Immutable Data Structures:** Use `namedtuple` or `dataclasses` (with `frozen=True`) for simple, immutable data structures.
* **Side Effect & Error Management:** **Crucially, use the `returns` library** (`Result[SuccessType, FailureType]` for fallible functions, `Maybe[ValueType]` for optional values, `@safe` decorator) for functional management of side effects and errors.
* **Composition Tools:** Explore `fn.py` or `toolz` (`fn.underscore._` or `toolz.pipe`) for advanced composition and readable data transformation pipelines.

## Project Structure

Adhere to the following project organization:

```
project_name/
│
├── core/               # Pure functional core of the application
│   ├── logic.py        # Pure functions, business logic
│   └── types.py        # Data types, dataclasses (frozen=True)
│
├── infrastructure/     # Impure layer, side effect management
│   ├── database.py     # Database interactions
│   ├── api_clients.py  # Clients for external APIs
│   └── file_io.py      # File reading/writing
│
├── main.py             # Entry point: orchestrates pure core calls and manages effects
│
└── tests/
    ├── property/       # Property-based tests
    └── unit/           # Classic unit tests
```

## Testing

* **Comprehensive Testing:** All new or modified code must be accompanied by comprehensive tests. Use `pytest` for unit and integration tests, `pytest-mock` for mocking, and `faker` for generating realistic test data.
* **Precise Date/Time Handling:** For time-sensitive logic in tests, use `pendulum` or `freezegun` to control date and time.
* **Correct Mock Patch Targets:** When using `pytest-mock`, always patch the object in the namespace where it is *used* (where it's imported or accessed), not where it is defined.
* **Specific Mocks:** When mocking configuration objects or objects with specific behaviors, provide mocks with necessary attributes/methods or use real instances with controlled parameters.
* **Precise Exception Testing:** Test for specific exception types raised by libraries and project code (e.g., `SystemExit` for `argparse` errors).
* **Property-Based Testing:** **Prioritize `hypothesis`** for property-based testing of functional code. Define properties that functions must respect across a range of automatically generated inputs.
* **Non-Regression Testing:** **Before finalizing any set of changes, you MUST run the entire test suite using `uv run pytest` to ensure no existing functionality has been broken.**
* **Log Capture:** Configure `loguru` with `pytest`'s `caplog` fixture in `tests/conftest.py` to allow assertion of log messages within tests.
* **Design for Testability:** Write inherently testable code by preferring dependency injection, avoiding global state, and breaking down complex logic into smaller, isolated units.

## Dependency Management

* **Exclusive `uv` Usage:** Use `uv` exclusively for all package management operations (installing, updating, removing, resolving dependencies).
* **Centralized Dependencies:** Respect `pyproject.toml` for defining all project dependencies, scripts, and metadata.
* **Reproducible Builds:** Utilize `uv.lock` to ensure exact and reproducible dependency installations across all environments.
* **Regular Updates:** Regularly update dependencies and consider automated security scanning.
* **Efficient Environment Management:** Leverage `uv`'s speed for creating and switching between virtual environments.

## CLI Design Best Practices

* **Flexible and User-Friendly CLIs:** Design command-line interfaces to be flexible and intuitive, using libraries like `click` or `argparse` effectively, providing helpful `--help` messages, default values, and validation.

## Git Operations

* **Commit Messages:** When preparing a commit, always propose a draft commit message that is clear, concise, and focuses on "why" the change was made rather than just "what" was changed. Match the style of recent commit messages.
* **Verification:** After each commit, confirm success by running `git status`.
* **No Push:** Never push changes to a remote repository without explicit user instruction.
