## Spécification Fonctionnelle - Projet ClassifAI

**Nom du Projet :** ClassifAI
**Objectif :** Organiser automatiquement les documents dans un dossier spécifié par l'utilisateur en les classifiant et en les déplaçant vers des sous-dossiers pertinents, en utilisant un modèle de langage local via Ollama et LiteLLM. Offrir une interface en ligne de commande (CLI) pour les utilisateurs techniques et une interface graphique web (Streamlit) pour une facilité d'utilisation.

-----

### 1\. Principes de Développement

* **Bonnes Pratiques Python :**
  * Respecter la PEP 8 (style de code, nommage, etc.).
  * Utiliser des docstrings clairs pour les modules, classes, fonctions et méthodes.
  * Gérer les exceptions de manière appropriée.
  * Utiliser des gestionnaires de contexte (`with`) pour les ressources (fichiers, etc.).
  * Privilégier les imports absolus.
  * Utiliser des f-strings pour le formatage de chaînes.
* **DRY (Don't Repeat Yourself) :** Éviter la duplication de code en factorisant les fonctionnalités communes dans des fonctions ou classes réutilisables.
* **KISS (Keep It Simple, Stupid) :** Concevoir des solutions aussi simples que possible pour chaque problème. Éviter la complexité inutile.
* **Tests et Qualité de Code :**
  * **Les tests ne sont pas une option.** Chaque module, fonction et classe critique doit être accompagné de tests unitaires.
  * Utiliser un framework de test : **`pytest`** pour l'exécution des tests.
  * Pour les mocks et stubs dans les tests : **`pytest-mock`**.
  * Génération de données de test réalistes : **`faker`**.
  * **Couverture de code :** Viser une couverture de code élevée (ex: >80%) pour s'assurer que la majorité du code est testée. Utiliser `coverage.py` (souvent intégré à `pytest` via `pytest-cov`).
  * Tests d'intégration pour vérifier les interactions entre les modules (parsing, IA, opérations de fichiers).
  * Tests fonctionnels pour la CLI et l'application Streamlit.
  * **Qualité statique du code :**
    * **`ruff`** pour le linting et le formatage automatique du code, garantissant le respect de la PEP 8 et d'autres conventions.
    * **`yamlfix`** pour formater et valider les fichiers YAML (notamment pour la configuration).
* **Sécurité et Confidentialité :**
  * **Utilisation de `.env` :** Toutes les informations sensibles (clés API, URLs de services externes si utilisées, etc.) doivent être chargées via des variables d'environnement, idéalement à partir d'un fichier `.env` qui ne sera **jamais committé** dans le contrôle de version (ajout au `.gitignore`). La bibliothèque `python-dotenv` sera utilisée pour charger ces variables.

-----

### 2\. Fonctionnalités Générales

* **Sélection du Dossier Source :** L'utilisateur doit pouvoir spécifier le chemin du dossier à organiser (par défaut, le dossier `~/Downloads` du système d'exploitation).
* **Mode "Dry Run" / Prévisualisation :** Avant d'appliquer les changements, l'outil doit afficher une prévisualisation des classifications proposées et des déplacements de fichiers, permettant à l'utilisateur de valider ou de modifier les suggestions.
* **Classification par IA (Ollama via LiteLLM) :** Utilisation d'un modèle de langage local (par exemple Llama2, Llama3, Mistral) servi par **Ollama** et interfacé via **LiteLLM** pour analyser le contenu des documents et déterminer la catégorie la plus pertinente.
* **Création Automatique de Dossiers :** Si un dossier de destination n'existe pas, il doit être créé automatiquement.
* **Gestion des Conflits de Noms :** En cas de fichier avec le même nom dans le dossier de destination, l'outil doit proposer une stratégie (ex: ajout d'un suffixe numérique `(1)`, `(2)`, ou demander à l'utilisateur).
* **Historique et Annulation (MVP+) :** Maintenir un journal des opérations effectuées pour permettre une annulation facile.
* **Prise en charge de divers formats :** Capacités de parsing étendues pour extraire le contenu pertinent.
* **Organisation par Langue :** Les documents sont classés dans des sous-dossiers basés sur leur langue détectée (ex: `fr`, `en`).
* **Renommage Intelligent :** Les fichiers peuvent être renommés en utilisant des informations extraites par l'IA, comme la compagnie émettrice et la date.

