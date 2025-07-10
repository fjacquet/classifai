## Architecture et Conception Détaillée - ClassifAI

**Date :** 10 juillet 2025
**Version :** 1.1
**Projet :** ClassifAI
**Objectif :** Ce document décrit l'architecture générale et la conception détaillée des modules clés du projet ClassifAI, en se basant sur la spécification fonctionnelle validée. Il intègre les principes de bonnes pratiques Python, DRY, KISS, une approche de développement axée sur les tests (TDD), la gestion sécurisée des configurations via `.env`, et l'utilisation d'Ollama/LiteLLM pour la classification.

-----

### 1\. Vue d'Ensemble de l'Architecture

ClassifAI adoptera une architecture modulaire et découplée pour faciliter le développement, les tests et la maintenance. Le système sera composé de plusieurs modules principaux interagissant de manière claire et définie.

```
+------------------+     +-------------------+     +-------------------------+
|                  |     |                   |     |                         |
|   CLI (Typer)    |---->|  Main Application |---->|  Ollama Classifier      |
|                  |     |  (Core Logic)     |<----|  (via LiteLLM)          |
+------------------+     |                   |     +-------------------------+
                         |                   |               ^
+------------------+     |                   |               |
|                  |     |                   |               |
| Streamlit App    |---->|                   |               |
|                  |     |                   |               |
+------------------+     +-------------------+               |
                                   |                         |
                                   |                         |
                                   v                         v
+------------------+     +-------------------+     +-------------------------+
|                  |     |                   |     |                         |
| Parsing Module   |<----|  File Operations  |<----|      Logging & History  |
|                  |     |     Module        |     |       Module            |
+------------------+     +-------------------+     +-------------------------+
                                   ^
                                   |
                                   |
+------------------+     +-------------------+
|                  |     |                   |
| Config & Env Vars|     |      Tests &      |
|  (.env, YAML)    |     |   Quality Tools   |
+------------------+     +-------------------+
```

**Composants Clés :**

* **Main Application (Core Logic) :** Le cœur de l'application qui orchestre le flux de travail (scan, parsing, classification, opération sur fichiers).
* **CLI (Typer) :** Interface en ligne de commande pour les utilisateurs techniques.
* **Streamlit App :** Interface utilisateur web pour une utilisation conviviale.
* **Parsing Module :** Responsable de l'extraction de contenu à partir de divers formats de documents.
* **Ollama Classifier :** Interagit avec les modèles Ollama via LiteLLM pour la classification des documents. Peut utiliser des modèles de chat ou d'embedding.
* **File Operations Module :** Gère le déplacement, la copie et la résolution des conflits de noms de fichiers.
* **Logging & History Module :** Enregistre les opérations et permet les fonctions d'annulation.
* **Config & Env Vars :** Gère la configuration de l'application et les variables d'environnement sensibles.
* **Tests & Quality Tools :** L'ensemble des outils pour garantir la qualité du code (pytest, ruff, yamlfix, coverage).

-----

### 2\. Conception Détaillée des Modules

#### 2.1. Module `config` et Gestion des Variables d'Environnement

* **Objectif :** Centraliser la gestion de la configuration de l'application et des variables d'environnement.
* **Implémentation :**
  * Utilisation de la bibliothèque `python-dotenv` pour charger les variables depuis un fichier `.env`.
  * Un fichier `config.yaml` pour les configurations non sensibles (catégories par défaut, règles, etc.).
  * Les fonctions de chargement devront valider la présence des variables essentielles (ex: `OLLAMA_MODEL_NAME`, `OLLAMA_API_URL`).
* **Exemple `.env` (non versionné) :**

    ```ini
    OLLAMA_MODEL_NAME=gemma3n
    OLLAMA_API_URL=http://localhost:11434
    # Autres variables sensibles
    ```

* **Bonnes Pratiques :** `.env` sera listé dans `.gitignore`. `yamlfix` sera utilisé pour maintenir le `config.yaml`.

#### 2.2. Module `logging`

