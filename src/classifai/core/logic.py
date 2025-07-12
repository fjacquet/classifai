"""
Core functional logic for ClassifAI.

This module contains the pure functions responsible for making decisions
based on the data collected in the FileContext. It uses functional
constructs and avoids side effects.
"""

from datetime import datetime
from pathlib import Path
from typing import Any

from loguru import logger
from returns.maybe import Maybe, Nothing, Some
from returns.result import Result, Success

from classifai.core.types import FileContext
from classifai.localization import get_default_value


def _get_final_filename(context: FileContext) -> str:
    """Pure helper to determine the final filename."""
    # Si l'option rename_files est activée et qu'un nouveau nom est fourni par l'IA
    if context.rename_files and "new_filename" in context.ai_results:
        new_filename = context.ai_results["new_filename"]
        final_filename = "".join(c for c in new_filename if c.isalnum() or c in " -_.").rstrip()
        if not final_filename.endswith(context.source_path.suffix):
            final_filename += context.source_path.suffix
        return final_filename

    # Si l'option rename_files est activée mais qu'aucun nom n'est fourni, créer un nom descriptif
    elif context.rename_files:
        # Extraire les composants pour le nom de fichier
        date = context.ai_results.get("date", "")
        short_title = context.ai_results.get("short_title", "")
        category = context.category or context.ai_results.get("category", "")
        issuer = context.issuer or context.ai_results.get("issuer", "")

        # Nettoyer les composants
        safe_date = "".join(c for c in date if c.isalnum() or c in "-_").rstrip() if date else ""
        safe_title = (
            "".join(c for c in short_title if c.isalnum() or c in " -_").rstrip() if short_title else ""
        )
        safe_category = "".join(c for c in category if c.isalnum() or c in " -_").rstrip() if category else ""
        safe_issuer = "".join(c for c in issuer if c.isalnum() or c in " -_").rstrip() if issuer else ""

        # Construire le nom de fichier
        components = []
        if safe_date:
            components.append(safe_date)
        if safe_category:
            components.append(safe_category.lower().replace(" ", "_"))
        if safe_title:
            components.append(safe_title.replace(" ", "_"))
        if safe_issuer:
            components.append(safe_issuer.replace(" ", "_"))

        # Si aucun composant n'est disponible, utiliser le nom original
        if not components:
            return context.source_path.name

        # Joindre les composants avec des tirets
        final_filename = "-".join(components)

        # Ajouter l'extension
        if not final_filename.endswith(context.source_path.suffix):
            final_filename += context.source_path.suffix

        logger.debug(f"Generated descriptive filename: {final_filename}")
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
            date = datetime.strptime(date_str, "%Y:%m:%d %H:%M:%S")
            year = date.strftime("%Y")
            month = date.strftime("%m_%B")
            dest = photo_path / year / month
            location = context.metadata.get("location")
            if location:
                safe_location = "".join(c for c in location if c.isalnum() or c in " -_,").rstrip()
                dest = dest / safe_location
            return dest / final_filename
    except (ValueError, KeyError):
        # In case of parsing failure, return a fallback path
        return photo_path / final_filename

    return photo_path / final_filename


def _calculate_general_destination(context: FileContext) -> Path:
    """Pure helper to calculate destination for general files."""
    # Utiliser la langue du contexte si elle est définie
    # Si les sous-dossiers de langue sont activés, utiliser toujours la langue détectée
    # sinon utiliser "fr" comme langue par défaut
    lang_folder = "fr"  # Langue par défaut pour la localisation française
    if context.language_subfolders and context.language and context.language != "N/A":
        lang_folder = context.language

    # Utiliser le secteur du contexte s'il est défini, sinon utiliser la valeur par défaut
    # Assurer que le secteur est en français
    sector_folder = context.sector if context.sector else get_default_value("unknown_sector")

    # Nettoyer le nom de l'émetteur pour le chemin
    safe_issuer = (
        "".join(c for c in context.issuer if c.isalnum() or c in " -_").rstrip()
        if context.issuer
        else get_default_value("unknown_issuer")
    )

    # Utiliser la catégorie du contexte directement si elle est définie
    # Sinon, utiliser la catégorie des résultats AI ou la valeur par défaut
    category = context.category or context.ai_results.get("category") or get_default_value("unclassified")

    # Obtenir le nom de fichier final
    final_filename = _get_final_filename(context)

    # Journaliser les valeurs utilisées pour le chemin de destination
    logger.debug(
        f"Destination path components: lang={lang_folder}, sector={sector_folder}, "
        f"issuer={safe_issuer}, category={category}"
    )

    # Construire et retourner le chemin de destination
    return context.destination_dir / lang_folder / sector_folder / safe_issuer / category / final_filename


def determine_final_path(context: FileContext) -> FileContext:
    """
    Calculates the final destination path based on all gathered information.
    This is a pure function that returns an updated context.
    """
    # Journaliser l'état du contexte avant de déterminer le chemin final
    logger.debug(
        f"Context before path determination: language={context.language}, sector={context.sector}, "
        f"category={context.category}, issuer={context.issuer}"
    )

    # Handle rule-based match first
    final_path: Path
    if context.rule_match_category:
        dest_path = context.destination_dir
        if context.language_subfolders:
            dest_path = dest_path / get_default_value("na")
        final_path = (
            dest_path
            / get_default_value("unknown_sector")
            / get_default_value("unknown_issuer")
            / context.rule_match_category
            / context.source_path.name
        )
    else:
        category = context.ai_results.get("category", "Non Classé")
        if category == "Photos" and "date" in context.metadata:
            final_path = _calculate_photo_destination(context)
        else:
            # Vérifier que le secteur est bien défini avant de calculer le chemin
            logger.debug(f"Before _calculate_general_destination: sector={context.sector}")
            final_path = _calculate_general_destination(context)

    # Créer une copie mise à jour du contexte avec le chemin final
    updated_context = context.__class__(**{**context.__dict__, "final_destination_path": final_path})

    # Journaliser l'état du contexte après la mise à jour
    logger.debug(
        f"Updated context with final path: sector={updated_context.sector}, "
        f"final_path={updated_context.final_destination_path}"
    )

    return updated_context


def create_summary(result: Result[FileContext, Any]) -> Maybe[dict]:
    """
    Creates a summary dictionary from a successful result.
    Returns Nothing if the result is a Failure.
    """

    def _format(context: FileContext) -> dict:
        return {
            "File Name": context.source_path.name,
            "Language": context.language,
            "Category": context.rule_match_category
            or context.ai_results.get("category", get_default_value("unclassified")),
            "Issuer": context.issuer or get_default_value("unknown_issuer"),
            "New Filename": Maybe.from_optional(context.final_destination_path)
            .map(lambda p: Path(p).name)
            .value_or(context.source_path.name),
            "Destination Path": str(context.final_destination_path),
            "Source Path": str(context.source_path.absolute()),
            "Metadata": context.metadata,
        }

    # Convert Result to Maybe (Success -> Some, Failure -> Nothing)
    if isinstance(result, Success):
        return Some(_format(result.unwrap()))
    return Nothing
