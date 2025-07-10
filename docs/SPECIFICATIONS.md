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
  * **Couverture de code :** Viser une couverture de code élevée (ex: \>80%) pour s'assurer que la majorité du code est testée. Utiliser `coverage.py` (souvent intégré à `pytest` via `pytest-cov`).
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

-----

### 3\. Modes d'Utilisation

#### 3.1. Interface en Ligne de Commande (CLI)

* **Lancement :**

    ```bash
    python classifai.py [OPTIONS]
    ```

* **Options Essentielles :**
  * `-s --source-dir <path>`: Chemin du dossier à organiser (obligatoire).
  * `-d --destination-dir <path>`: Chemin du dossier racine où les sous-dossiers classifiés seront créés (par défaut, le même que le dossier source).
  * `-m --mode <mode>`: Mode de fonctionnement (`dry-run` par défaut, `move`, `copy`).
    * `dry-run`: Prévisualise les actions sans déplacer ni copier de fichiers.
    * `move`: Déplace les fichiers vers leurs destinations classifiées.
    * `copy`: Copie les fichiers vers leurs destinations classifiées (l'original reste).
  * `-ai --ollama-model <model_name>`: Nom du modèle Ollama à utiliser (ex: `llama2`, `mistral`, `llama3`). Par défaut, un modèle pertinent sera choisi via `.env` ou une valeur par défaut.
  * `-url --ollama-url <url>`: URL de l'API Ollama (par défaut: `http://localhost:11434`, configurable via `.env`).
  * `-v --verbose`: Affiche plus de détails sur le processus (fichiers analysés, erreurs, etc.).
  * `--log-file <path>`: Chemin pour enregistrer les logs des opérations.
* **Affichage des Résultats (en mode `dry-run`) :**
  * Tableau clair listant : `Nom du Fichier Original | Catégorie Proposée | Chemin de Destination Proposé`
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
  * Affichage clair de chaque fichier détecté et de sa classification proposée (catégorie et chemin de destination).
  * Pour chaque fichier :
    * Nom du fichier original.
    * Catégorie IA suggérée (ex: "Factures", "Photos de Vacances", "Rapports Techniques").
    * Chemin de destination complet.
    * Possibilité de **modifier manuellement** la catégorie suggérée via une liste déroulante ou un champ de texte.
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
  * Possibilité de définir des règles de classification personnalisées (ex: si le nom contient "facture", classer dans "Factures" avant l'IA).
  * Gestion des "Catégories Inconnues" (ex: un dossier "Divers" ou "À Vérifier").

-----

### 4\. Architecture Technique

* **Structure de Projet :** Organisation modulaire avec des dossiers clairs pour les sources, les tests, la documentation, etc.
* **Gestion de Projet :** Utilisation de **`uv`** pour la gestion rapide et fiable des dépendances Python.
* **Exécution :** Le produit doit a minima fonctionner sur **macOS**.
* **Configuration :** Utilisation d'un fichier de configuration (ex: `config.yaml`) pour les paramètres par défaut (catégories, etc.). Les informations sensibles ou variables d'environnement (URL Ollama, nom du modèle par défaut) seront chargées via **`.env`**. Ce fichier sera formaté et validé par `yamlfix`.
* **Modules dédiés (respectant DRY/KISS) :**
  * `parsing_module.py` : Encapsule toute la logique d'extraction de contenu (utilisant `PyMuPDF`, `pytesseract`, `python-docx`, etc.).
  * `ollama_classification_module.py` : Contient l'interface avec Ollama via LiteLLM et la logique de mappage des classifications brutes de l'IA vers des catégories définies.
    * Implémentation des appels `litellm.completion` pour les modèles texte et potentiellement vision (`ollama/llava`) en fonction du type de contenu.
  * `file_operations_module.py` : Gère les déplacements/copies de fichiers et la résolution des conflits de noms.
  * `loguru` : For logging.
  * `history_module.py` : Pour le suivi des actions et l'annulation.
  * `utils.py` : Fonctions utilitaires génériques réutilisables.

-----

### 5\. Spécifications Techniques Détaillées

#### 5.1. Extraction de Contenu (Parsing)

* **Prise en charge des formats (priorité) :**
  * PDF (`PyMuPDF`) : Texte, métadonnées.
  * Images (`Pillow` + `pytesseract`) : Texte via OCR, métadonnées EXIF. Pour les images avec du texte, envisager l'utilisation d'un **modèle Ollama Vision comme `llava` via LiteLLM** si l'analyse d'image est plus riche que l'OCR pur.
  * Microsoft Word (`.docx` via `python-docx`) : Texte.
  * Microsoft Excel (`.xlsx` via `openpyxl`) : Texte des cellules.
  * Microsoft PowerPoint (`.pptx` via `python-pptx`) : Texte des diapositives.
  * Fichiers texte (`.txt`, `.md`, `.log`, `.csv`, etc.) : Lecture directe.
  * Fichiers audio/vidéo (`pydub`, `moviepy` + `SpeechRecognition`/`Whisper` - **MVP+**) : Transcription audio pour le contenu parlé, extraction de métadonnées.
* **Gestion des erreurs de parsing :** Si un fichier ne peut pas être parsé (corrompu, format non pris en charge), le signaler et éventuellement l'ajouter à une catégorie "Non classifiable" ou "Erreur de Parsing".
* **Limitation de la taille du contenu :** Pour l'IA, limiter le contenu envoyé (ex: 1000-4000 premiers caractères) pour des raisons de performance et de fenêtre de contexte du modèle Ollama.

#### 5.2. Classification par IA (Ollama via LiteLLM)

* **Prérequis :** L'utilisateur doit avoir un serveur Ollama installé et un ou plusieurs modèles téléchargés et disponibles localement.
* **Chargement des identifiants :** Les informations comme l'URL de l'API Ollama ou le nom du modèle par défaut seront chargées depuis le fichier `.env` ou des variables d'environnement système.
* **Prompt Engineering :** Concevoir un prompt efficace pour le modèle Ollama qui prend le contenu extrait et la nature du fichier, et demande une classification claire ou un renommage.
  * **Exemple de prompt initial :** "Given the content of this document and its file type ({file\_type}), suggest the most appropriate category for it. Possible categories include: {liste\_categories\_predéfinies}. Only return the category name."
  * Ou pour le renommage : "Based on the content of this {file\_type} file, propose a concise, descriptive, and filename-friendly title without extension or special characters. Content: {file\_content\_snippet}"
* **Appels LiteLLM :**

    ```python
    from litellm import completion
    from dotenv import load_dotenv
    import os

    load_dotenv() # Charge les variables du fichier .env

    # Récupérer les infos depuis les variables d'environnement, avec des valeurs par défaut si non trouvées
    OLLAMA_MODEL_NAME = os.getenv("OLLAMA_MODEL_NAME", "llama2")
    OLLAMA_API_URL = os.getenv("OLLAMA_API_URL", "http://localhost:11434")

    # Logique pour déterminer le préfixe du modèle (ollama_chat/ ou ollama/)
    model_prefix = "ollama_chat/" if "chat" in OLLAMA_MODEL_NAME.lower() else "ollama/"
    model_to_use = f"{model_prefix}{OLLAMA_MODEL_NAME}"

    response = completion(
        model=model_to_use,
        messages=[{ "content": prompt_content,"role": "user"}],
        api_base=OLLAMA_API_URL
    )
    # ... (logique pour les modèles vision comme llava si applicable)
    ```

* **Catégories par défaut :** Définir un ensemble de catégories initiales (ex: `Documents`, `Images`, `Vidéos`, `Audio`, `Factures`, `CVs`, `Rapports`, `Présentations`, `Code`, `Archives`, `Divers`). Permettre leur personnalisation.
* **Robustesse :** Gérer les cas où le modèle Ollama ne répond pas (serveur non démarré, modèle non trouvé) ou donne une catégorie non reconnue.

#### 5.3. Gestion des Fichiers et Dossiers

* **Chemins absolus :** Travailler avec des chemins absolus pour éviter les ambiguïtés.
* **Sécurité :** S'assurer que les opérations de déplacement/copie ne suppriment pas accidentellement des fichiers existants sans confirmation.
* **Performance :** Optimiser les opérations sur les répertoires pour les grands volumes de fichiers.

-----

### 6\. Plan de Développement (Itératif)

1. **Préparation de l'environnement :**
      * S'assurer que **Ollama est installé et fonctionnel sur macOS**.
      * Télécharger un modèle de base (ex: `llama2` ou `llama3`) via `ollama pull <model_name>`.
      * Utilisation de **`uv`** pour gérer toutes les dépendances Python, y compris **`python-dotenv`**.
      * Mettre en place la structure de projet et les outils de test (`pytest`, `pytest-mock`, `faker`, `coverage.py`).
      * Configurer les outils de qualité de code (`ruff`, `yamlfix`).
      * Créer un fichier `.env.example` et l'ajouter au `.gitignore`.
2. **MVP (Minimum Viable Product) - CLI de Base :**
      * Implémentation du scan de dossier et du parsing pour quelques formats clés (PDF, TXT, DOCX, PNG/JPG via OCR).
      * **Intégration de la lecture des variables d'environnement depuis `.env` pour la configuration Ollama.**
      * Intégration initiale de **Ollama via LiteLLM** pour la classification, avec gestion des paramètres de modèle et d'URL.
      * Fonctionnalité "dry-run" avec affichage des propositions.
      * Fonctionnalité de déplacement/copie avec confirmation.
      * **Écriture des tests unitaires et d'intégration essentiels (avec couverture) pour ces fonctionnalités, en utilisant des mocks pour les appels externes (Ollama/LiteLLM).**
3. **Améliorations CLI (MVP+) :**
      * Gestion complète des erreurs et logging.
      * Options CLI avancées.
      * Amélioration des prompts et gestion des catégories.
      * Ajout de plus de formats de parsing.
      * **Extension de la suite de tests et amélioration de la couverture. Application de `ruff` et `yamlfix`.**
4. **Implémentation Streamlit :**
      * Construction de l'interface utilisateur Streamlit autour des fonctionnalités CLI existantes.
      * Ajout de la modification manuelle des classifications.
      * Progression et affichage des logs en temps réel.
      * **Tests fonctionnels pour l'interface Streamlit.**
5. **Fonctionnalités Avancées (Futures itérations) :**
      * Historique et annulation.
      * Règles de classification personnalisées (ex: "si le nom contient X, alors Y").
      * Renommage de fichiers par IA.
      * Surveillance de dossier en arrière-plan.
      * Support avancé des modèles Vision d'Ollama (`llava`) pour des classifications plus riches sur les images.
