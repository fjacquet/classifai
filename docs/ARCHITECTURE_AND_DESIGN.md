# ClassifAI: Architecture and Design Principles

**Date:** July 12, 2025  
**Version:** 3.0  
**Project:** ClassifAI  
**Objective:** This document provides a comprehensive overview of ClassifAI's architecture, design principles, and implementation patterns.

---

## 1. System Architecture

ClassifAI adopts a modular architecture to facilitate development, testing, and maintenance. The system is organized into distinct layers with clear responsibilities.

### 1.1. Architecture Overview

```
+--------------------------+     +-------------------------+
|                          |     |                         |
|   UI (CLI / Streamlit)   |---->|  Core Logic             |
|                          |     |  (classifai_app.py,     |
|                          |     |   classifai_cli.py)     |
+--------------------------+     +-------------------------+
            ^                            |
            |                            v
+--------------------------+     +-------------------------+
|                          |     |                         |
|   Configuration          |     |  Classification Module  |
| (.env, categories.yaml,  |<----|  (Ollama)               |
|  debitors.yaml)          |     |                         |
+--------------------------+     +-------------------------+
            ^                            |
            |                            v
+--------------------------+     +-------------------------+
|                          |     |                         |
|   Knowledge Base Module  |     |  Parsing Module         |
|   (debitors.yaml)        |     |  (Specific, Generic,    |
|                          |     |   Pandoc Fallback)      |
+--------------------------+     +-------------------------+
            ^                            |
            |                            v
+--------------------------+     +-------------------------+
|                          |     |                         |
|   Geocoding Module       |     |  File Operations Module |
|   (EXIF -> Location)     |     |                         |
+--------------------------+     +-------------------------+
```

### 1.2. Key Components

1. **UI Layer**:
   - **CLI Interface** (`classifai_cli.py`): Command-line interface built with Typer.
   - **Web Interface** (`classifai_app.py`): Streamlit-based web UI for interactive use.

2. **Core Logic**:
   - **Application Core** (`classifai_core.py`): Central orchestration of the classification workflow.
   - **Configuration Management** (`config.py`): Handles loading and validation of configuration.

3. **Processing Modules**:
   - **Parsing Module** (`parsing.py`): Extracts text and metadata from various file formats.
   - **Classification Module** (`ollama_classification.py`): Interfaces with Ollama for content classification.
   - **File Operations Module** (`file_system.py`): Handles file operations with functional error handling.
   - **Geocoding Module** (`geocoding.py`): Extracts and processes location data from files.

4. **Support Modules**:
   - **Knowledge Base** (`knowledge_base.py`): Manages reference data for classification.
   - **History** (`history.py`): Tracks file operations for auditing and undo functionality.
   - **Logging** (`logging.py`): Centralized logging with Loguru.

## 2. Functional Programming Approach

ClassifAI embraces functional programming principles to enhance code quality, testability, and maintainability.

### 2.1. Core Functional Programming Principles

1. **Pure Functions**: Functions that always produce the same output for the same input and have no side effects.
2. **Immutability**: Data structures are not modified after creation; instead, new instances are created.
3. **Function Composition**: Building complex operations by combining simpler functions.
4. **Higher-Order Functions**: Functions that take other functions as arguments or return functions.
5. **Separation of Pure Logic and Side Effects**: Isolating side effects (I/O, network calls) from pure business logic.

### 2.2. Functional Containers

ClassifAI uses the `returns` library to implement functional programming patterns:

1. **Result[Success, Failure]**: For operations that may fail.

   ```python
   def transfer_file(context: FileContext, operation: str) -> Result[FileContext, str]:
       if not context.final_destination_path:
           return Failure("Destination path not set in context.")
       # ...
   ```

