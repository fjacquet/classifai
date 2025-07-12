import tempfile
from pathlib import Path

from classifai.core.types import FileContext
from classifai.infrastructure.file_system import transfer_file

# Create test environment
tmp_dir = tempfile.mkdtemp()
source_dir = Path(tmp_dir) / "source"
source_dir.mkdir()
test_file = source_dir / "test.txt"
test_file.write_text("test content")

dest_dir = Path(tmp_dir) / "dest"
dest_dir.mkdir()
existing_file = dest_dir / "test.txt"
existing_file.write_text("existing content")
dest_path = dest_dir / "test.txt"

# Create context
context = FileContext(
    source_path=test_file,
    destination_dir=dest_dir,
    rename_files=False,
    use_vision=False,
    language_subfolders=False,
    categories=[],
    final_destination_path=dest_path,
)

# Print initial state
print("Before transfer:")
print(f"- Source: {test_file}, exists: {test_file.exists()}")
print(f"- Dest: {dest_path}, exists: {dest_path.exists()}")
print(f"- Context destination: {context.final_destination_path}")

# Perform transfer
result = transfer_file(context, "move")

# Print results
print(f"\nTransfer result: {result}")
print(f"Result successful: {result.is_successful()}")

if result.is_successful():
    updated_context = result.unwrap()
    print("\nAfter transfer:")
    print(f"- Updated context destination: {updated_context.final_destination_path}")
    moved_path = Path(updated_context.final_destination_path)
    print(f"- Moved path: {moved_path}")
    print(f"- Moved path exists: {moved_path.exists()}")
    print(f"- Moved path name: {moved_path.name}")
    print(f"- Original context destination: {context.final_destination_path}")

    # Check if original file still exists
    print(f"- Original source still exists: {test_file.exists()}")

    # Check if destination file exists with (1) suffix
    expected_path = dest_dir / "test (1).txt"
    print(f"- Expected path with (1) suffix: {expected_path}")
    print(f"- Expected path exists: {expected_path.exists()}")
