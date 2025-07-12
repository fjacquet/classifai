# Testing and Error Handling Best Practices - ClassifAI

**Date:** July 12, 2025  
**Version:** 1.0  
**Project:** ClassifAI  
**Objective:** This document outlines best practices for testing and error handling in the ClassifAI project, with a focus on functional programming principles and lessons learned from debugging.

---

## 1. Testing in Functional Programming Context

### 1.1. Testing Pure Functions

Pure functions are the cornerstone of our functional programming approach and offer significant advantages for testing:

* **Deterministic Results**: For the same input, a pure function always produces the same output, making tests reliable and reproducible.
* **No Side Effects**: Pure functions don't modify external state, so tests don't need complex setup or teardown procedures.
* **Isolated Testing**: Each function can be tested in isolation without complex mocking of external dependencies.

**Example from ClassifAI**:

```python
# Pure function - easy to test
def _resolve_name_conflict(destination: Path) -> Path:
    """
    Handles name conflicts by appending a counter to the filename.
    This is a pure-like helper, but marked safe due to file system access.
    """
    # Check if the destination exists
    if not destination.exists():
        return destination
        
    # If it exists, create a new filename with a counter
    counter = 1
    final_destination = destination.parent / f"{destination.stem} ({counter}){destination.suffix}"
    
    # Keep incrementing the counter until we find a non-existing filename
    while final_destination.exists():
        counter += 1
        final_destination = destination.parent / f"{destination.stem} ({counter}){destination.suffix}"
        
    return final_destination
```

### 1.2. Testing Impure Functions

For functions that interact with external systems (file system, network, etc.), we use the following strategies:

* **Dependency Injection**: Pass external dependencies as parameters to make functions testable.
* **Mocking**: Use `unittest.mock` or `pytest-mock` to simulate external dependencies.
* **Test Fixtures**: Create controlled environments (e.g., temporary directories) for testing file operations.

**Example from ClassifAI**:

```python
@contextmanager
def create_test_env():
    """
    Creates a temporary directory structure for testing file operations.
    Yields the source directory path and the path to a test file.
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        source_dir = Path(tmpdir) / "source"
        source_dir.mkdir()
        test_file = source_dir / "test.txt"
        test_file.write_text("test content")
        yield source_dir, test_file
```

### 1.3. Testing Functional Containers

When testing code that uses functional containers like `Result`, `Maybe`, etc., consider these practices:

* **Test Both Success and Failure Paths**: Ensure both happy and error paths are tested.
* **Verify Container Types**: Check that the correct container type is returned.
* **Unwrap Values**: Test the actual values inside containers, not just the container itself.

**Example from ClassifAI**:

```python
def test_name_conflict_resolution():
    """
    Tests that name conflicts are handled correctly by appending a counter.
    """
    with create_test_env() as (source_dir, test_file):
        # Setup test environment with conflict
        dest_dir = source_dir.parent / "destination"
        dest_dir.mkdir()
        existing_file = dest_dir / "test.txt"
        existing_file.write_text("existing content")
        dest_path = dest_dir / "test.txt"
        
        context = FileContext(
            source_path=test_file,
            destination_dir=dest_dir,
            rename_files=False,
            use_vision=False,
            language_subfolders=False,
            categories=[],
            final_destination_path=dest_path,
        )
        
        # Execute function under test
        result = transfer_file(context, "move")
        
        # Verify result is successful
        assert result.is_successful()
        
        # Get the updated context from the result
        updated_context = result.unwrap()
        moved_path = Path(updated_context.final_destination_path)
        
        # Verify file was moved with correct name
        assert moved_path.exists()
        assert moved_path.name == "test (1).txt"
        assert moved_path.parent == dest_dir.absolute()
        assert existing_file.exists()  # Original file should still exist
```

## 2. Error Handling with Functional Containers

### 2.1. Using `Result` for Operations that May Fail

The `Result` container from the `returns` library is our primary tool for handling operations that may fail:

* **Success/Failure**: Use `Success` for successful operations and `Failure` for errors.
* **Error Propagation**: Use `.bind()` to chain operations and propagate errors.
* **Error Transformation**: Use `.alt()` to transform error messages.

**Example from ClassifAI**:

