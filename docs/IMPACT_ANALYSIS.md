# Impact Analysis (Harmonized): Finalizing the Organization Strategy

**Date:** July 19, 2025
**Version:** 4.1
**Project:** ClassifAI
**Author:** Gemini

---

## 1. Context

This impact analysis outlines the remaining development tasks required to fully align the ClassifAI application with the `FUNCTIONAL_SPECIFICATION.md`. This version has been harmonized with the project's canonical architecture and naming conventions.

The primary remaining tasks concern the **final folder structure**, **support for specific file formats**, and **code cleanup**.

---

## 2. Remaining Tasks and Detailed Impact

### 2.1. Finalize Folder Structure and Renaming (High Priority)

**Required Specification:** `Langue/Secteur_Activité/Émetteur/Catégorie/Date_Titre.ext`.

The current implementation logic needs to be updated to generate this complete, multi-level path.

* **Impact on `core/classification.py` (Low):**
  * **Action:** Ensure the classification function consistently returns a data structure (e.g., a frozen dataclass from `core/types.py`) containing `language`, `business_sector`, `issuer`, and `category`.

* **Impact on `infrastructure/file_system.py` (High):**
  * **Action:** The main file transfer function must be modified to accept the full classification result object.
  * **Action:** The destination path construction logic must be updated to correctly build the full, required structure: `base_destination / Langue / Secteur_Activité / Émetteur / Catégorie / filename`. This order is critical and must be implemented precisely.

* **Impact on `core/workflow.py` (Medium):**
  * **Action:** The main processing workflow must be updated to correctly extract all required fields (`language`, `business_sector`, `issuer`, `category`) from the classification result.
  * **Action:** The workflow must pass this complete set of information to the `infrastructure.file_system.transfer_file` function.

* **Impact on `app/cli.py` and `app/web_ui.py` (Medium):**
  * **Action:** The user interface components must be updated to correctly invoke the main workflow in `core/workflow.py` and properly display the final destination path to the user for confirmation.

### 2.2. Add Parser for `.msg` Files (Medium Priority)

**Required Specification:** Support the `.msg` format via the `extract-msg` library.

* **Impact on `pyproject.toml` (Low):**
  * **Action:** Add the `extract-msg` dependency using `uv`.

* **Impact on `infrastructure/parsing.py` (Medium):**
  * **Action:** Create a new function `parse_msg(file_path)` that uses the `extract-msg` library to pull content.
  * **Action:** Add `".msg": parse_msg` to the dictionary of specific parsers.

* **Impact on `tests/` (Low):**
  * **Action:** Create a new test file for `parse_msg`, including a sample `.msg` file or a mock, to ensure it functions correctly.

### 2.3. Code Refactoring and Cleanup (Low Priority)

**Required Specification:** Removal of deprecated features as per `FUNCTIONAL_SPECIFICATION.md`.

* **Impact on entire codebase (Medium):**
  * **Action:** Perform a global search for any logic related to "embeddings" or vector databases and remove it entirely. This feature has been formally deprecated.
  * **Action:** Delete the `config/debitors.yaml` and `config/debitors.yaml.example` files and remove any code that references them, as they are no longer used.

### 2.4. Audio/Video Transcription (Deferred Task)

This task remains unchanged. It should be approached with a conditional import strategy to ensure stability if the required libraries are not installed.
