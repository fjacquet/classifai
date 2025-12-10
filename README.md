# ClassifAI

ClassifAI is a tool to automatically organize files in a directory using a hybrid of rule-based logic and local AI models with Ollama.

[![codecov](https://codecov.io/gh/fjacquet/classifai/graph/badge.svg?token=TS8PKVYX1V)](https://codecov.io/gh/fjacquet/classifai)

## Features

- **Hybrid Classification**: Uses a rule-based engine and a knowledge base (`sector_issuer_mapping.yaml`) for fast, accurate classification, falling back to powerful, user-selectable language models for semantic analysis.
- **Robust Parsing**: Supports a wide range of file types with a fallback to Pandoc for maximum compatibility.
- **Web Interface**: An intuitive Streamlit UI for easy configuration, previewing, and execution.
- **Command-Line Interface**: A powerful CLI for scripting and advanced users.

### Supported File Types

| Category | Extensions | Parser |
|----------|------------|--------|
| Documents | `.pdf`, `.docx`, `.doc`, `.txt`, `.rtf`, `.odt` | Native |
| Spreadsheets | `.xlsx`, `.xls`, `.ods` | Native |
| Presentations | `.pptx`, `.ppt`, `.odp` | Pandoc |
| Images (OCR) | `.png`, `.jpg`, `.jpeg`, `.tiff`, `.bmp` | Tesseract |
| Email | `.msg`, `.eml` | Native |
| Web | `.html` | Native |
| E-books | `.epub` | Pandoc |
| Technical docs | `.md`, `.rst`, `.tex`, `.org` | Pandoc |

## Installation

1. **Clone the repository:**

   ```bash
   git clone https://github.com/your-username/classifai.git
   cd classifai
   ```

2. **Install System Dependencies:**

   - **Pandoc:** For advanced document parsing.

     ```bash
     # On macOS with Homebrew
     brew install pandoc
     ```

   - **Tesseract:** For Optical Character Recognition (OCR) in images.

     ```bash
     # On macOS with Homebrew
     brew install tesseract
     ```

   - **libmagic:** For accurate MIME type detection (optional but recommended).

     ```bash
     # On macOS with Homebrew
     brew install libmagic

     # On Ubuntu/Debian
     sudo apt-get install libmagic1

     # On Windows
     # Download from https://github.com/nscaife/file-windows
     ```

   - **ExifTool:** For rich metadata extraction from documents and images (optional but recommended).

     ```bash
     # On macOS with Homebrew
     brew install exiftool

     # On Ubuntu/Debian
     sudo apt-get install exiftool

     # On Windows
     # Download from https://exiftool.org
     ```

3. **Install Python dependencies:**

   ```bash
   uv pip install -e .
   ```

4. **Install Ollama & Models:**

   - Follow the instructions on the [Ollama website](https://ollama.ai/) to install and run Ollama.
   - Pull a model, for example `gemma3n`:

     ```bash
     ollama pull gemma3n
     ```

## Usage

### Web Interface (Recommended)

Launch the Streamlit application for a user-friendly experience:

```bash
streamlit run src/classifai/classifai_app.py
```

### Command-Line Interface (CLI)

**Basic usage:**

```bash
uv run classifai run --source-dir /path/to/your/files --mode dry-run
```

**Common options:**

```bash
# Preview without making changes
uv run classifai run -s /path/to/files -m dry-run

# Move files to destination
uv run classifai run -s /path/to/files -d /path/to/dest -m move

# Copy files instead of moving
uv run classifai run -s /path/to/files -d /path/to/dest -m copy

# Verbose logging (DEBUG level)
uv run classifai run -s /path/to/files -v

# Verbose but suppress noisy LLM logs
uv run classifai run -s /path/to/files -v --quiet-llm

# Scan subdirectories recursively
uv run classifai run -s /path/to/files -R
```

**All CLI options:**

| Option | Short | Description | Default |
|--------|-------|-------------|---------|
| `--source-dir` | `-s` | Source directory to organize | Required |
| `--destination-dir` | `-d` | Destination directory | Same as source |
| `--mode` | `-m` | Operation mode: dry-run, move, copy | dry-run |
| `--recursive` | `-R` | Scan subdirectories | False |
| `--rename-files` | `-r` | Enable AI-powered file renaming | False |
| `--use-vision` | `-uv` | Use vision model for images | False |
| `--language-subfolders` | `-ls` | Create language-based subfolders | False |
| `--verbose` | `-v` | Enable DEBUG logging | False |
| `--quiet-llm` | `-ql` | Suppress LLM DEBUG logs | False |
| `--ollama-model` | `-ai` | Ollama model name | From config |
| `--log-file` | | Path to log file | logs/main.log |

## Configuration

### Sector and Issuer Mapping

ClassifAI uses the `config/sector_issuer_mapping.yaml` file to map document issuers to business sectors and handle issuer aliases for consistent organization.

#### Basic Structure

The file organizes issuers by business sectors:

```yaml
Banque:
  - UBS
  - PostFinance
  - BCV

Santé:
  - Médecins
  - Hôpitaux
  - Helsana
  - M-Thérapies

Commerce:
  - Migros
  - Coop
  - Amazon
```

#### Issuer Aliases

To handle different variations of the same issuer name, add an `aliases` section at the end of the file:

```yaml
aliases:
  # Banking aliases
  "UBS AG": "UBS"
  "UBS Switzerland AG": "UBS"
  "PostFinance AG": "PostFinance"
  "La Poste - PostFinance": "PostFinance"

  # Insurance aliases
  "AXA Winterthur": "AXA"
  "Swiss Life AG": "Swiss Life"

  # Health sector aliases
  "Helsana Assurance": "Helsana"
  "SWICA Assurance": "Swica"
```

#### How Aliases Work

1. **Document Processing**: When ClassifAI encounters an issuer name like "UBS AG"
2. **Alias Lookup**: The system checks the aliases section
3. **Normalization**: "UBS AG" gets normalized to "UBS"
4. **Folder Creation**: The document goes to the folder with the canonical name "UBS"

#### Benefits

- **Consistency**: All variations of the same issuer go to the same folder
- **Organization**: Prevents duplicate folders for the same entity
- **Flexibility**: Handles different legal names, abbreviations, and variations
- **Maintenance**: Easy to add new aliases as you encounter them

#### Usage Tips

- Add aliases as you discover them during document processing
- Use the most common/recognizable name as the canonical name
- Include legal variations (SA, AG, Ltd, etc.)
- Consider language variations (French/German company names)

### Folder Structure

ClassifAI organizes documents following this structure:

```
Langue/Secteur_Activité/Émetteur/Catégorie/Date_Titre.ext
```

Example:

```
fr/Santé/M-Thérapies/Factures/2025-07-18_Medical_bill_for_treatment.pdf
en/Finance/UBS/Relevés/2025-01-15_Monthly_statement.pdf
```
