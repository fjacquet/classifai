# ClassifAI Improvement Plan

This document outlines identified issues and proposed improvements for the ClassifAI codebase, organized by priority.

## Critical Issues (Must Fix)

### 1. Missing AppConfig Attributes - Runtime Crashes

**Problem:** Code references attributes that don't exist in `AppConfig`, causing `AttributeError` at runtime.

**Files affected:**
- `infrastructure/file_system.py:128` - `app_config.supported_extensions`
- `infrastructure/knowledge_base.py:52,144,166` - `app_config.config_dir`

**Solution:**
```python
# In config.py, add to AppConfig:
config_dir: Path = field(default=Path("config"))
supported_extensions: list[str] = field(init=False)

def __post_init__(self):
    # Derive supported_extensions from settings or hardcode
    object.__setattr__(
        self,
        "supported_extensions",
        self.settings.get("supported_extensions", [".pdf", ".docx", ".xlsx", ...])
    )
```

### 2. Category Configuration Mismatch

**Problem:** `knowledge_base.py:256` assumes categories is a dict with `keywords`, but `config/categories.yaml` is a simple list.

**Files affected:**
- `infrastructure/knowledge_base.py:256` - `get_category_suggestions()` will fail with KeyError

**Solution:** Either update the YAML structure or fix the code to handle list format.

### 3. Deprecated KnowledgeBase Class Still in Active Use

**Problem:** Class marked deprecated but used in core pipeline.

**Files affected:**
- `pipeline.py:110` - Creates deprecated `KnowledgeBase()`
- `background_watcher.py:27` - Also uses deprecated class

**Solution:** Complete migration to module-level functions and remove class.

---

## High Priority Issues

### 4. Error Handling Improvements

#### 4.1 Add Context Managers for File Operations

**Files to fix:**
- `config.py:27` - `with open(path) as f:` (already has it, verify)
- `classifai_cli.py:274` - Add context manager
- `infrastructure/history.py:30,35,54,73,79` - Multiple file operations need context managers

#### 4.2 Subprocess Timeout and Error Handling

**File:** `infrastructure/parsing.py:105,112,215`

```python
# Add timeout to subprocess calls
result = subprocess.run(
    ["pandoc", "-f", format_type, "-t", "plain", str(file_path)],
    capture_output=True,
    text=True,
    check=True,
    timeout=30  # Add timeout
)
```

#### 4.3 Replace Broad Exception Handlers

**Files affected:**
- `__init__.py:85` - Log the exception instead of silent pass
- `infrastructure/knowledge_base.py:92` - Distinguish between I/O, YAML, and other errors
- `infrastructure/llm.py:229,331` - Propagate error context instead of empty dict

### 5. Global State Thread Safety

**File:** `localization.py:160-171`

**Problem:** `global current_language` without thread safety.

**Solution:**
```python
import threading
_language_lock = threading.Lock()
_current_language = Language.EN

def set_language(lang: Language) -> None:
    global _current_language
    with _language_lock:
        _current_language = lang
```

### 6. Security Improvements

#### 6.1 Subprocess Security

**File:** `infrastructure/parsing.py`

- Validate pandoc binary path exists before execution
- Add `cwd` restriction to subprocess calls
- Consider using `shutil.which("pandoc")` to verify binary location

#### 6.2 Path Traversal Prevention

**File:** `core/logic.py`

- Use `Path.is_relative_to()` (Python 3.9+) instead of custom implementation
- Add path length validation
- Validate no symlink attacks in file operations

---

## Medium Priority Issues

### 7. Performance Optimizations

#### 7.1 Pre-compile Regex Patterns

**File:** `infrastructure/knowledge_base.py:36`

```python
# At module level
_NORMALIZE_PATTERN = re.compile(r'\s+')
_SPECIAL_CHARS_PATTERN = re.compile(r'[^\w\s-]')

def normalize_issuer_name(name: str) -> str:
    name = _SPECIAL_CHARS_PATTERN.sub('', name)
    name = _NORMALIZE_PATTERN.sub(' ', name)
    return name.strip().lower()
```

#### 7.2 Move JSON Import to Module Level

**File:** `infrastructure/llm.py:113,217,298`

Move `import json` to top of file instead of inside functions.

#### 7.3 Efficient File Scanning

**File:** `infrastructure/file_system.py:132-137`