* **Objectif :** Fournir un système de journalisation flexible et informatif pour suivre les opérations de ClassifAI.
* **Implémentation :**
  * Utilisation du module `loguru`.
  * Configuration pour écrire à la fois sur la console et dans un fichier log (configurable via CLI/Streamlit).
  * Niveaux de log (INFO, WARNING, ERROR, DEBUG) pour différents niveaux de détail.
* **Bonnes Pratiques :** Configurer les loggers de manière à ce qu'ils n'interfèrent pas entre les modules.

#### 2.3. Module `parsing`

* **Objectif :** Extraire le texte et les métadonnées de divers types de documents.
* **Dépendances :** `PyMuPDF`, `python-docx`, `openpyxl`, `python-pptx`, `Pillow`, `pytesseract`.
* **Implémentation :**
  * Fonction `parse_document(file_path: Path) -> Tuple[str, dict]` qui retourne le contenu texte et un dictionnaire de métadonnées.
  * Utilisation d'une stratégie de design pattern "Strategy" ou "Factory" pour gérer les différents types de fichiers (ex: une fonction pour chaque type de fichier qui est appelée par un dispatcher).
  * Gestion robuste des erreurs de lecture/parsing pour chaque type de fichier (retourner un contenu vide ou une erreur spécifique).
  * Limitation de la taille du contenu texte extrait pour l'envoi aux modèles LLM.
* **Bonnes Pratiques :** DRY en évitant la duplication de logique pour des formats similaires. KISS en gardant les fonctions de parsing simples et spécifiques à un type de fichier.

#### 2.4. Module `ollama_classification` (Stratégie Hybride)

* **Objectif :** Interfacer avec Ollama via LiteLLM pour la classification des documents, en utilisant une approche hybride pour combiner vitesse et précision.
* **Dépendances :** `litellm`.
* **Implémentation :**
    * **Mode 1: Classification par Embedding (Rapide)**
        * **Fonction `get_embedding(text: str) -> List[float]`**: Appelle `litellm.embedding` avec un modèle d'embedding (ex: `nomic-embed-text`).
        * **Logique de Similarité**: Calcule la similarité cosinus entre l'embedding d'un document et les embeddings pré-calculés pour chaque catégorie.
        * **Cas d'utilisation**: Idéal pour le traitement rapide de grands volumes de fichiers.
    * **Mode 2: Classification par Complétion (Approfondie)**
        * **Fonction `classify_document_completion(content: str, file_type: str) -> str`**: Construit un prompt détaillé et demande au modèle de chat (ex: `gemma3n`) de choisir une catégorie.
        * **Cas d'utilisation**: Pour les fichiers où une analyse sémantique plus profonde est nécessaire.
* **Bonnes Pratiques :**
  * Encapsuler la logique de chaque mode dans des fonctions distinctes.
  * Permettre à l'utilisateur de choisir le mode via la CLI (`--classification-mode`).
  * Gérer les timeouts et les erreurs réseau avec Ollama.
  * Utiliser `pytest-mock` pour simuler les appels à LiteLLM lors des tests.

#### 2.5. Module `file_operations`

* **Objectif :** Gérer les déplacements et copies réels des fichiers, inclure la gestion des conflits.
* **Dépendances :** `shutil`, `pathlib`.
* **Implémentation :**
  * Fonction `move_file(source_path: Path, dest_dir: Path, new_name: Optional[str] = None) -> Path`: Déplace un fichier, gère les conflits de noms en ajoutant un suffixe numérique.
  * Fonction `copy_file(source_path: Path, dest_dir: Path, new_name: Optional[str] = None) -> Path`: Copie un fichier, gère les conflits.
  * Fonction `resolve_conflict(dest_path: Path) -> Path`: Logique interne pour trouver un nom de fichier unique.
* **Bonnes Pratiques :** S'assurer que les chemins sont absolus et validés. Gérer les permissions et les erreurs d'E/S. KISS en gardant les fonctions de déplacement/copie minimalistes et concentrées sur leur tâche.

#### 2.6. Module `history` (MVP+)

