# ClassifAI: Functional Specification

This document provides a functional specification for the ClassifAI tool. It outlines the current capabilities of the system and details the new feature for intelligent document classification.

## 1. Current Functionality

ClassifAI is a command-line tool designed to organize and manage documents within a specified folder structure. Based on the current architecture, the key functional components are:

* **Application Interfaces:** The tool is operated via multiple interfaces (`app/cli.py`, `app/web_ui.py`), which serve as the primary user entry points.
* **Core Application Logic:** A `core/` directory contains the main business logic of the application, orchestrated by `core/workflow.py`.
* **Processing Pipeline:** A processing pipeline within the core workflow orchestrates the sequence of operations for document processing.
* **Configuration Management:** The application uses an `infrastructure/config.py` module to handle settings and parameters, and a `config/categories.yaml` to define document categories.
* **LLM Integration:** The system leverages a Large Language Model via the `infrastructure/llm.py` module for intelligent processing tasks.
* **Background File Monitoring:** A `background_watcher.py` component allows the tool to monitor a directory for new files and process them automatically.
* **Localization:** The `localization.py` module provides support for multiple languages.

## 2. New Feature: Constrained Document Classification

This section details the new functionality for classifying documents based on the predefined list of categories.

### 2.1. Objective

The primary objective is to enhance the document classification process by using the `gemma3` model to categorize each document according to a strict, user-defined list. The final file path should follow the convention:

`Langue/Secteur_Activité/Émetteur/Catégorie/Date_Titre.ext`

### 2.2. Category Source and Management

The single source of truth for document categories is the `config/categories.yaml` file. The application must read this file at the start of the classification process.

**File Format (`config/categories.yaml`):**

The file is a YAML document containing a simple list of strings, where each string is a valid category.

Example:

```yaml
- Analyses
- Contrats
- Factures
- Rapports
```

### 2.3. Classification Process

1. **Load Categories:** The application will parse the `config/categories.yaml` file to load the list of valid categories.
2. **Prompt the Model:** For each document, the `gemma3n` model will be prompted to select the most suitable category **exclusively from the loaded list**. The prompt must clearly instruct the model that it is constrained to this list.
3. **File Organization:** The document will be moved and renamed according to the category returned by the model.

### 2.4. Handling of Uncategorizable Documents

If the model cannot confidently assign a document to any of the predefined categories, the following procedure will be followed:

1. **Temporary Classification:** The document will be assigned a special, non-final category named `_UNKNOWN_`.
2. **Category Suggestion:** The application will then make a second call to the `gemma3n` model, asking it to **suggest a new category** for the document. This suggestion is for user consideration and will not be automatically added to the `config/categories.yaml` file.
3. **File Naming for Review:** The document will be moved to the `_UNKNOWN_` category folder. The suggested category will be appended to the filename to facilitate user review.
    * **Example Filename:** `Langue/Secteur_Activité/Émetteur/_UNKNOWN_/2025-07-19_Titre_suggested-Ressources-Humaines.pdf`

This process ensures that all documents are handled, the integrity of the category list is maintained, and a clear workflow is provided for expanding the category set based on operational needs.

### 2.5. File Naming Convention

The final filename will be constructed using several pieces of information extracted or derived from the document. The standard format is `Date_Titre.ext`.

#### 2.5.1. Date Extraction

The date component of the filename is crucial for chronological organization. It will be determined using the following priority:

1. **From Document Content:** The system will first attempt to parse the document's content to find a relevant date (e.g., invoice date, report date).
2. **From File Metadata:** If no date can be reliably extracted from the content, the system will fall back to using the document's creation date from the file system metadata.

The date must be formatted according to the **ISO 8601 standard: `YYYY-MM-DD`**.

#### 2.5.2. Title Extraction

The `Titre` (Title) component will be a concise and descriptive title extracted from the document's content by the `gemma3` model.

#### 2.5.3. Language Extraction

The `Langue` (Language) component of the folder path determines the primary language of the document. It will be determined using the following logic:

1. **From Document Content:** The system will first prompt the `gemma3` model to identify the primary language of the document's content.
2. **Default Value:** If the language cannot be determined from the content, it will default to English (`en`).

The language must be represented as a two-letter code following the **ISO 639-1 standard**.

#### 2.5.4. Sector and Issuer Extraction

The `Secteur_Activité` (Business Sector) and `Émetteur` (Issuer) are determined using a two-step process that prioritizes a predefined knowledge base over AI classification to ensure consistency and accuracy.

**Step 1: Knowledge Base Lookup**