```python
# Instead of multiple globs, do single pass
def get_supported_files(directory: Path, recursive: bool) -> list[Path]:
    supported_ext = set(app_config.supported_extensions)
    pattern = "**/*" if recursive else "*"
    return [
        f for f in directory.glob(pattern)
        if f.is_file() and f.suffix.lower() in supported_ext
    ]
```

#### 7.4 Add API Exponential Backoff

**File:** `infrastructure/llm.py:30-50`

```python
import time

def _make_request(...) -> dict[str, Any]:
    for attempt in range(MAX_RETRIES):
        try:
            # ... existing code
        except httpx.RequestError as e:
            if attempt < MAX_RETRIES - 1:
                wait_time = 2 ** attempt  # Exponential backoff
                time.sleep(wait_time)
            else:
                raise
```

### 8. Code Deduplication

#### 8.1 Extract Filename Sanitization Function

**File:** `core/logic.py` or new `utils.py`

```python
def sanitize_filename(text: str, max_length: int = 100) -> str:
    """Sanitize text for use in filenames."""
    sanitized = "".join(c for c in text if c.isalnum() or c in " -_")
    return sanitized.strip()[:max_length]
```

Then replace duplicate patterns in:
- `core/logic.py:40-41,54,98`
- `infrastructure/llm.py:175`

#### 8.2 Unify Context Update Pattern

Create helper method or use consistent pattern across:
- `core/logic.py:86,179` - Uses `context.__class__(**{**context.__dict__, ...})`
- `core/classification.py:41-45` - Uses `.copy(update={...})`

### 9. Remove Duplicate Implementations

#### 9.1 Consolidate CLI Implementations

**Problem:** Two CLI implementations exist:
- `app/cli.py` - Newer implementation
- `classifai_cli.py` - Older implementation

**Solution:** Keep one, remove the other, update entry point in `pyproject.toml`.

#### 9.2 Consolidate Pipeline Implementations

**Problem:** Two pipeline implementations:
- `pipeline.py` - Main pipeline
- `core/workflow.py` - Alternative workflow

**Solution:** Merge into single implementation or clearly document when to use each.

---

## Low Priority Issues

### 10. Testing Improvements

#### 10.1 Add Missing Test Coverage

Create test files for:
- `app/api.py` - API endpoint tests
- `infrastructure/geocoding.py` - Mock Nominatim API
- Security tests for archive extraction (symlink attacks, path traversal)

#### 10.2 Add Edge Case Tests

- Very long filenames (>255 chars)
- Unicode/emoji in filenames
- Files without extensions
- Empty files
- Concurrent file processing

### 11. Code Quality

#### 11.1 Add Missing Type Hints

**Files to update:**
- `infrastructure/parsing.py:31-55` - `parsing_handler` decorator
- `core/logic.py:21` - `_get_final_filename()` return type
- `infrastructure/geocoding.py` - Function parameters

#### 11.2 Remove Commented Code

**File:** `infrastructure/llm.py:236-245` - Remove commented prompt block

#### 11.3 Consistent Docstring Style

Standardize on Google or NumPy style docstrings across all modules.

### 12. Configuration Improvements

#### 12.1 Add YAML Schema Validation

Consider using `pydantic` or `cerberus` to validate YAML configuration files at startup.

#### 12.2 Make Hardcoded Values Configurable

Move to `config/settings.yaml`:
- `MAX_RETRIES` and `TIMEOUT` from `llm.py`
- Default language from `core/logic.py:113`
- Date format patterns

---

## Implementation Order

### Phase 1: Critical Fixes (Immediate)
1. Add missing `AppConfig` attributes
2. Fix category configuration mismatch
3. Remove deprecated `KnowledgeBase` usage

### Phase 2: Stability (1-2 weeks)
4. Error handling improvements
5. Thread safety for global state
6. Security hardening

### Phase 3: Performance (2-3 weeks)
7. Performance optimizations
8. Code deduplication
9. Remove duplicate implementations

### Phase 4: Quality (Ongoing)
10. Testing improvements
11. Code quality improvements
12. Configuration improvements

---

## Notes

- All changes should maintain backward compatibility where possible
- Each fix should include corresponding test updates
- Consider feature flags for gradual rollout of breaking changes
- Document any API changes in CHANGELOG.md
