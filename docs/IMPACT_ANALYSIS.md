# Analyse d'Impact (Version Finale) : Finalisation de la Stratégie d'Organisation

**Date :** 11 juillet 2025
**Version :** 4.0
**Projet :** ClassifAI
**Auteur :** Gemini

---

## 1. Contexte

Cette analyse d'impact finale se base sur l'état actuel du projet et les spécifications détaillées du document `ADDENDUM.md`. Elle identifie les dernières tâches de développement nécessaires pour aligner complètement l'application avec les exigences fonctionnelles.

Les principaux écarts restants concernent la **structure de dossiers granulaire** et le **support de formats de fichiers spécifiques**.

---

## 2. Tâches Restantes et Impact Détaillé

### 2.1. Finalisation de la Structure de Dossiers et du Renommage

**Spécification Requise :** `Langue/Secteur_Activité/Émetteur/Catégorie/Date_Titre.ext`

L'implémentation actuelle ne crée pas le sous-dossier `{Émetteur}` et ne passe pas les informations nécessaires pour le faire.

* **Impact sur `ollama_classification_module.py` (Faible) :**
  * **Action :** S'assurer que la clé `issuer` est systématiquement retournée dans le dictionnaire de la fonction `classify_content`. La logique de prompt existe déjà, mais la propagation des données doit être vérifiée.

* **Impact sur `file_operations_module.py` (Élevé) :**
  * **Action :** La fonction `_transfer_file` doit être modifiée pour accepter un paramètre `issuer`.
  * **Action :** La logique de construction du chemin de destination doit être mise à jour pour insérer le sous-dossier de l'émetteur. L'ordre correct est `base_destination / language / issuer / category / filename`.
  * **Action :** La logique de la fonction `_get_photo_destination` doit également être revue pour s'assurer qu'elle s'intègre correctement avec cette nouvelle structure (par exemple, en n'appliquant pas le dossier `issuer` pour les photos).

* **Impact sur `classifai_app.py` (Moyen) :**
  * **Action :** La fonction `process_file` doit être mise à jour pour extraire et retourner `issuer` depuis le résultat de `classify_content`.
  * **Action :** La fonction `run_scan` doit être mise à jour pour gérer le `issuer` retourné et construire le chemin de prévisualisation correct.
  * **Action :** La fonction `execute_file_operations` doit être mise à jour pour passer le `issuer` aux fonctions `move_file` et `copy_file`.

* **Impact sur `classifai_cli.py` (Moyen) :**
  * **Action :** Le `process_file` étant partagé, les modifications se propageront. Il faudra s'assurer que la boucle `run` du CLI gère correctement le `issuer` dans le tuple de résultats et le passe à `move_file`/`copy_file`.

### 2.2. Ajout du Parser pour les Fichiers `.msg`

**Spécification Requise :** Supporter le format `.msg` via la bibliothèque `extract-msg`.

* **Impact sur `pyproject.toml` (Faible) :**
  * **Action :** Ajouter la dépendance `extract-msg`.

* **Impact sur `parsing_module.py` (Moyen) :**
  * **Action :** Créer une nouvelle fonction `parse_msg(file_path)`.
  * **Action :** Ajouter `".msg": parse_msg` au dictionnaire `specific_parsers` dans la fonction `get_parser`.

* **Impact sur `tests/` (Faible) :**
  * **Action :** Créer un nouveau fichier de test pour `parse_msg`, incluant un exemple de fichier `.msg` ou un mock.

### 2.3. Transcription Audio/Vidéo (Tâche Différée)

Cette tâche reste inchangée par rapport à l'analyse précédente et doit être abordée avec une stratégie d'importation conditionnelle pour garantir la stabilité.

---

## 3. Plan d'Action Recommandé

1. **Finaliser la Structure de Dossiers (Priorité Haute) :**
    * Modifier `file_operations_module.py`.
    * Modifier `classifai_app.py` et `classifai_cli.py` pour propager et utiliser l'information `issuer`.
    * Mettre à jour les tests existants pour valider la nouvelle structure de dossiers.
2. **Ajouter le Support `.msg` (Priorité Moyenne) :**
    * Ajouter la dépendance et implémenter la fonction de parsing et les tests associés.
3. **Ré-évaluer la Transcription Audio/Vidéo (Priorité Basse) :**
    * Tenter l'implémentation conditionnelle.

Cette approche structurée permettra de finaliser les fonctionnalités de base de manière robuste avant de s'attaquer à la tâche la plus risquée.