-----

### 3\. Modes d'Utilisation

#### 3.1. Interface en Ligne de Commande (CLI)

* **Lancement :**

    ```bash
    uv run main.py [OPTIONS]
    ```

* **Options Essentielles :**
  * `-s --source-dir <path>`: Chemin du dossier à organiser (obligatoire).
  * `-d --destination-dir <path>`: Chemin du dossier racine où les sous-dossiers classifiés seront créés (par défaut, le même que le dossier source).
  * `-m --mode <mode>`: Mode de fonctionnement (`dry-run` par défaut, `move`, `copy`).
    * `dry-run`: Prévisualise les actions sans déplacer ni copier de fichiers.
    * `move`: Déplace les fichiers vers leurs destinations classifiées.
    * `copy`: Copie les fichiers vers leurs destinations classifiées (l'original reste).
  * `-ai --ollama-model <model_name>`: Nom du modèle Ollama à utiliser (ex: `gemma3n`). Par défaut, un modèle pertinent sera choisi via `.env` ou une valeur par défaut.
  * `-url --ollama-url <url>`: URL de l'API Ollama (par défaut: `http://localhost:11434`, configurable via `.env`).
  * `-v --verbose`: Affiche plus de détails sur le processus (fichiers analysés, erreurs, etc.).
  * `--log-file <path>`: Chemin pour enregistrer les logs des opérations (par défaut: `logs/main.log`).
* **Affichage des Résultats (en mode `dry-run`) :**
  * Tableau clair listant : `Nom du Fichier Original | Catégorie Proposée | Langue | Nouveau Nom | Chemin de Destination Proposé`
  * Option pour confirmer les actions avant de les exécuter si le mode n'est pas `dry-run`.
* **Confirmation :** Demander une confirmation explicite à l'utilisateur avant d'effectuer des déplacements réels en mode `move` ou `copy`.
* **Rapports Post-Exécution :** Résumé des actions effectuées (nombre de fichiers traités, classés, déplacés/copiés, erreurs).

#### 3.2. Interface Graphique Web (Streamlit)

* **Lancement :**

    ```bash
    streamlit run classifai_app.py
    ```

* **Écran d'Accueil / Configuration :**
  * Champ de saisie pour le **Dossier Source**.
  * Champ de saisie pour le **Dossier de Destination**.
  * Champ de sélection pour le **Modèle Ollama** à utiliser (avec valeur par défaut tirée de `.env` ou code).
  * Champ de saisie pour l'**URL Ollama API** (avec valeur par défaut tirée de `.env` ou code).
  * Bouton "Scanner le dossier" pour lancer l'analyse en mode `dry-run`.
* **Section "Prévisualisation & Validation" :**
  * Affichage clair de chaque fichier détecté et de sa classification proposée.
  * Pour chaque fichier :
    * Nom du fichier original.
    * Catégorie IA suggérée.
    * Langue détectée.
    * Nouveau nom de fichier proposé.
    * Chemin de destination complet.
    * Possibilité de **modifier manuellement** les attributs suggérés.
    * Possibilité de **cocher/décocher** les fichiers à inclure ou exclure du processus.
  * Compteur de fichiers sélectionnés et actions à effectuer.
* **Boutons d'Action :**
  * "Lancer la Classification (Déplacer)" : Exécute les déplacements réels.
  * "Lancer la Classification (Copier)" : Exécute les copies réelles.
  * "Annuler" / "Réinitialiser".
* **Progression et Journal :**
  * Barre de progression pendant le scan et la classification/déplacement.
  * Zone d'affichage des logs en temps réel.
* **Personnalisation (Options Avancées - Streamlit) :**
  * Possibilité de définir des règles de classification personnalisées.
  * Gestion des "Catégories Inconnues".

-----

### 4\. Architecture Technique

* **Structure de Projet :** Organisation modulaire avec des dossiers clairs pour les sources, les tests, la documentation, etc.
* **Gestion de Projet :** Utilisation de **`uv`** pour la gestion rapide et fiable des dépendances Python.
* **Exécution :** Le produit doit a minima fonctionner sur **macOS**.
* **Configuration :** Utilisation d'un fichier de configuration (ex: `config.yaml`) pour les paramètres par défaut (catégories, etc.). Les informations sensibles ou variables d'environnement (URL Ollama, nom du modèle par défaut) seront chargées via **`.env`**. Ce fichier sera formaté et validé par `yamlfix`.
* **Modules dédiés (respectant DRY/KISS) :**
  * `parsing_module.py` : Encapsule toute la logique d'extraction de contenu.
  * `ollama_classification_module.py` : Contient l'interface avec Ollama via LiteLLM.
  * `file_operations_module.py` : Gère les déplacements/copies de fichiers.
  * `loguru` : For logging.
  * `history_module.py` : Pour le suivi des actions et l'annulation.
  * `utils.py` : Fonctions utilitaires génériques réutilisables.

-----

### 5\. Spécifications Techniques Détaillées

#### 5.1. Extraction de Contenu (Parsing)

* **Stratégie de Parsing Hiérarchique**:
    1. **Parser Spécifique**: Utiliser le parser optimisé pour l'extension (`.pdf`, `.docx`, etc.).
    2. **Parser Texte Générique**: Si aucun parser spécifique n'est trouvé, tenter une lecture en tant que texte brut (pour les `.log`, `.sh`, `.pem`, etc.).
    3. **Fallback sur Métadonnées**: En cas d'échec, utiliser le nom du fichier et les métadonnées pour la classification.
* **Prise en charge des formats (priorité) :**
  * PDF (`PyMuPDF`)
  * Images (`Pillow` + `pytesseract`)
  * Microsoft Word (`.docx` via `python-docx`)
  * Microsoft Excel (`.xlsx` via `openpyxl`)
  * Fichiers texte (`.txt`, `.md`, `.log`, `.csv`, etc.)
* **Gestion des erreurs de parsing :** Si un fichier ne peut pas être parsé, le signaler et l'ajouter à une catégorie "Non classifiable".
* **Limitation de la taille du contenu :** Pour l'IA, limiter le contenu envoyé (ex: 1000-4000 premiers caractères).

#### 5.2. Classification par IA (Ollama via LiteLLM)

* **Stratégie Hybride**:
  * **Mode Embedding (Défaut)**: Rapide, basé sur la similarité sémantique.
  * **Mode Complétion**: Plus lent, mais plus approfondi, pour une analyse contextuelle.
* **Extraction d'Entités**:
  * Le prompt demandera à l'IA d'extraire la langue et, pour certains types de documents, la compagnie émettrice.
* **Appels LiteLLM :**
  * Utilisation de `litellm.completion` pour le mode complétion.
  * Utilisation de `litellm.embedding` pour le mode embedding.
* **Robustesse :** Gérer les cas où le modèle Ollama ne répond pas ou donne une catégorie non reconnue.

#### 5.3. Gestion des Fichiers et Dossiers

* **Chemins absolus :** Travailler avec des chemins absolus pour éviter les ambiguïtés.
* **Structure de Destination**: `/destination_root/{langue}/{catégorie}/`.
* **Format de Renommage**: `{Catégorie}_{Émetteur}_{Date}_{TitreCourt}.{extension}`.
* **Sécurité :** S'assurer que les opérations de déplacement/copie ne suppriment pas accidentellement des fichiers existants sans confirmation.

-----

### 6\. Plan de Développement (Itératif)

1. **MVP (Terminé)**: CLI de base avec parsing et classification par complétion.
2. **Améliorations du Parsing**: Implémenter la stratégie de parsing hiérarchique et la gestion des erreurs.
3. **Classification par Embeddings**: Implémenter le mode de classification par embedding.
4. **Organisation Avancée**: Ajouter la détection de langue et le renommage intelligent.
5. **Streamlit UI**: Construire l'interface graphique.
6. **Fonctionnalités Futures**: Historique/annulation, règles personnalisées, etc.
