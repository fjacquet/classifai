
## Addendum sur l'Intelligence Contextuelle et la Classification Multimédia - ClassifAI

**Date :** 11 juillet 2025
**Version :** 1.6 (Addendum mis à jour à la Spécification Fonctionnelle et à l'Architecture Détaillée)
**Projet :** ClassifAI
**Contexte :** Cet addendum décrit l'intégration de sources de connaissances externes (fichier `debitors.yaml`) pour une classification hybride, l'exploitation des métadonnées EXIF (y compris les données GPS) pour une classification et une organisation avancées des fichiers multimédias, et précise la stratégie de parsing des documents incluant l'utilisation de `Pandoc` comme solution robuste pour les formats divers, remplaçant `textract`. Il introduit également une stratégie de renommage et de structuration des dossiers plus granulaire pour les documents non-image, basée sur l'émetteur, la catégorie et la date.

---

### 1. Amélioration de la Classification via un Fichier de Connaissances des Débiteurs (`debitors.yaml`)

ClassifAI exploitera un fichier `debitors.yaml` fourni par l'utilisateur pour pré-classifier et affiner la catégorisation des documents financiers et transactionnels. Cette approche hybride combine la puissance de l'IA avec une connaissance explicite et fiable.

**1.1. Stratégie d'Intégration : Pré-classification Hybride**

* **Priorité à la Connaissance Explicite :** Avant d'interroger un modèle LLM générique (Ollama via LiteLLM) pour la classification, ClassifAI effectuera une tentative de pré-classification basée sur le contenu du `debitors.yaml`.
* **Extraction de l'Entité Clé :** Pour les documents où c'est pertinent (ex: Factures, Relevés Bancaires, Contrats, Rapports Techniques, Présentations), le module de classification tentera d'extraire le nom du débiteur, de l'émetteur, ou du tiers principal du document.
* **Logique de Correspondance :**
  * **Correspondance Exacte :** Si le nom extrait correspond exactement à une entrée dans `debitors.yaml`, la catégorie associée sera assignée avec une haute confiance.
  * **Correspondance Floue (MVP+) :** Si une correspondance exacte n'est pas trouvée, des techniques de correspondance floue (ex: distance de Levenshtein, similarité textuelle) pourront être utilisées pour trouver des noms similaires dans le `debitors.yaml`. Une catégorie sera alors suggérée avec une confiance inférieure.
* **Passage à l'IA Générique (Fallback) :** Si aucune correspondance confiante n'est trouvée dans `debitors.yaml`, le document sera alors envoyé au processus de classification standard du LLM d'Ollama, potentiellement avec le nom de l'entité extraite comme contexte additionnel dans le prompt.

**1.2. Impact sur les Modules :**

* **`config/debitors.yaml` :** Nouveau fichier de configuration contenant les mappings `Nom_Débiteur: Catégorie`.
* **`knowledge_base_module.py` (Nouveau Module - Recommandé) :**
  * Responsable du chargement, de la validation, et de l'accès efficace aux données du `debitors.yaml`.
  * Inclura des fonctions pour la recherche exacte et la correspondance floue des noms de débiteurs.
* **`ollama_classification_module.py` :**
  * **Phase de Pré-classification :** Intégrer l'appel au `knowledge_base_module` avant l'appel à LiteLLM.
  * **Gestion du Prompt :** Ajuster le prompt pour inclure l'information du débiteur (même si non matché) lorsque le fallback à l'IA générique est nécessaire.
* **`cli.py` & `streamlit_app.py` :**
  * Le rapport "dry run" indiquera la source de la classification (ex: "Débiteurs connus" vs. "IA générique").
  * Pour le Streamlit UI (MVP+), une fonctionnalité permettra à l'utilisateur d'ajouter de nouvelles entrées au `debitors.yaml` pour les débiteurs fréquemment rencontrés et non reconnus.

---

### 2. Exploitation des Données EXIF pour la Classification Multimédia (Photos)

ClassifAI tirera parti des métadonnées EXIF des images, notamment les informations GPS et temporelles, pour enrichir la classification et proposer des structures de dossiers d'organisation plus intuitives.

**2.1. Extraction et Utilisation des Données EXIF :**

* **Source de Données :** Les données EXIF seront extraites des fichiers image (ex: `.jpg`, `.png`).
* **Types d'Informations Clés :**
  * **Date et Heure de Capture :** Champs comme `DateTimeOriginal` permettront une organisation chronologique (ex:  `Photos/2025-07-11/`).
  * **Données GPS :** `GPSLatitude`, `GPSLongitude`, etc., issues des capteurs GPS des appareils photo.
    * **Géoréférencement Inverse (Reverse Geocoding) :** Les coordonnées GPS seront converties en informations de localisation lisibles par l'humain (pays, ville, lieu spécifique). Cela nécessitera une intégration avec un service de géoréférencement inverse (ex: via `geopy` et une API externe comme OpenStreetMap Nominatim API).
  * **Informations Appareil Photo :** Fabricant (`Make`), Modèle (`Model`).
  * **Descriptions/Commentaires :** `ImageDescription`, `UserComment` si renseignés.

**2.2. Stratégies d'Organisation et de Classification :**

* **Organisation Hiérarchique par Langue, Date et Lieu :** La structure des dossiers pour les photos pourra devenir très spécifique, intégrant la langue (si pertinente pour des légendes), la date de capture et la localisation géographique.
  * **Exemple de Chemin :** `~/sorted/Photos/fr/2025/07_Juillet/France/Paris/Ma_Photo_Tour_Eiffel.jpg`
* **Priorisation des Attributs :** Pour les photos, la date et le lieu (si GPS disponible et géocodé) prendront une priorité élevée dans la suggestion de chemin de destination, avant la classification sémantique pure par l'IA.
* **Contexte pour l'IA :** Les données EXIF extraites (en particulier les descriptions textuelles et les lieux géocodés) seront incluses dans le prompt de l'IA (Ollama) pour affiner la classification sémantique (ex: "Photo de vacances", "Photo de famille", "Capture d'écran").

**2.3. Impact sur les Modules :**

* **`parsing_module.py` :**
  * Améliorer la fonction de parsing d'images pour extraire toutes les métadonnées EXIF pertinentes. Utiliser `Pillow` pour cette extraction.
  * Stocker ces données dans le dictionnaire de métadonnées retourné par le parser.
* **`geocoding_module.py` (Nouveau Module - MVP+) :**
  * Contiendra la logique et les appels API pour convertir les coordonnées GPS en adresses lisibles.
  * Gérera les clés API et les limites de taux pour le service de géoréférencement.
* **`ollama_classification_module.py` :**
  * Adapter la construction du prompt pour les images afin d'inclure les métadonnées EXIF (date, heure, informations géocodées, description utilisateur).
  * **Modèles Vision (llava - MVP+) :** Pour les cas où l'OCR est faible ou absent, et qu'une classification plus riche est nécessaire, le module pourra passer l'image à un modèle Ollama Vision (`ollama/llava`) via `litellm` pour obtenir une description textuelle de l'image, qui sera ensuite utilisée par le LLM principal pour la classification sémantique.
* **`file_operations_module.py` :**
  * Modifier la logique de création des chemins de destination pour les images, en intégrant les sous-dossiers basés sur la date et la localisation.
* **`config/settings.yaml` :**
  * Ajouter des configurations pour la stratégie d'organisation des photos (par date, par lieu, par catégorie IA).
  * Paramètres pour l'API de géoréférencement inverse (URL, clé API si nécessaire).
  * Option pour activer/désactiver l'utilisation de modèles Ollama Vision pour les images.
* **`cli.py` & `streamlit_app.py` :**
  * Le rapport "dry run" et l'interface utilisateur afficheront les métadonnées EXIF extraites (date, localisation) et les chemins de destination basés sur ces informations pour validation par l'utilisateur.

---

### 3. Précisions sur la Stratégie de Parsing et de Renommage des Documents

Cette section clarifie le rôle des différents outils de parsing et de leurs dépendances système dans la stratégie globale de ClassifAI, et introduit une logique de renommage plus granulaire pour les documents non-image.

**3.1. Approche Stratégique du `parsing_module` :**

Le `parsing_module` adoptera une stratégie de parsing hiérarchique et robuste pour maximiser l'extraction d'informations à partir de divers formats :

1. **Parsing Spécifique et Prioritaire :** Tenter en premier lieu d'utiliser les parsers Python dédiés et optimisés que nous avons explicitement choisis pour les formats courants. Ces parsers sont préférés pour leur intégration native, leur vitesse et leurs fonctionnalités spécifiques :
    * **`.pdf` :**
        * **Priorité 1 :** `PyMuPDF` (Fitz) pour sa vitesse, son intégration native et ses fonctionnalités étendues.
        * **Fallback Robuste :** Si `PyMuPDF` échoue ou ne produit pas de contenu significatif, le `parsing_module` tentera d'extraire le texte via `pdftotext` (nécessitant l'installation de `poppler-utils` sur le système de l'utilisateur).
    * `.docx` via `python-docx`.
    * `.xlsx` via `openpyxl`.
    * `.pptx` via `python-pptx`.
    * Images (`.jpg`, `.jpeg`, `.png`, `.tif`, `.tiff`, `.gif`) via `Pillow` pour l'image et `pytesseract` pour l'OCR.
    * Fichiers audio (`.mp3`, `.ogg`, `.wav`) via `pydub`, `moviepy` et `SpeechRecognition`.
    * **Nouveaux Parsers Directs :** Pour des formats précédemment couverts par `textract`, nous utiliserons des bibliothèques Python dédiées et bien maintenues :
        * `.html` / `.htm` via `BeautifulSoup` (`beautifulsoup4`).
        * `.rtf` via `striprtf`.
        * `.eml` via le module `email` intégré de Python.
        * `.msg` via `extract-msg`.
2. **Parsing Texte Brut Généralisé :** Pour les extensions non spécifiquement gérées par un parser dédié ou connues pour contenir du texte (ex: `.csv`, `.json`, `.log`, `.md`, `.odt`, `.sh`, `.txt`, fichiers sans extension), le module tentera une lecture directe du fichier en tant que texte (UTF-8 par défaut, avec gestion des erreurs d'encodage).
    * **Cas Spécifiques (Sensibilité) :** `.pem`, `.ppk`, `.pass` seront traités comme du texte brut. Leur contenu sera parsé, mais la classification par l'IA devra gérer leur sensibilité de manière appropriée, potentiellement en les dirigeant vers une catégorie "Sécurité" ou "Clés" avec des recommandations de non-déplacement.
3. **Rôle de `Pandoc` (Fallback Universel) :**
    * **`Pandoc`** sera utilisé comme un **fallback universel robuste** pour les formats de documents complexes ou moins courants qui ne sont pas gérés de manière satisfaisante par nos parsers spécifiques ou le parser texte brut.
    * L'intégration se fera via un appel `subprocess.run()` à l'exécutable `pandoc` ou potentiellement via la bibliothèque `pypandoc`.
    * **Dépendance Système Obligatoire :** `Pandoc` devra être installé en tant qu'outil système sur la machine de l'utilisateur (via Homebrew sur macOS : `brew install pandoc`). Cela doit être clairement documenté.
4. **Gestion des Fichiers Binaires et Archives (MVP) :**
    * Les fichiers archives (`.zip`, `.backup`) et autres fichiers binaires inconnus qui ne peuvent pas être parsés efficacement seront traités comme **non parsables** pour leur contenu interne dans le MVP.
    * Leur classification se basera principalement sur leur nom de fichier et leur extension (ex: vers une catégorie "Archives" ou "Sauvegardes"). Un avertissement sera journalisé pour indiquer l'absence de parsing de contenu.
5. **Fallback d'Information en Cas d'Échec :** En cas d'échec complet d'extraction de contenu textuel (fichier corrompu, format non supporté, ou OCR vide), ClassifAI utilisera le **nom du fichier** et les **métadonnées du système d'exploitation** (taille, date) pour la classification. Le document sera alors classé dans une catégorie "Non classifiable" ou "Erreur de Parsing" et signalé dans les logs.

**3.2. Impact sur les Modules :**

* **`parsing_module.py` :**
  * Refonte de la fonction `parse_document` pour implémenter la logique de dispatching hiérarchique et la gestion des retours (contenu textuel, métadonnées, état de parsing).
  * Implémentation robuste du parser `openpyxl` pour `.xlsx`.
  * Intégration des appels aux nouvelles bibliothèques (`beautifulsoup4`, `striprtf`, module `email`, `extract-msg`).
  * Intégration de la logique d'appel à `Pandoc` comme dernier recours.
  * Gestion des exceptions spécifiques à chaque parser.
* **`ollama_classification_module.py` :**
  * Adapter la logique de prompt pour gérer les scénarios où le contenu parsé est vide ou incomplet.
  * **Extraction de Langue et d'Émetteur :** Le prompt sera affiné pour explicitement demander la langue détectée du document et, pour les catégories pertinentes (Factures, Relevés Bancaires, Contrats, Rapports Techniques, Présentations), le nom de la compagnie émettrice. L'IA devra fournir ces informations de manière structurée si possible.
* **`file_operations_module.py` :**
  * **Noms de Fichier Structurés et Chemins de Destination Granulaires pour Documents Non-Image :**
    * Les fichiers de catégories comme `Factures`, `Relevés Bancaires`, `Contrats`, `Rapports Techniques`, `Présentations` (et d'autres jugées pertinentes) seront renommés et déplacés en utilisant un format standardisé qui inclut la langue détectée, l'émetteur, la catégorie et la date (si détectable).
    * **Exemple de Format :** `{Dossier_Racine_Langue}/{Émetteur_Nom_Clair}/{Catégorie_Spécifique}/{Date_Document}_{Titre_Court_Document}.{extension}`
    * **Exemple Concret :** `fr/Orange/Facture/2025-07-10_Mobile.pdf`
    * Si la langue n'est pas détectée ou n'est pas pertinente, le segment `{Dossier_Racine_Langue}` sera remplacé par "Undetermined_Language" ou omis si la configuration le permet.
    * Si l'émetteur n'est pas détecté, cette partie sera remplacée par une valeur générique (ex: "Unknown_Issuer") ou omise si la configuration le permet.
    * Le `Titre_Court_Document` sera également généré par l'IA pour fournir un nom de fichier significatif.
    * Pour les autres types de documents (ex: `Code`, `Scripts`, `Divers`), un format de nommage plus simple (ex: `Catégorie/NomOriginal.extension` ou `Catégorie/TitreCourt.extension`) sera appliqué.
* **`logging_module.py` :**
  * S'assurer que les messages d'avertissement pour les parsers manquants ou les échecs de parsing sont clairs, informatifs et journalisés avec les détails pertinents.
