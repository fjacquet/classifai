# Architecture et Conception Détaillée - ClassifAI

**Date :** 11 juillet 2025
**Version :** 2.0
**Projet :** ClassifAI
**Objectif :** Ce document décrit l'architecture générale, le flux de travail, et la conception détaillée des modules clés du projet ClassifAI.

---

### 1. Vue d'Ensemble de l'Architecture

ClassifAI adopte une architecture modulaire pour faciliter le développement et la maintenance.

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

### 2. Flux de Classification et d'Organisation

Le processus de classification suit une logique d'enrichissement progressif :

1. **Parsing du Document**: Le contenu et les métadonnées du fichier sont extraits.
2. **Classification et Extraction par IA**: Le contenu est envoyé à Ollama pour extraire la `Catégorie` et l'`Émetteur`.
3. **Enrichissement via la Base de Connaissances**: Le `Secteur d'Activité` est récupéré depuis `debitors.yaml` en utilisant l'`Émetteur`.
4. **Construction du Chemin Final**: Le `core_logic` assemble le chemin final en utilisant le format : .
5. **Création de l'Arborescence**: Le `file_operations_module` crée la structure de dossiers si elle n'existe pas.

---

### 3. Conception Détaillée des Modules

#### 3.1. Module `parsing` (Stratégie Hiérarchique)

* **Objectif :** Maximiser l'extraction de contenu de manière robuste.
* **Stratégie :**
    1. **Parsers Spécifiques (Python Natif) :** `PyMuPDF` pour `.pdf`, `python-docx` pour `.docx`, `openpyxl` pour `.xlsx`, `Pillow` pour les métadonnées d'images, `extract-msg` pour `.msg`.
    2. **Parser Texte Générique :** Pour les extensions de type texte (`.log`, `.csv`, `.md`, etc.).
    3. **Fallback Universel (`Pandoc`) :** Pour les formats de documents restants. `Pandoc` est une dépendance système externe.
    4. **Fallback sur Métadonnées :** Si tout le reste échoue, utilise le nom du fichier pour la classification.
* **Extraction EXIF :** Le parser d'images extraira les données EXIF, y compris les informations GPS pour le géocodage.

#### 3.2. Module `knowledge_base`

* **Objectif :** Fournir une couche d'abstraction pour interroger le fichier `debitors.yaml`.
* **Implémentation :**
  * Charge le fichier `debitors.yaml` au démarrage.
  * Fournit une fonction `get_sector_for_issuer(issuer_name)` pour rechercher un secteur d'activité.

#### 3.3. Module `ollama_classification`

* **Objectif :** Classifier les documents et extraire les informations pertinentes.
* **Prompt :** Le prompt est conçu pour extraire la `Catégorie` et l'`Émetteur` dans un format JSON structuré.

#### 3.4. Module `file_operations`

* **Objectif :** Gérer la création des chemins de destination et les opérations sur les fichiers.
* **Logique de Renommage :**
  * Utilise les informations extraites (Catégorie, Émetteur, Date) pour créer des noms de fichiers structurés au format `YYYY-MM-DD_Titre_Court_Document.ext`.
  * Un mécanisme de fallback est en place si le nom de fichier généré par l'IA est invalide.

---

### 4. Configuration

* **`.env`**: Pour les informations sensibles (clés API, URLs).
* **`config/categories.yaml`**: Liste des catégories de documents possibles.
* **`config/debitors.yaml`**: Mappe les émetteurs à leur secteur d'activité.
* **`config/settings.yaml`**: Pour les autres paramètres de l'application.