1. The system first attempts to identify the issuer from the document's content.
2. It then checks if this issuer exists in the `config/sector_issuer_mapping.yaml` file.
3. **If a match is found:**
    * The `Business_Sector` is assigned directly from the mapping file.
    * The `Issuer` is the value that was found.
    * The process stops here; the classifier is not used for this determination.

**Step 2: Classifier Fallback**

If the issuer is not found in the mapping file, the system falls back to the `gemma3` model:

1. **Business Sector Classification:** The model is prompted to select a `Business_Sector` for the document. This selection is **strictly constrained** to the list of valid sectors defined in `config/sectors.yaml`.
2. **Issuer Identification:** The model is also prompted to identify the `Issuer` from the document's content.
3. **Proposing New Mappings:** The newly identified issuer and its classified sector should be saved to a temporary file (e.g., `config/unknown_issuers.yaml`) for user review. This provides a mechanism to enrich the primary `sector_issuer_mapping.yaml` over time.

#### 2.5.4.1. Issuer Aliases

The system must support aliases for issuers to handle variations in issuer names that refer to the same entity:

1. **Alias Definition:** Multiple issuer name variations can be mapped to the same business sector in the `sector_issuer_mapping.yaml` file.
2. **Canonical Name:** One issuer name should be designated as the canonical (primary) name, with all aliases directing to the same folder structure.
3. **Normalization:** The system should normalize issuer names (e.g., case-insensitive matching, removing special characters) to improve matching accuracy.

#### 2.5.4.2. Unknown Issuers Workflow

The system provides a structured workflow for handling unknown issuers and integrating them into the knowledge base:

1. **Recording Unknown Issuers:** When the system encounters an issuer not in the mapping file, it records the issuer name and timestamp in the `config/unknown_issuers.yaml` file.
2. **Manual Review Process:** Administrators should periodically review the `unknown_issuers.yaml` file to:
   * Identify new issuers that need to be added to the knowledge base
   * Determine the appropriate business sector for each new issuer
   * Identify if the issuer is an alias of an existing issuer
3. **Knowledge Base Update:** After review, administrators should update the `config/sector_issuer_mapping.yaml` file with the new issuer-to-sector mappings or aliases.
4. **Format for Updates:**
   * For new issuers: Add the issuer name to the appropriate sector list
   * For aliases: Add the alias to the same sector as the canonical issuer name

---

## 3. System-Wide Requirements

This section outlines overarching requirements that apply to the entire ClassifAI system, its development, and its operation.

### 3.1. Application Interfaces

The application's core logic must be accessible through multiple interfaces, each offering the same set of functionalities and options:

* **Command-Line Interface (CLI):** The primary interface for direct user interaction and scripting.
* **Web UI:** A user-friendly web interface built with **Streamlit**.
* **API:** A RESTful API to allow for programmatic integration with other systems.

### 3.2. Configuration and Validation

* **LLM Selection:** The specific Large Language Model used by the classifier must not be hardcoded. It must be selectable by the user via an environment variable in the `.env` file.
* **Rules Validation:** The `config/rules.yaml` file must be validated at startup. Any category referenced within the rules must exist in the `config/categories.yaml` file. The application should fail to start if this consistency check fails.

### 3.3. Language and Localization

* **Classifier Language:** To minimize translation efforts and complexity within the application code, all interactions with the LLM (prompts and expected responses) must be in **French**.

### 3.4. Deprecated and Removed Features

To maintain a clean and focused codebase, the following features are considered deprecated and must be removed:

* **Debitors Configuration:** The `config/debitors.yaml` and `config/debitors.yaml.example` files are no longer used and should be removed from the project.
* **Embedding Logic:** The system will not use embedding models or vector databases. All related code and dependencies must be removed.

### 3.5. Quality Assurance and Testing

* **Mandatory Testing:** All new and modified code must be accompanied by comprehensive automated tests. Testing is not optional.
* **Sufficient Coverage:** The test suite must provide sufficient coverage to ensure the reliability and correctness of the application's logic.

### 3.6. Development Standards

All development must strictly adhere to the principles and guidelines documented in the following files:

* `docs/ARCHITECTURE_AND_DESIGN.md`
* `docs/GEMINI.md`
* `docs/TESTING_AND_ERROR_HANDLING.md`

This `FUNCTIONAL_SPECIFICATION.md` document shall serve as the single source of truth for all functional requirements.

### 3.7. File Type Handling Constraints

* **Archive Files:** The system must not process ZIP files directly. All archive files with `.zip` extension must be decompressed before being submitted to the classification system. This pre-processing step is the responsibility of the user or an external workflow and is outside the scope of ClassifAI's direct functionality.
