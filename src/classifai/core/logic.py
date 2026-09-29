"""
Core functional logic for ClassifAI.

This module contains the pure functions responsible for making decisions
based on the data collected in the FileContext. It uses functional
constructs and avoids side effects.
"""

from datetime import datetime
from pathlib import Path

from classifai.core.types import FileContext
from classifai.localization import get_default_value
from classifai.utils import (
    format_date_for_filename,
    parse_date_flexible,
    sanitize_filename,
    sanitize_path_component,
)

# Category whose files are filed by EXIF date (Photos/YYYY/MM_Month/...)
PHOTO_CATEGORY = "Images"


def _document_date(context: FileContext) -> str:
    """Pure helper: first valid date among the model's answer and the file metadata, as YYYY-MM-DD."""
    candidates = (
        context.ai_results.get("date"),
        context.metadata.get("creation_date"),
        context.metadata.get("date"),
    )
    for candidate in candidates:
        # [:19] drops timezone suffixes such as "+01:00" from EXIF/PDF dates
        parsed = parse_date_flexible(str(candidate)[:19]) if candidate else None
        if parsed:
            return format_date_for_filename(parsed)
    return ""


def _get_final_filename(context: FileContext) -> str:
    """Pure helper to determine the final filename."""
    # Si l'option rename_files est activée, créer un nom descriptif
    if context.rename_files:
        # Extraire les composants pour le nom de fichier selon la spécification: Date_Titre.ext
        date = _document_date(context)
        short_title = context.ai_results.get("short_title", "")
        category = context.category or context.ai_results.get("category", "")
        category_suggestion = context.ai_results.get("category_suggestion", "")

        # Nettoyer les composants
        safe_date = sanitize_filename(date, allowed="-_") if date else ""
        safe_title = (
            sanitize_filename(short_title, allowed=" -_", replace_spaces_with="_") if short_title else ""
        )

        # Construire le nom de fichier selon la convention Date_Titre.ext
        components = []
        if safe_date:
            components.append(safe_date)
        if safe_title:
            components.append(safe_title)

        # Pour les documents _UNKNOWN_, ajouter la suggestion de catégorie
        if category == "_UNKNOWN_" and category_suggestion:
            safe_suggestion = sanitize_filename(category_suggestion, allowed="-_")
            if safe_suggestion:
                components.append(f"suggested-{safe_suggestion}")

        # Si aucun composant n'est disponible, utiliser le nom original
        if not components:
            return context.source_path.name

        # Joindre les composants avec des underscores selon la spécification
        final_filename = "_".join(components)

        # Ajouter l'extension
        if not final_filename.endswith(context.source_path.suffix):
            final_filename += context.source_path.suffix

        return final_filename

    # Si l'option rename_files n'est pas activée, conserver le nom original
    return context.source_path.name


def _calculate_photo_destination(context: FileContext) -> Path:
    """Pure helper to calculate destination for photos."""
    base_path = context.destination_dir
    if context.language_subfolders and context.language != "N/A":
        base_path = base_path / context.language

    photo_path = base_path / "Photos"
    final_filename = _get_final_filename(context)

    try:
        # This logic can fail if date is not present or format is wrong
        date_str = context.metadata.get("date")
        if date_str:
            from datetime import timezone

            date = datetime.strptime(date_str, "%Y:%m:%d %H:%M:%S").replace(tzinfo=timezone.utc)
            year = date.strftime("%Y")
            month = date.strftime("%m_%B")
            dest = photo_path / year / month
            location = context.metadata.get("location")
            if location:
                safe_location = sanitize_filename(location, allowed=" -_,")
                dest = dest / safe_location
            return dest / final_filename
    except (ValueError, KeyError):
        # In case of parsing failure, return a fallback path
        return photo_path / final_filename

    return photo_path / final_filename


def _language_folder(context: FileContext) -> str:
    """Pure helper: detected language when subfolders are enabled, "fr" otherwise."""
    if context.language_subfolders and context.language and context.language != "N/A":
        return context.language
    return "fr"  # Langue par défaut pour la localisation française


def _calculate_general_destination(context: FileContext) -> Path:
    """Pure helper to calculate destination for general files."""
    lang_folder = _language_folder(context)

    # Utiliser le secteur du contexte s'il est défini, sinon utiliser la valeur par défaut
    # Assurer que le secteur est en français
    sector_folder = context.sector if context.sector else get_default_value("unknown_sector")

    # Nettoyer le nom de l'émetteur pour le chemin
    safe_issuer = sanitize_path_component(context.issuer or "") or get_default_value("unknown_issuer")

    # Utiliser la catégorie du contexte directement si elle est définie
    # Sinon, utiliser la catégorie des résultats AI ou la valeur par défaut
    category = context.category or context.ai_results.get("category") or get_default_value("unclassified")

    # Obtenir le nom de fichier final
    final_filename = _get_final_filename(context)

    # Construire et retourner le chemin de destination
    return context.destination_dir / lang_folder / sector_folder / safe_issuer / category / final_filename


def determine_final_path(context: FileContext) -> FileContext:
    """
    Calculates the final destination path based on all gathered information.
    This is a pure function that returns an updated context.
    """
    # Handle rule-based match first
    final_path: Path
    if context.rule_match_category:
        dest_path = context.destination_dir
        if context.language_subfolders:
            dest_path = dest_path / _language_folder(context)
        final_path = (
            dest_path
            / get_default_value("unknown_sector")
            / get_default_value("unknown_issuer")
            / context.rule_match_category
            / context.source_path.name
        )
    else:
        if context.category == PHOTO_CATEGORY and "date" in context.metadata:
            final_path = _calculate_photo_destination(context)
        else:
            final_path = _calculate_general_destination(context)

    # Créer une copie mise à jour du contexte avec le chemin final
    return context.model_copy(update={"final_destination_path": final_path})


def create_summary(context: FileContext | None) -> dict | None:
    """
    Creates a summary dictionary from a FileContext.
    Returns None if context is None.

    Args:
        context: The file context to summarize, or None

    Returns:
        Summary dictionary or None if context is None
    """
    if context is None:
        return None

    # Determine the new filename from final_destination_path
    new_filename = context.source_path.name
    if context.final_destination_path:
        new_filename = Path(context.final_destination_path).name

    return {
        "File Name": context.source_path.name,
        "Language": context.language,
        "Category": context.rule_match_category
        or context.ai_results.get("category", get_default_value("unclassified")),
        "Issuer": context.issuer or get_default_value("unknown_issuer"),
        "New Filename": new_filename,
        "Destination Path": str(context.final_destination_path) if context.final_destination_path else "",
        "Source Path": str(context.source_path.absolute()),
        "Metadata": context.metadata,
    }