2. **Maybe[Some, Nothing]**: For optional values.

   ```python
   def get_last_operation() -> Maybe[Dict[str, Any]]:
       try:
           with open(HISTORY_FILE, 'r') as f:
               history = json.load(f)
               if not history:
                   return Nothing
               return Some(history[-1])
       except (FileNotFoundError, json.JSONDecodeError):
           return Nothing
   ```

3. **Function Composition with Bind and Map**:

   ```python
   return (
       resolved_path_result
       .bind(lambda final_dest: _perform_operation(context.source_path, final_dest, operation).map(lambda _: final_dest))
       .bind(lambda final_dest: safe(log_operation)(operation, str(context.source_path), str(final_dest)).map(lambda _: final_dest))
       .map(lambda final_dest: context.__class__(**{**context.__dict__, "final_destination_path": str(final_dest)}))
   )
   ```

## 3. File Operations Module

The File Operations Module is a critical component that handles file manipulation with robust error handling.

### 3.1. Key Components

1. **FileContext**: Immutable dataclass that holds the context for file operations.

   ```python
   @dataclass(frozen=True)
   class FileContext:
       source_path: str
       destination_dir: str
       rename_files: bool = False
       use_vision: bool = False
       language_subfolders: bool = False
       categories: List[str] = field(default_factory=list)
       final_destination_path: Optional[str] = None
   ```

2. **File Transfer Functions**:
   - `transfer_file`: Main entry point for file operations (move/copy).
   - `_resolve_name_conflict`: Handles filename conflicts by appending counters.
   - `_perform_operation`: Executes the actual file system operation.
   - `log_operation`: Records the operation in the history.

### 3.2. Name Conflict Resolution

The system handles file name conflicts by appending a counter to the filename:

```python
@safe
def _resolve_name_conflict(destination: Path) -> Path:
    if not destination.exists():
        return destination
    counter = 1
    final_destination = destination.parent / f"{destination.stem} ({counter}){destination.suffix}"
    while final_destination.exists():
        counter += 1
        final_destination = destination.parent / f"{destination.stem} ({counter}){destination.suffix}"
    return final_destination
```

**Important Lesson**: When resolving file name conflicts, the updated path must be correctly propagated through the entire operation chain. This requires:

1. Properly unwrapping the `Result` from `_resolve_name_conflict`.
2. Using the resolved path in subsequent operations.
3. Updating the `FileContext` with the new path.
4. Ensuring tests check the updated context, not the original.

## 4. Testing Strategy

ClassifAI follows a comprehensive testing strategy to ensure code quality and correctness.

### 4.1. Test Categories

1. **Unit Tests**: Test individual functions in isolation.
2. **Integration Tests**: Test interactions between modules.
3. **Functional Tests**: Test end-to-end workflows.

### 4.2. Testing Pure Functions

Pure functions are tested by verifying that they produce the expected output for given inputs:

```python
def test_resolve_name_conflict_no_conflict(tmp_path):
    # Setup
    test_file = tmp_path / "test.txt"
    
    # Execute
    result = _resolve_name_conflict(test_file)
    
    # Verify
    assert result == test_file
```

### 4.3. Testing Impure Functions

Impure functions are tested using mocks and controlled environments:

```python
def test_transfer_file_with_conflict(tmp_path):
    # Setup test environment with conflict
    source_dir = tmp_path / "source"
    source_dir.mkdir()
    test_file = source_dir / "test.txt"
    test_file.write_text("test content")
    
    dest_dir = tmp_path / "destination"
    dest_dir.mkdir()
    existing_file = dest_dir / "test.txt"
    existing_file.write_text("existing content")
    
    context = FileContext(
        source_path=str(test_file),
        destination_dir=str(dest_dir),
        final_destination_path=str(dest_dir / "test.txt")
    )
    
    # Execute
    result = transfer_file(context, "move")
    
    # Verify
    assert result.is_successful()
    updated_context = result.unwrap()
    assert Path(updated_context.final_destination_path).name == "test (1).txt"
    assert not test_file.exists()  # Original file should be moved
    assert existing_file.exists()  # Original destination file should remain
```

