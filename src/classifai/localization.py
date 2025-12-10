"""
Module de localisation pour ClassifAI.
Permet de traduire les textes de l'application dans différentes langues.
"""

from contextvars import ContextVar
from enum import Enum


class Language(Enum):
    """Langues supportées par l'application."""

    EN = "en"
    FR = "fr"


# Dictionnaire de traduction
TRANSLATIONS: dict[Language, dict[str, str]] = {
    Language.EN: {
        # CLI messages
        "starting_classifai": "Starting ClassifAI in {mode} mode.",
        "source_directory": "Source directory: {source_dir}",
        "destination_directory": "Destination directory: {destination_dir}",
        "ollama_model": "Ollama model: {model}",
        "classification_preview": "Classification Preview",
        "file_name": "File Name",
        "language": "Language",
        "category": "Category",
        "issuer": "Issuer",
        "new_filename": "New Filename",
        "destination_path": "Destination Path",
        "operations_summary": "Operations Summary",
        "files_to_process": "Files to process: {count}",
        "executing_operations": "Executing operations...",
        "operation_completed": "Operation completed successfully.",
        "no_files_found": "No files found for processing.",
        # Default values
        "unknown_issuer": "Unknown_Issuer",
        "unknown_sector": "Secteur_Inconnu",
        "unclassified": "Non Classé",
        "na": "N/A",
    },
    Language.FR: {
        # CLI messages
        "starting_classifai": "Démarrage de ClassifAI en mode {mode}.",
        "source_directory": "Répertoire source : {source_dir}",
        "destination_directory": "Répertoire de destination : {destination_dir}",
        "ollama_model": "Modèle Ollama : {model}",
        "classification_preview": "Aperçu de la Classification",
        "file_name": "Nom du Fichier",
        "language": "Langue",
        "category": "Catégorie",
        "issuer": "Émetteur",
        "new_filename": "Nouveau Nom",
        "destination_path": "Chemin de Destination",
        "operations_summary": "Résumé des Opérations",
        "files_to_process": "Fichiers à traiter : {count}",
        "executing_operations": "Exécution des opérations...",
        "operation_completed": "Opération terminée avec succès.",
        "no_files_found": "Aucun fichier trouvé pour le traitement.",
        # Default values
        "unknown_issuer": "Émetteur_Inconnu",
        "unknown_sector": "Secteur_Inconnu",
        "unclassified": "Non Classé",
        "na": "N/A",
    },
}


# Langue par défaut
DEFAULT_LANGUAGE = Language.EN

# Mappages de traduction pour les secteurs
SECTOR_MAPPINGS: dict[str, str] = {
    "Healthcare": "Santé",
    "Health": "Santé",
    "Medical": "Médical",
    "Finance": "Finance",
    "Banking": "Banque",
    "Insurance": "Assurance",
    "Education": "Éducation",
    "Government": "Gouvernement",
    "Technology": "Technologie",
    "Tech": "Technologie",
    "IT": "Informatique",
    "Retail": "Commerce de détail",
    "Manufacturing": "Fabrication",
    "Energy": "Énergie",
    "Transportation": "Transport",
    "Telecom": "Télécommunications",
    "Legal": "Juridique",
    "Real Estate": "Immobilier",
    "Media": "Médias",
    "Entertainment": "Divertissement",
    "Food": "Alimentation",
    "Agriculture": "Agriculture",
    "Construction": "Construction",
    "Hospitality": "Hôtellerie",
    "Tourism": "Tourisme",
    "Automotive": "Automobile",
    "Aerospace": "Aérospatiale",
    "Defense": "Défense",
    "Pharmaceutical": "Pharmaceutique",
    "Biotech": "Biotechnologie",
    "Consulting": "Conseil",
    "Logistics": "Logistique",
    "Nonprofit": "Organisation à but non lucratif",
    "NGO": "ONG",
    "Sports": "Sports",
    "Fitness": "Fitness",
    "Art": "Art",
    "Fashion": "Mode",
    "Beauty": "Beauté",
    "Environment": "Environnement",
    "Research": "Recherche",
    "Science": "Science",
}

