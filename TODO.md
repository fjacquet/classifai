# ClassifAI - TODO

Ce document suit les tâches restantes et l'historique du travail effectué pour le projet ClassifAI.

---

## Tâches en Cours

### 1. Améliorations du Système de Classification

- [ ] **Amélioration de la Détection de la Langue**:
  - [ ] Implémenter une détection de langue plus précise pour les documents courts
  - [ ] Ajouter le support de plus de langues

- [ ] **Optimisation des Performances**:
  - [ ] Mettre en cache les réponses de l'API LLM pour des requêtes similaires
  - [ ] Optimiser le traitement par lots pour les gros volumes de fichiers

### 2. Fonctionnalités Futures

- [ ] **Support Archive**:
  - [ ] Ré-intégrer la transcription archive avec des imports conditionnels (tâche différée).

- [ ] **Support Audio/Vidéo**:
  - [ ] Ré-intégrer la transcription audio/vidéo avec des imports conditionnels (tâche différée).
  
- [ ] **Amélioration de l'Interface Utilisateur**:
  - [ ] Ajouter une interface graphique pour la configuration et la surveillance
  - [ ] Créer des tableaux de bord pour les statistiques d'utilisation

---

## Completed Tasks

### 1. Architecture & Refactoring

- [x] **Adopter une Architecture Fonctionnelle Stricte (`LAYOUT.md`)**:
  - [x] Restructurer le projet en répertoires `core` et `infrastructure`.
  - [x] Déplacer la logique pure vers `core/` et les appels I/O et API impurs vers `infrastructure/`.
  - [x] Intégrer la bibliothèque `returns` pour la gestion des erreurs et des valeurs optionnelles (`Result`, `Maybe`).
  - [x] Refactoriser le pipeline principal pour utiliser `returns.pipeline.flow`.
  - [x] Ajouter `hypothesis` pour les tests basés sur les propriétés de la logique pure.
  
- [x] **Correction du Pipeline de Classification**:
  - [x] Corriger la propagation des valeurs de secteur dans le pipeline
  - [x] Implémenter la préservation du secteur défini par l'IA
  - [x] Améliorer la gestion des erreurs et la journalisation
  - [x] Valider que les chemins de destination utilisent correctement la langue et le secteur détectés
- [x] **Adopt Functional Programming Principles**:
  - [x] Refactor `core_logic.py` to use a functional approach, with a clear separation of pure functions and side effects.
  - [x] Isolate I/O operations in the `parsing_module` and `knowledge_base_module`.
  - [x] Use function composition to build the main application pipeline.
- [x] **Refactor `core_logic.process_file`**:
  - [x] Break down the function into smaller, single-responsibility functions.
  - [x] Improve clarity and reduce complexity.
- [x] **Refactor `parsing_module`**:
  - [x] Create a decorator or helper to reduce boilerplate in `parse_*` functions.
- [x] **Refactor `core_logic.py`**:
  - [x] Relocate orchestration logic to `pipeline.py`.
  - [x] Update all imports in entrypoints and tests.
  - [x] Delete obsolete `core_logic.py`.
- [x] **Improve Configuration Handling**:
  - [x] Centralize configuration management in the `config.py` module.
  - [x] Load all YAML files at startup and provide a unified access point.

### 2. Fonctionnalités & Améliorations

- [x] **Amélioration du Suivi des Émetteurs Inconnus**:
  - [x] Stocker le `secteur` déterminé par l'IA dans `unknown_issuers.yaml`.
  - [x] Supprimer le champ `timestamp`.
  
- [x] **Localisation Française**:
  - [x] Implémenter la traduction des secteurs et catégories en français
  - [x] S'assurer que tous les messages à l'utilisateur sont en français
  - [x] Valider que les chemins de destination utilisent les noms de dossiers en français
  
- [x] **Amélioration des Noms de Fichiers de Destination**:
  - [x] Générer des noms de fichiers plus descriptifs basés sur les métadonnées extraites
  - [x] S'assurer que les caractères spéciaux sont correctement gérés dans les noms de fichiers
  - [x] Update the `kb-list-unknown` CLI command to display the new structure.
  - [x] Update tests to verify the new data and logic.

- [x] **Handle issuer aliases**:
  - [x] Update `debitors.yaml` to support an `aliases` key for each issuer.
  - [x] Modify `KnowledgeBase._load_debitors()` to expand aliases into the main debitors mapping.
  - [x] Ensure `get_sector_for_issuer()` correctly resolves aliases.
  - [x] Add unit tests for alias resolution.

- [x] **Support PDF**:
  - [x] Ré-intégrer la transcription PDF avec des imports conditionnels (tâche différée).

### 3. Features

- [x] **Unknown issuer tracking**:
  - [x] Create `unknown_issuers.yaml` alongside `config/debitors.yaml` to accumulate unmatched issuers (lower-cased) with timestamp.
  - [x] Update `KnowledgeBase.get_sector_for_issuer()` to append to this YAML when no match is found (avoid duplicates).
  - [x] Add unit tests verifying that unknown issuers are recorded exactly once.
  - [x] Provide an optional CLI command (`classifai kb-list-unknown`) to print the list for manual review.

### 4. Refactoring and Cleanup