```python
def transfer_file(context: FileContext, operation: str) -> Result[FileContext, str]:
    """
    Moves or copies a file, handling path creation and name conflicts.
    This is the main entrypoint for file transfer operations.
    """
    if not context.final_destination_path:
        return Failure("Destination path not set in context.")

    destination = Path(context.final_destination_path)

    # Ensure the destination directory exists
    destination.parent.mkdir(parents=True, exist_ok=True)

    # Pipeline: resolve conflicts → perform operation → log → return updated context
    # First, resolve any name conflicts
    resolved_path_result = _resolve_name_conflict(destination)
    
    # The rest of the pipeline needs to work with the resolved path
    return (
        resolved_path_result
        # After resolving, perform the requested operation
        .bind(
            lambda final_dest: _perform_operation(
                context.source_path, final_dest, operation
            ).map(lambda _: final_dest)
        )
        # Log the operation
        .bind(
            lambda final_dest: safe(log_operation)(
                operation, str(context.source_path), str(final_dest)
            ).map(lambda _: final_dest)
        )
        # Return a NEW context instance that reflects the actual destination
        .map(
            lambda final_dest: context.__class__(
                **{**context.__dict__, "final_destination_path": str(final_dest)}
            )
        )
        .alt(lambda err: Failure(f"File operation failed: {err}"))
    )
```

### 2.2. Using `Maybe` for Optional Values

The `Maybe` container is used for operations that might return a value or nothing:

* **Some/Nothing**: Use `Some` for present values and `Nothing` for absent values.
* **Safe Access**: Use `.map()` to safely transform values if they exist.
* **Default Values**: Use `.value_or()` to provide defaults for absent values.

**Example from ClassifAI**:

```python
def get_last_operation() -> Maybe[Dict[str, Any]]:
    """
    Returns the last operation from the history file.
    Returns Nothing if the history is empty.
    """
    try:
        with open(HISTORY_FILE, 'r') as f:
            history = json.load(f)
            if not history:
                return Nothing
            return Some(history[-1])
    except (FileNotFoundError, json.JSONDecodeError):
        return Nothing
```

## 3. Common Pitfalls and Solutions

### 3.1. Container Type Checking

**Issue**: Type checking with `isinstance()` may not work as expected with functional containers.

**Solution**: Use monkey patching to add necessary methods for type checking or use explicit container-specific checks.

**Example from ClassifAI**:

```python
# Monkey patch for returns.maybe.Nothing to make it usable as a type
# This allows isinstance(result, Nothing) to work correctly
Nothing.__class_getitem__ = classmethod(lambda cls, _: cls)

# Add is_some() method to Some class for consistent checking
def _is_some(self):
    return True

Some.is_some = _is_some
```

### 3.2. Result-to-Maybe Conversion

**Issue**: Converting between `Result` and `Maybe` containers can be tricky.

**Solution**: Use explicit conversion patterns instead of relying on built-in methods that might not behave as expected.

**Example from ClassifAI**:

```python
# Instead of using to_maybe() which might not work as expected
def result_to_maybe(result):
    """Convert a Result to a Maybe."""
    if result.is_successful():
        return Some(result.unwrap())
    else:
        return Nothing
```

### 3.3. Updating Immutable Context

**Issue**: When working with immutable context objects, updates must create new instances.

**Solution**: Use dictionary unpacking or dataclass replace to create new instances with updated values.

**Example from ClassifAI**:

```python
# Return a NEW context instance that reflects the actual destination
.map(
    lambda final_dest: context.__class__(
        **{**context.__dict__, "final_destination_path": str(final_dest)}
    )
)
```

### 3.4. File Name Conflict Resolution

**Issue**: When resolving file name conflicts, the updated path must be correctly propagated through the entire operation chain.

**Solution**: Ensure that functions return the updated path and that calling code uses this updated path.

**Lesson Learned**: In our file name conflict resolution test, we were checking the original context instead of the updated context returned by the `transfer_file` function. This led to a test failure even though the code was working correctly.

```python
# Incorrect:
moved_path = Path(context.final_destination_path)  # Original context

# Correct:
updated_context = result.unwrap()  # Get updated context from result
moved_path = Path(updated_context.final_destination_path)
```

## 4. Best Practices for Test Design

### 4.1. Test Setup and Teardown

* Use context managers for test environment setup and cleanup.
* Isolate tests from each other to prevent interdependencies.
* Use fixtures for common setup code.

### 4.2. Test Assertions

* Be specific in assertions to catch subtle bugs.
* Test both the happy path and error paths.
* For functional containers, test both the container type and its contents.

### 4.3. Test Coverage

* Aim for high code coverage (>80%).
* Focus on testing complex logic and error handling.
* Don't just test that functions run; test that they produce the correct results.

---

By following these testing and error handling best practices, we can ensure that ClassifAI remains robust, maintainable, and bug-free as it evolves.
