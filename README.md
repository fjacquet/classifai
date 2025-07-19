# ClassifAI

ClassifAI is a tool to automatically organize files in a directory using a hybrid of rule-based logic and local AI models with Ollama.

[![codecov](https://codecov.io/gh/fjacquet/classifai/graph/badge.svg?token=TS8PKVYX1V)](https://codecov.io/gh/fjacquet/classifai)

## Features

* **Hybrid Classification**: Uses a rule-based engine and a knowledge base (`sector_issuer_mapping.yaml`) for fast, accurate classification, falling back to powerful, user-selectable language models for semantic analysis.
* **Robust Parsing**: Supports a wide range of file types, including PDFs, Office documents, images (with OCR), and generic text files, with a fallback to `pandoc` for maximum compatibility.
* **Web Interface**: An intuitive Streamlit UI for easy configuration, previewing, and execution.
* **Command-Line Interface**: A powerful CLI for scripting and advanced users.

## Installation

1. **Clone the repository:**

    ```bash
    git clone https://github.com/your-username/classifai.git
    cd classifai
    ```

2. **Install System Dependencies:**
    * **Pandoc:** For advanced document parsing.

        ```bash
        # On macOS with Homebrew
        brew install pandoc
        ```

    * **Tesseract:** For Optical Character Recognition (OCR) in images.

        ```bash
        # On macOS with Homebrew
        brew install tesseract
        ```

3. **Install Python dependencies:**

    ```bash
    uv pip install -e .
    ```

4. **Install Ollama & Models:**
    * Follow the instructions on the [Ollama website](https://ollama.ai/) to install and run Ollama.
    * Pull a model, for example `gemma3n`:

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

**Example:**

```bash
uv run main.py --source-dir /path/to/your/files
```

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
