
## Addendum sur l'Organisation Avancée des Fichiers - ClassifAI

**Date :** 10 juillet 2025
**Version :** 1.1 (Addendum à la Spécification Fonctionnelle et à l'Architecture Détaillée)
**Projet :** ClassifAI
**Contexte :** Cet addendum introduit des stratégies d'organisation et de renommage plus sophistiquées, basées sur des attributs extraits du document par l'IA, tels que la langue et l'entité émettrice.

---

### 1. Organisation Basée sur la Langue

Pour une organisation optimale, les documents seront classés dans des sous-dossiers racines basés sur leur langue détectée.

* **Détection de la Langue :** Le **`parsing_module`** ou une nouvelle composante (ex: `language_detection_module`) sera responsable de détecter la langue principale du contenu textuel extrait d'un document. Des bibliothèques Python comme `langdetect` ou `fasttext` pourront être explorées pour cette tâche.
* **Structure des Dossiers :** Les dossiers de destination seront préfixés par un code de langue (ex: `fr`, `en`, `de`).
    * **Exemple de Chemin :** `/Users/fjacquet/sorted/fr/Factures/`
    * Si la langue ne peut pas être détectée avec une confiance suffisante ou est non pertinente, un dossier "Unknown" ou "Undetermined" sera utilisé (ex: `/Users/fjacquet/sorted/Unknown/Documents/`).
* **Impact sur la Classification :** Le prompt envoyé à Ollama pourra inclure la langue détectée comme information contextuelle supplémentaire, potentiellement aidant l'IA dans sa classification.

---

### 2. Renommage Basé sur la Compagnie Émettrice

Pour les documents de nature transactionnelle ou formelle, le nom de la compagnie émettrice sera extrait et utilisé dans le renommage des fichiers.

* **Types de Documents Ciblés :** Cette fonctionnalité s'appliquera principalement aux catégories de documents où une entité émettrice est fortement présente et pertinente. Les catégories incluent :
    * `Factures`
    * `Relevés Bancaires`
    * `Contrats`
    * `Rapports Techniques`
    * `Présentations`
* **Extraction de l'Émetteur par l'IA :** Le **`ollama_classification_module`** sera chargé d'extraire le nom de la compagnie émettrice.
    * Le prompt envoyé à Ollama sera enrichi pour demander spécifiquement l'identification de l'émetteur (ex: "Détecte la compagnie émettrice de ce document. Si c'est une facture, un relevé ou un contrat, identifie le nom de l'entreprise qui l'a émis. Sinon, réponds 'N/A'.").
    * L'IA devra être capable de fournir cette information dans un format structuré (ex: JSON) si le modèle le permet, ou via une extraction de texte que ClassifAI devra ensuite parse.
* **Noms de Fichier Structurés :** Les fichiers seront renommés en utilisant un format standardisé qui inclut l'émetteur, la date (si détectable) et la catégorie.
    * **Exemple de Format :** `{Catégorie}_{Émetteur}_{Date}_{TitreCourt}.{extension}`
    * **Exemple Concret :** `Facture_Orange_2025-07-10_Mobile.pdf`
    * Si l'émetteur n'est pas détecté, cette partie sera omise ou remplacée par une valeur générique.

---

### 3. Impact et Modifications des Modules

Ces améliorations nécessiteront des modifications dans plusieurs modules existants :

* **`parsing_module.py` :**
    * Intégration d'une fonction de **détection de langue**. Le résultat (code ISO 639-1) sera ajouté aux métadonnées du document.
* **`ollama_classification_module.py` :**
    * **Enrichissement des Prompts :** Les prompts de classification seront mis à jour pour demander à l'IA la langue du document et, pour les catégories spécifiques, le nom de l'émetteur.
    * **Extraction Structurée :** Développer la logique pour parser la réponse de l'IA et en extraire la langue et le nom de l'émetteur de manière fiable.
* **`file_operations_module.py` :**
    * La fonction de détermination du chemin de destination devra maintenant construire le chemin en intégrant le dossier langue (ex: `destination_root / langue_code / categorie / nom_fichier`).
    * La fonction de renommage devra générer le nouveau nom de fichier en utilisant l'émetteur et la date, en plus du titre court.
* **`config/settings.yaml` :**
    * Ajouter des options pour les catégories spécifiques nécessitant l'extraction de l'émetteur.
    * Définir des langages par défaut ou supportés.
* **`cli.py` et `streamlit_app.py` :**
    * L'affichage "dry run" devra montrer la langue détectée et l'émetteur proposé, permettant à l'utilisateur de valider ou corriger ces informations avant exécution.

---

### 4. Considérations et Complexités

* **Détection de Langue :** La précision peut varier, surtout pour les documents courts ou multilingues.
* **Extraction de l'Émetteur :** C'est une tâche **délicate pour l'IA**. Les noms de compagnie peuvent être ambigus ou absents. L'IA peut "halluciner" des noms. Il faudra un prompt très clair et une post-traitement robuste de la réponse de l'IA, potentiellement avec une phase de validation humaine pour les cas incertains.
* **Performance :** Ces étapes supplémentaires (détection de langue, extraction d'émetteur par l'IA) ajouteront du temps de traitement par document.
* **Tests :** Des jeux de données de test variés (différentes langues, documents avec et sans émetteurs clairs) seront cruciaux pour valider la robustesse de ces nouvelles fonctionnalités.

Ces ajouts transformeront ClassifAI en un outil de gestion de documents vraiment puissant et personnalisé.