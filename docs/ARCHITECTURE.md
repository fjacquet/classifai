## Architecture et Conception Détaillée - ClassifAI

**Date :** 11 juillet 2025
**Version :** 1.2
**Projet :** ClassifAI
**Objectif :** Ce document décrit l'architecture générale et la conception détaillée des modules clés du projet ClassifAI.

-----

### 1\. Vue d'Ensemble de l'Architecture

ClassifAI adopte une architecture modulaire pour faciliter le développement et la maintenance.

```
+----------------------+     +-------------------------+
|                      |     |                         |
|   UI (CLI / Streamlit)|---->|  Main Application Logic |
|                      |     |                         |
+----------------------+     +-------------------------+
            ^                            |
            |                            v
+--------------------------+     +-------------------------+
|                          |     |                         |
|   Configuration          |     |  Classification Module  |
| (.env, settings.yaml,    |<----|  (Hybrid: Rules + AI)   |
|  debitors.yaml)          |     |                         |
+--------------------------+     +-------------------------+
                                             |
                                             v
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

**Composants Clés :**

* **Main Application Logic :** Orchestre le flux de travail.
* **UI (CLI / Streamlit) :** Interfaces utilisateur.
* **Configuration :** Gère tous les fichiers de configuration.
* **Classification Module :** Moteur de classification hybride.
* **Knowledge Base Module :** Gère la base de connaissances `debitors.yaml`.
* **Parsing Module :** Responsable de l'extraction de contenu et de métadonnées.
* **Geocoding Module :** Convertit les coordonnées GPS en noms de lieux.
* **File Operations Module :** Gère les opérations sur les fichiers.

-----

### 2\. Conception Détaillée des Modules

#### 2.1. Module `parsing` (Stratégie Hiérarchique)

* **Objectif :** Maximiser l'extraction de contenu de manière robuste.
* **Stratégie :**
    1. **Parsers Spécifiques (Python Natif) :** `PyMuPDF` pour `.pdf`, `python-docx` pour `.docx`, `openpyxl` pour `.xlsx`, `Pillow` pour les métadonnées d'images.
    2. **Parser Texte Générique :** Pour les extensions de type texte (`.log`, `.csv`, `.md`, etc.).
    3. **Fallback Universel (`Pandoc`) :** Pour les formats de documents restants. `Pandoc` est une dépendance système externe.
    4. **Fallback sur Métadonnées :** Si tout le reste échoue, utilise le nom du fichier pour la classification.
* **Extraction EXIF :** Le parser d'images extraira les données EXIF, y compris les informations GPS.

#### 2.2. Module `knowledge_base`

* **Objectif :** Fournir une couche d'abstraction pour interroger le fichier `debitors.yaml`.
* **Implémentation :**
  * Charge le fichier `debitors.yaml` au démarrage.
  * Fournit une fonction pour rechercher une catégorie basée sur un nom de débiteur (correspondance exacte et floue).

#### 2.3. Module `geocoding`

* **Objectif :** Convertir les coordonnées GPS des métadonnées EXIF en adresses lisibles.
* **Dépendances :** `geopy`.
* **Implémentation :**
  * Prend les coordonnées GPS en entrée.
  * Interroge un service de géocodage externe (ex: Nominatim/OpenStreetMap).
  * Retourne un nom de lieu (ex: "Paris, France").

#### 2.4. Module `ollama_classification` (Logique Hybride)

* **Objectif :** Classifier les documents en utilisant une approche hybride.
* **Workflow :**
    1. **Pré-classification par Base de Connaissances :** Tente d'abord de classifier le document en utilisant le `knowledge_base_module`.
    2. **Classification par IA (Fallback) :** Si la pré-classification échoue, le document est envoyé à Ollama.
        * Le prompt est enrichi avec les métadonnées extraites (nom de fichier, date, données EXIF/géocodées).
        * Supporte les modes `embedding` (rapide) et `completion` (approfondi).

#### 2.5. Module `file_operations`

* **Objectif :** Gérer la création des chemins de destination et les opérations sur les fichiers.
* **Logique de Chemin :**
  * **Photos :** `Destination/{Langue}/Photos/{Année}/{Mois}_{NomMois}/{Lieu}/{NouveauNomFichier}`
  * **Autres Documents :** `Destination/{Langue}/{Catégorie}/{NouveauNomFichier}`
* **Logique de Renommage :**
  * Utilise les informations extraites (Catégorie, Émetteur, Date) pour créer des noms de fichiers structurés.
  * Ex: `Facture_Orange_2025-07-10.pdf`