## 5. Document Types and Parsing Strategy

ClassifAI supports a wide range of document types through specialized parsers.

### 5.1. Supported Document Types

1. **Documents Bureautiques**:
   - PDF (.pdf)
   - Microsoft Word (.doc, .docx)
   - Microsoft Excel (.xls, .xlsx)
   - Microsoft PowerPoint (.ppt, .pptx)
   - Text Files (.txt, .rtf, .md)
   - Email Files (.eml, .msg)

2. **Multimedia**:
   - Images (.jpg, .png, .gif, .tiff, .heic, .webp)
   - Videos (.mp4, .mov, .avi, .webm)
   - Audio (.mp3, .wav, .ogg, .flac)

3. **Archives**:
   - ZIP (.zip), RAR (.rar), 7z (.7z)

4. **Other Formats**:
   - Code/Scripts (.sh, .py, .js, .ps1)
   - Configuration Files (.json, .yaml, .xml, .ini)
   - Web Files (.html, .htm, .url, .webloc)

### 5.2. Parsing Strategy

The parsing module uses a multi-tiered approach:

1. **Format-Specific Parsers**: Optimized parsers for common formats.
2. **Generic Parser**: Fallback for less common formats.
3. **Pandoc Conversion**: For formats requiring conversion before parsing.
4. **OCR**: For image-based documents with text content.

## 6. Key Technology Choices

ClassifAI leverages modern, robust libraries for its implementation:

1. **Functional Programming**: `returns` library for functional containers and patterns.
2. **Logging**: `loguru` for structured, configurable logging.
3. **CLI Framework**: `typer` for building command-line interfaces.
4. **Web UI**: `streamlit` for interactive web interfaces.
5. **LLM Integration**: `litellm` for interfacing with Ollama.
6. **Parsing Libraries**:
   - `PyMuPDF` (Fitz) for PDF processing
   - `python-docx` for Word documents
   - `openpyxl` for Excel files
   - `python-pptx` for PowerPoint files
   - `Pillow` for image processing
   - `pytesseract` for OCR
   - `extract-msg` for Outlook MSG files

## 7. Lessons Learned and Best Practices

### 7.1. Container Handling

1. **Unwrap Results Properly**: Always unwrap `Result` containers before using their values.

   ```python
   # Incorrect
   final_dest = resolved_path_result
   
   # Correct
   final_dest = resolved_path_result.unwrap()
   ```

2. **Update Immutable Context**: When updating immutable objects, create new instances.

   ```python
   # Create a new context with updated path
   updated_context = context.__class__(
       **{**context.__dict__, "final_destination_path": str(final_dest)}
   )
   ```

3. **Test Container Contents**: Test both the container type and its contents.

   ```python
   assert result.is_successful()
   updated_context = result.unwrap()
   assert updated_context.final_destination_path == expected_path
   ```

### 7.2. Error Handling

1. **Use Descriptive Error Messages**: Include context in error messages.

   ```python
   return Failure(f"Failed to move file {source} to {destination}: {str(e)}")
   ```

2. **Propagate Errors Properly**: Use `.bind()` to chain operations and propagate errors.

   ```python
   return (
       first_operation()
       .bind(lambda result: second_operation(result))
       .alt(lambda err: Failure(f"Operation failed: {err}"))
   )
   ```

3. **Handle Edge Cases**: Consider all possible failure modes.

   ```python
   if not path.exists():
       return Failure(f"Source file {path} does not exist")
   ```

### 7.3. Testing

1. **Test Both Success and Failure Paths**: Ensure both happy and error paths are tested.
2. **Use Controlled Environments**: Use temporary directories for file operation tests.
3. **Check Updated Context**: When testing operations that update context, verify the updated context.

---

By following these architectural principles and design patterns, ClassifAI maintains a robust, maintainable, and extensible codebase that can evolve to meet future requirements.
