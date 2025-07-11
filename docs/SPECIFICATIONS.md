## Spécification Fonctionnelle - Projet ClassifAI

**Nom du Projet :** ClassifAI
**Objectif :** Organiser automatiquement les documents dans un dossier spécifié par l'utilisateur en les classifiant et en les déplaçant vers des sous-dossiers pertinents, en utilisant une approche hybride de règles et de modèles de langage locaux (Ollama).

-----

### 1\. Principes de Développement

* **Bonnes Pratiques Python :** PEP 8, docstrings, gestion des exceptions, etc.
* **DRY (Don't Repeat Yourself) & KISS (Keep It Simple, Stupid).**
* **Tests et Qualité de Code :** `pytest`, `pytest-mock`, `faker`, `coverage.py`, `ruff`, `yamlfix`.
* **Sécurité et Confidentialité :** Utilisation de `.env` pour les informations sensibles.

-----

### 2\. Fonctionnalités Générales

* **Sélection du Dossier Source et Destination.**
* **Mode "Dry Run" / Prévisualisation.**
* **Classification Hybride :**
    1. **Base de Connaissances (`debitors.yaml`) :** Pré-classification rapide basée sur des règles définies par l'utilisateur.
    2. **IA (Ollama via LiteLLM) :** Classification sémantique pour les documents non couverts par les règles.
* **Organisation Intelligente :**
  * **Par Langue :** Crée des sous-dossiers par langue détectée (`/fr`, `/en`).
  * **Par Date et Lieu (pour les photos) :** Utilise les métadonnées EXIF pour créer des dossiers chronologiques et géographiques.
* **Renommage Structuré :** Renomme les fichiers en utilisant les informations extraites (catégorie, émetteur, date).
* **Parsing Robuste :** Utilise une stratégie hiérarchique avec `Pandoc` comme fallback pour supporter un maximum de formats.

-----

### 3\. Modes d'Utilisation

#### 3.1. Interface en Ligne de Commande (CLI)

* **Lancement :** `uv run main.py [OPTIONS]`
* **Options Clés :** `--source-dir`, `--destination-dir`, `--mode`, `--classification-mode`.
* **Affichage "Dry Run" :** Montre la catégorie, la langue, le nouveau nom et le chemin de destination proposés pour chaque fichier.

#### 3.2. Interface Graphique Web (Streamlit)

* **Lancement :** `streamlit run src/classifai/classifai_app.py`
* **Fonctionnalités :**
  * Configuration des dossiers et des modèles.
  * Tableau de prévisualisation éditable.
  * Boutons pour lancer les opérations de copie ou de déplacement.
  * (Futur) Éditeur pour le fichier `debitors.yaml`.

-----

### 4\. Architecture Technique

* **Modules Clés :** `parsing`, `knowledge_base`, `geocoding`, `ollama_classification`, `file_operations`.
* **Dépendances Système :** `pandoc` est maintenant une dépendance requise pour le parsing avancé.
* **Configuration :**
  * `.env` pour les secrets.
  * `config/settings.yaml` pour les paramètres généraux.
  * `config/debitors.yaml` pour la base de connaissances.

-----

### 5\. Plan de Développement

1. **MVP (Terminé)**: CLI de base et classification par complétion.
2. **Améliorations (En cours)**:
    * Implémenter la classification par base de connaissances.
    * Intégrer le parsing avancé avec Pandoc.
    * Ajouter l'organisation par EXIF et le géocodage.
3. **Fonctionnalités Futures**: Historique/annulation, règles personnalisées, etc.
