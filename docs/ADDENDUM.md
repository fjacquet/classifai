
## Addendum sur la Gestion des Types de Fichiers et des Erreurs de Parsing - ClassifAI

**Date :** 10 juillet 2025
**Version :** 1.0 (Addendum à la Spécification Fonctionnelle et à l'Architecture Détaillée)
**Projet :** ClassifAI
**Contexte :** Cet addendum adresse les messages d'avertissement rencontrés lors du parsing de certains types de fichiers ("No parser found for file type: .ext") et les échecs d'extraction de contenu (ex: "Could not parse content from .png"). Il détaille les stratégies et les implémentations pour rendre ClassifAI plus robuste et tolérant aux erreurs.

---

### 1. Stratégie Générale de Parsing Améliorée

Le `parsing_module` de ClassifAI adoptera une stratégie de parsing hiérarchique et robuste pour maximiser la capacité à extraire des informations, même face à des formats inconnus ou des erreurs :

1. **Parsing Spécifique au Format :** Tenter en premier lieu d'utiliser le parser dédié et optimisé pour l'extension de fichier connue (ex: `PyMuPDF` pour `.pdf`, `openpyxl` pour `.xlsx`, etc.).
2. **Parsing Texte Brut Généralisé :** Si aucun parser spécifique n'est trouvé pour l'extension, ou si l'extension est connue pour contenir du texte brut (ex: `.log`, `.sh`, `.pem`, `.ppk`, `.pass`, les fichiers sans extension), tenter une lecture directe du fichier en tant que texte (UTF-8, avec gestion des erreurs d'encodage).
3. **Fallback d'Information :** En cas d'échec complet de l'extraction de contenu textuel (qu'il s'agisse d'un problème de parser, de fichier corrompu, ou d'absence de texte significatif), ClassifAI utilisera les informations disponibles :
    * Le **nom du fichier**.
    * Les **métadonnées du fichier** (taille, date de création/modification, type MIME détecté par le système d'exploitation).
    * Une **catégorie par défaut** indiquant un échec de parsing ou un type inconnu.
4. **Signalement des Erreurs :** Chaque échec de parsing sera journalisé comme un avertissement (`WARNING`) ou une erreur (`ERROR`) via `loguru`, fournissant des détails sur le fichier et la raison de l'échec.

---

### 2. Solutions Spécifiques par Type de Fichier

#### 2.1. Fichiers `.xlsx` (Microsoft Excel)

* **Problème rencontré :** "No parser found for file type: .xlsx".
* **Solution :**
  * **Priorité Élevée :** Confirmer que l'intégration de `openpyxl` dans le `parsing_module` est complète et fonctionnelle.
  * Le parser `.xlsx` devra lire toutes les feuilles de calcul et extraire le contenu textuel de chaque cellule pertinente.
  * Les tests seront renforcés pour couvrir divers scénarios de fichiers `.xlsx`.

#### 2.2. Fichiers Texte Génériques (ex: `.log`, `.sh`, `.pem`, `.ppk`, `.pass`, fichiers sans extension)

* **Problème rencontré :** "No parser found for file type: .log", "No parser found for file type: .sh", etc.
* **Solution :**
  * Implémenter un **parser de texte brut générique** capable de lire le contenu de n'importe quel fichier en mode texte.
  * Ce parser sera le **fallback par défaut** pour toutes les extensions non reconnues ou explicitement désignées comme du texte brut.
  * **Gestion des encodages :** Tenter la lecture en UTF-8 en premier, avec des fallbacks pour d'autres encodages courants si l'UTF-8 échoue.
  * **Considération Sécurité pour `.pem`, `.ppk`, `.pass` :** Bien que le contenu puisse être parsé textuellement, ces types de fichiers contiennent des données sensibles. La classification par l'IA doit être programmée pour les diriger vers une catégorie spécifique "Sécurité" ou "Clés" et l'outil pourrait avertir l'utilisateur avant de les déplacer, ou même refuser de les déplacer vers des destinations non sécurisées.

#### 2.3. Fichiers Archives (ex: `.zip`, `.backup`)

* **Problème rencontré :** "No parser found for file type: .zip", "No parser found for file type: .backup".
* **Solution (MVP) :**
  * Pour la version initiale, ces fichiers seront traités comme **non parsables** pour leur contenu interne.
  * Ils seront classés principalement sur la base de leur **nom de fichier** et de leur **extension** (ex: dans une catégorie "Archives" ou "Sauvegardes").
  * Le log d'avertissement sera toujours émis pour indiquer l'absence de parsing de contenu interne.
* **Amélioration Future (MVP+) :** Envisager un parser avancé capable de lister les fichiers à l'intérieur de l'archive ou d'extraire un petit échantillon de contenu pour une analyse plus poussée par l'IA.

#### 2.4. Échecs de Parsing d'Images (ex: `.png` avec "Could not parse content")

* **Problème rencontré :** "Could not parse content from ... .png" (impliquant un échec d'OCR).
* **Solution :**
  * **Robustesse de l'OCR :** Le parser d'images utilisant `pytesseract` sera rendu plus tolérant. Si Tesseract ne détecte aucun texte, le contenu textuel sera simplement vide, sans générer d'erreur, mais avec un log de niveau DEBUG ou INFO pour indiquer "OCR returned no text".
  * **Fallback d'Informations :** Si l'OCR ne produit pas de texte, le `ollama_classification_module` utilisera les **métadonnées de l'image** (dimensions, format, données EXIF si disponibles) et le **nom du fichier** comme principales sources d'information pour la classification.
  * **Intégration d'Ollama Vision (`llava`) (MVP+) :**
    * Pour les images où l'OCR est insuffisant (texte absent, illisible, ou besoin d'une compréhension visuelle), ClassifAI pourra, si configuré, envoyer l'image encodée en Base64 au modèle `ollama/llava` via `litellm`.
    * La description textuelle générée par `llava` servira alors de contenu principal pour la classification par le modèle LLM principal (e.g., Llama3). Cela améliorera considérablement la classification des images non textuelles.

---

### 3. Impact sur les Modules

* **`parsing_module.py` :**
  * Refonte de la fonction `parse_document` pour implémenter la logique de dispatching hiérarchique (spécifique -> texte brut -> fallback).
  * Ajout de la gestion des exceptions spécifiques à chaque parser pour un reporting plus granulaire.
* **`ollama_classification_module.py` :**
  * Adapter la logique de prompt pour gérer les scénarios où le contenu textuel est vide (utiliser alors le nom du fichier et les métadonnées).
  * Intégrer les appels à `litellm.completion` avec `ollama/llava` si l'option de classification par vision est activée pour les images.
* **`config/settings.yaml` :**
  * Possibilité de définir les extensions à traiter comme du texte brut générique.
  * Option pour activer/désactiver l'utilisation de modèles Ollama Vision pour les images.
* **`logging_module.py` :**
  * S'assurer que les messages d'avertissement sont clairs et informatifs, distinguant les "pas de parser" des "parsing échoué".
