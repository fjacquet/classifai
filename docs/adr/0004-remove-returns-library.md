# ADR-0004: Remove the `returns` library; use native exceptions

- **Status:** Accepted
- **Date:** Unreleased (CHANGELOG), codified retroactively 2026-04-19
- **Deciders:** Frederic Jacquet

## Context

Earlier versions of ClassifAI used the [`returns`](https://github.com/dry-python/returns)
library extensively:

- `Result[Success, Failure]` for fallible operations
- `Maybe[Some, Nothing]` for optional values
- `@safe` decorator to wrap exception-throwing functions
- `.bind()` / `.map()` / `flow()` / `pipe()` for composition

This produced code like:

```python
return (
    resolved_path_result.bind(lambda final_dest: _perform_operation(...).map(lambda _: final_dest))
    .bind(lambda final_dest: safe(log_operation)(...).map(lambda _: final_dest))
    .map(
        lambda final_dest: context.__class__(
            **{**context.__dict__, "final_destination_path": str(final_dest)}
        )
    )
    .alt(lambda err: Failure(f"File operation failed: {err}"))
)
```

It required monkey-patches to make `isinstance(x, Nothing)` work, and the
team-local idiom of `context.__class__(**{**context.__dict__, ...})` obscured
what would normally be a one-line Pydantic `model_copy(update=...)`.

## Decision

**Remove the `returns` library entirely.** Replace with native Python:

| Before                       | After                                                |
| ---------------------------- | ---------------------------------------------------- |
| `Result[T, E]`               | Plain return value; exceptions for failure           |
| `Success(value)`             | `return value`                                       |
| `Failure(error)`             | `raise ClassifAIError(error)` (custom exception)     |
| `Maybe[T]`                   | `T \| None`                                          |
| `@safe`                      | Explicit `try` / `except`                            |
| `flow(x, f, g, h)`           | `h(g(f(x)))` or sequential statements                |
| `.bind(...).map(...)`        | Sequential calls — let exceptions propagate          |
| `context.__class__(**{...})` | `context.model_copy(update={...})` (Pydantic v2)     |

A full custom exception hierarchy lives in `src/classifai/exceptions.py`
(`ClassifAIError` → `ParsingError`, `LLMError`, `FileOperationError`, etc.).

## Rationale

- **Readability.** Sequential try/except is immediately legible to any
  Python developer; `.bind(lambda x: f(x).map(lambda y: g(y)))` is not.
- **Debuggability.** Native exceptions give real stack traces. `returns`
  containers obscured the site of failure behind chained `.alt()` calls.
- **Ecosystem fit.** Every library the project touches (Pydantic, FastAPI,
  Typer, loguru, tenacity) uses exceptions natively. `returns` was a
  foreign grammar inside an otherwise idiomatic stack.
- **Dependency weight.** One fewer third-party runtime dependency.
- **Monkey-patches gone.** The `isinstance(result, Nothing)` workaround and
  manual `result_to_maybe` helpers all disappear.
- **Error classification improves.** Custom exceptions carry semantic type
  information; `Failure("file operation failed: {err}")` was an opaque
  string.

## Alternatives considered

1. **Keep `returns` and accept the overhead.** Rejected: ongoing cognitive
   cost for every contributor; no offsetting benefit once the team chose
   exceptions for composition anyway.
2. **Migrate to `rustedpy/result` (lighter-weight Result type).** Rejected:
   same conceptual complexity, smaller ecosystem.
3. **Only use `Result`; drop `Maybe`.** Rejected: partial migration is
   worse than either endpoint.

## Consequences

- **Positive:** Simpler code, clearer stack traces, one less dependency,
  idiomatic Python throughout.
- **Negative:** Loss of exhaustiveness checks that `Result` pattern-matching
  could provide. Mitigated by typed exception hierarchy + tests.
- **Enforcement:** `CLAUDE.md` Pre-Commit Checklist requires **"No `returns`
  library imports."** Any reintroduction is caught at review.

## References

- `CHANGELOG.md` — Unreleased section, "BREAKING: Removed `returns` library"
- `src/classifai/exceptions.py` — custom exception hierarchy
- `src/classifai/pipeline.py` — current sequential-call style
- `CLAUDE.md` — FP section enforcing this pattern