# Mappages de traduction pour les catégories spécifiques
CATEGORY_MAPPINGS: dict[str, str] = {
    # Standard translations
    "Letters": "Lettres",
    "Lettres": "Lettres",
    "Prescription": "Ordonnances",
    "Prescriptions": "Ordonnances",
    "Medical Prescription": "Ordonnances",
    "Thermal Prescription": "Ordonnances",
    "Thermale Prescription": "Ordonnances",
    "Ordonnance": "Ordonnances",
    "Ordonnances": "Ordonnances",
    "Invoice": "Factures",
    "Invoices": "Factures",
    "Facture": "Factures",
    "Factures": "Factures",
    "Contract": "Contrats",
    "Contracts": "Contrats",
    "Contrat": "Contrats",
    "Contrats": "Contrats",
    "Report": "Rapports",
    "Reports": "Rapports",
    "Rapport": "Rapports",
    "Rapports": "Rapports",
    "Certificate": "Certificats",
    "Certificates": "Certificats",
    "Certificat": "Certificats",
    "Certificats": "Certificats",
    # Common typos and variations
    "Fiichiers Spécifiques": "Fichiers Spécifiques",
    "Fiichés Spécifiques": "Fichiers Spécifiques",
    "Fiachiers Texte": "Fichiers Texte",
    "Fiichiers Texte": "Fichiers Texte",
    "Fichers Texte": "Fichiers Texte",
    "Fiichers Texte": "Fichiers Texte",
    "Fiichiers de Code": "Fichiers de Code",
    "Fiichiers de Configuration": "Fichiers de Configuration",
    "Fiichiers E-mail": "Fichiers E-mail",
    "Fiichiers Web": "Fichiers Web",
}

# Thread-safe current language using contextvars (no global mutable state)
_current_language: ContextVar[Language] = ContextVar("language", default=DEFAULT_LANGUAGE)


def set_language(language: Language) -> None:
    """
    Définit la langue actuelle de l'application.

    This function is thread-safe - each thread/async context gets its own value.

    Args:
        language: La langue à utiliser
    """
    _current_language.set(language)


def get_current_language() -> Language:
    """
    Récupère la langue actuelle.

    Returns:
        La langue actuelle
    """
    return _current_language.get()


def get_text(key: str, **kwargs) -> str:
    """
    Récupère un texte traduit dans la langue actuelle.

    Args:
        key: La clé du texte à traduire
        **kwargs: Les paramètres à formater dans le texte

    Returns:
        Le texte traduit et formaté
    """
    current_lang = _current_language.get()
    translations = TRANSLATIONS.get(current_lang, TRANSLATIONS[DEFAULT_LANGUAGE])
    text = translations.get(key, TRANSLATIONS[DEFAULT_LANGUAGE].get(key, key))

    if kwargs:
        try:
            return text.format(**kwargs)
        except KeyError:
            # En cas d'erreur de formatage, retourner le texte non formaté
            return text

    return text


def get_default_value(key: str) -> str:
    """
    Récupère une valeur par défaut traduite.

    Args:
        key: La clé de la valeur par défaut

    Returns:
        La valeur par défaut traduite
    """
    return get_text(key)


def translate_sector(sector: str) -> str:
    """
    Traduit un secteur en français.

    Args:
        sector: Le secteur à traduire

    Returns:
        Le secteur traduit en français
    """
    if not sector:
        return get_default_value("unknown_sector")

    return SECTOR_MAPPINGS.get(sector, sector)


def translate_category(category: str, content: str | None = None) -> str:
    """
    Traduit une catégorie en français et applique des règles spécifiques.

    Args:
        category: La catégorie à traduire
        content: Le contenu du document pour analyse contextuelle (optionnel)

    Returns:
        La catégorie traduite en français
    """
    if not category:
        return get_default_value("unclassified")

    # Vérifier si c'est une ordonnance médicale basée sur le contenu
    if (
        content
        and ("ordonnance" in content.lower() or "prescription" in content.lower())
        and ("thermal" in content.lower() or "thermale" in content.lower())
    ):
        return "Ordonnances"

    # Utiliser le mappage de catégorie
    return CATEGORY_MAPPINGS.get(category, category)