* **Objectif :** Enregistrer toutes les opérations de déplacement/copie pour permettre une fonction d'annulation.
* **Implémentation :**
  * Stocker un journal des opérations (fichier JSON ou SQLite léger).
  * Chaque entrée du journal doit contenir : `timestamp`, `original_path`, `new_path`, `operation_type` (move/copy), `status` (success/fail).
  * Fonction `undo_last_operation()`.
* **Bonnes Pratiques :** Sérialiser/désérialiser les données de manière fiable.

#### 2.7. Module `cli` (Utilisant Typer)

* **Objectif :** Fournir l'interface en ligne de commande.
* **Dépendances :** `typer`.
* **Implémentation :**
  * Utiliser des décorateurs `typer.command()` et `typer.Option()` pour définir les commandes et les arguments.
  * Valider les chemins d'entrée/sortie.
  * Orchestrer les appels aux autres modules (parsing, classification, opérations de fichiers).
  * Afficher les résultats clairs en mode `dry-run`.
  * Demander confirmation avant les opérations réelles.
* **Bonnes Pratiques :** Messages d'erreur clairs. Options `--help` fonctionnelles.

#### 2.8. Module `streamlit_app`

* **Objectif :** Fournir l'interface utilisateur graphique.
* **Dépendances :** `streamlit`.
* **Implémentation :**
  * Composants Streamlit pour la sélection de dossiers (`st.text_input`, `st.file_uploader` si nécessaire pour des dossiers).
  * Affichage des résultats de prévisualisation dans un tableau (`st.dataframe` ou `st.table`).
  * Widgets pour la modification manuelle des catégories (`st.selectbox`, `st.text_input`).
  * Boutons pour lancer les opérations.
  * Barre de progression (`st.progress`).
  * Affichage des logs (`st.text_area`).
* **Bonnes Pratiques :** Conception réactive. Mise à jour de l'interface utilisateur pour refléter l'état de l'opération.

-----

### 3\. Gestion de la Qualité et des Tests

* **Structure des Tests :**
  * Dossier `tests/` à la racine du projet.
  * Sous-dossiers pour les tests unitaires de chaque module (ex: `tests/unit/parsing_tests.py`, `tests/unit/ollama_classification_tests.py`).
  * Dossiers pour les tests d'intégration (ex: `tests/integration/`).
  * Dossiers pour les tests fonctionnels (ex: `tests/functional/cli_tests.py`, `tests/functional/streamlit_tests.py`).
* **Outils :**
  * **`pytest`** : Exécuteur de tests.
  * **`pytest-mock`** : Pour simuler les dépendances externes (appels réseau à Ollama, opérations de fichiers réelles).
  * **`faker`** : Pour générer des noms de fichiers, du contenu, des chemins bidons pour les tests.
  * **`pytest-cov`** : Extension de `pytest` pour la couverture de code.
  * **`ruff`** : Configuré pour s'exécuter via les hooks Git (pre-commit) ou manuellement.
  * **`yamlfix`** : Utilisé pour formater les fichiers `config.yaml`.
* **Stratégie de Test :**
  * **Tests unitaires :** Tester chaque fonction/méthode isolément. Mocker les dépendances.
  * **Tests d'intégration :** Vérifier que les modules interagissent correctement.
  * **Tests fonctionnels (CLI/Streamlit) :** Simuler l'interaction utilisateur pour s'assurer que l'application se comporte comme prévu.
* **Workflow de Développement (TDD - Test-Driven Development) :**
    1. Écrire un test qui échoue pour une nouvelle fonctionnalité.
    2. Écrire le code minimal pour faire passer le test.
    3. Refactoriser le code, en s'assurant que les tests passent toujours.
    4. Répéter.

-----

### 4\. Environnement de Développement et Déploiement

* **Gestionnaire de Paquets :** **`uv`**.
* **Dépendances Python :** Toutes les dépendances sont spécifiées dans `pyproject.toml`.
* **Dépendances Système :** Rappel que `tesseract-ocr` doit être installé sur le système hôte (en particulier macOS).
* **Ollama :** Nécessite une installation locale d'Ollama et le téléchargement des modèles LLM souhaités (ex: `ollama pull gemma3n`).