- [x] **Remove embedding code**:
  - [x] Delete `src/classifai/embedding_module.py`.
  - [x] Remove all imports and logic branches referencing embeddings in:
    - `core_logic.py`
    - `classifai_cli.py`
    - `classifai_app.py`
    - `background_watcher.py`
    - `entrypoint_utils.py`
  - [x] Drop `--classification-mode` and `--embedding-model` options (CLI) and associated Streamlit widgets.
  - [x] Simplify `ScanConfig` to a single mode (completion).
  - [x] Remove embedding-only dependencies (`openai-whisper`, etc.) from `pyproject.toml`.
  - [x] Delete `tests/test_embedding_module.py` and embedding section in `tests/test_cli.py`.
  - [x] Run `ruff`, `pytest --cov` to ensure green build.
  - [x] Update docs (`README.md`, `ARCHITECTURE.md`) to reflect removal.

### 5. Finalizing Implementation and Documentation

- [x] **Bug Fix**: Corrected the destination path logic in `core_logic.py` to align with the `Langue/Émetteur/Catégorie` structure.
- [x] **Refine File Naming**
  - [x] Improve the AI prompt in `ollama_classification_module.py` to enforce the `YYYY-MM-DD_Titre_Court_Document.ext` format.
  - [x] Add a fallback mechanism in `core_logic.py` to handle cases where the AI-generated filename is invalid.
- [x] **Consolidate Documentation**:
  - [x] Merge `ADDENDUM.md`, `SPECIFICATIONS.md`, and `SPECIFICATION_REVISED.md` into a single, authoritative `ARCHITECTURE.md`.
  - [x] Delete the old specification documents.
- [x] **Code Cleanup**:
  - [x] Remove the duplicate `classifai_app.py` from the project root.

### 6. Environment & Core Setup

- [x] Install Ollama and pull a base model.
- [x] Initialize project structure (source, tests, docs).
- [x] Configuration de l'environnement de développement :
  - [x] Mise en place de `uv` pour la gestion des dépendances
  - [x] Configuration de `pytest`, `pytest-mock`, `faker` et `coverage.py` pour les tests
  - [x] Configuration de `ruff` pour le linting et le formatage
  - [x] Configuration de `yamlfix` pour les fichiers YAML
  - [x] Création de `.env.example` et ajout de `.env` à `.gitignore`
  
- [x] **Amélioration de la Documentation** :
  - [x] Mettre à jour la documentation pour refléter les changements récents
  - [x] Ajouter des exemples d'utilisation pour les nouvelles fonctionnalités
  - [x] Documenter la structure du projet et les bonnes pratiques de développement

## Prochaines Étapes

1. **Tests et Validation** :
   - [ ] Écrire des tests unitaires pour les nouvelles fonctionnalités
   - [ ] Effectuer des tests d'intégration complets
   - [ ] Valider les performances avec des volumes de données importants

2. **Déploiement** :
   - [ ] Préparer une nouvelle version du package
   - [ ] Mettre à jour la documentation utilisateur
   - [ ] Planifier le déploiement en production

3. **Améliorations Futures** :
   - [ ] Implémenter des analyses avancées des documents
   - [ ] Ajouter des fonctionnalités de rapport personnalisé
   - [ ] Explorer l'intégration avec d'autres outils de gestion documentaire
- [x] Implement core logic modules (`parsing`, `ollama_classification`, `file_operations`, `utils`, `logging`).

### 7. CLI and UI Implementation

- [x] Implement the command-line interface (CLI) with all options.
- [x] Implement the Streamlit web application (UI).
- [x] Implement "dry-run" mode and user confirmation.
- [x] Implement progress bars and real-time logging in the UI.

### 8. Advanced Parsing & Classification

- [x] **Structured Renaming & Organization**:
  - [x] Implement the full folder structure: `Langue/Émetteur/Catégorie/`.
  - [x] Ensure the filename format `Date_Titre_Court_Document.ext` is correctly applied.
- [x] **Knowledge-Based Classification**:
  - [x] Create `knowledge_base_module.py` to handle `debitors.yaml`.
- [x] **Advanced Parsing with Pandoc**:
  - [x] Refactor `parsing_module.py` to use a hierarchical approach with Pandoc as a fallback.
  - [x] Added parsers for `.html`, `.rtf`, `.eml`, and `.msg`.
- [x] **EXIF-Based Photo Organization**:
  - [x] Enhance image parser to extract all relevant EXIF data.
  - [x] Create `geocoding_module.py` to handle reverse geocoding.
  - [x] Update file operations to create date/location-based folders for photos.
- [x] **Custom Rules**:
  - [x] Implement a rules engine for pre-classification based on filename or path.
- [x] **Language-Based Organization**:
  - [x] Integrate a language detection library (`langdetect`).
  - [x] Update file operations to create language-based subfolders.
- [x] **Archive Support**:
  - [x] Add support for parsing archive contents (`.zip`, etc.).
- [x] **AI-Powered Renaming (Initial)**:
  - [x] Enhance Ollama prompts to extract issuer, date, and a short title.
- [x] **AI-Powered Sector Classification**:
  - [x] Add a new function `get_sector_with_ai` to `ollama_classification_module.py`.
  - [x] Update `core_logic.py` to call this function as a fallback when the issuer is not in the knowledge base.
- [x] **Rule for `.ppk` Files**:
  - [x] Add a rule to `config/rules.yaml` to classify `.ppk` files as "Clés et Certificats".

### 9. Advanced Features

- [x] **History and Undo**:
  - [x] Create `history_module.py` to log all file operations.
  - [x] Implement an `undo` command.
- [x] **Vision Model Integration**:
  - [x] Integrate `ollama/llava` for advanced image classification.
- [x] **Background Watching**:
  - [x] Implement a background process to watch a folder for new files.

### 10. Testing and Configuration

- [x] Write comprehensive unit and integration tests for all completed features.
- [x] Add configuration for generic text file extensions.
- [x] Add configuration to enable/disable vision model usage.
- [x] Add `categories.yaml` for dynamic category management.
