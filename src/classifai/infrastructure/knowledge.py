"""
Infrastructure for knowledge base interactions.

This module contains impure functions for interacting with the YAML-based
knowledge base. All I/O is wrapped to return `Result` objects.
"""

from pathlib import Path

import yaml
from loguru import logger
from returns.result import Result, Success

from classifai.core.types import FileContext
from classifai.infrastructure.llm import get_sector_with_ai

UNKNOWN_ISSUERS_PATH = Path("config/unknown_issuers.yaml")


class KnowledgeBase:
    def __init__(self, debitors: dict[str, str]):
        self.debitors = debitors

    def get_sector_for_issuer(self, issuer_name: str) -> str | None:
        """
        Finds the business sector for a given issuer name.
        """
        if not self.debitors or not issuer_name:
            return None

        issuer_lower = issuer_name.lower()
        # First, try for an exact match
        if issuer_lower in self.debitors:
            return self.debitors[issuer_lower]

        # If no exact match, try for a partial match
        for debitor, sector in self.debitors.items():
            if debitor in issuer_lower:
                logger.info(
                    f"Found partial knowledge base match: '{issuer_name}' contains '{debitor}' -> '{sector}'"
                )
                return sector

        return None


def record_unknown_issuer(issuer_name: str, sector: str):
    """Records an unknown issuer and its AI-suggested sector."""
    issuer_lower = issuer_name.lower()
    try:
        unknown_issuers = []
        if UNKNOWN_ISSUERS_PATH.exists():
            with open(UNKNOWN_ISSUERS_PATH) as f:
                content = yaml.safe_load(f)
                if content is not None:
                    unknown_issuers = content

        # Check if issuer is already recorded
        if any(entry.get("issuer") == issuer_lower for entry in unknown_issuers):
            return

        # Add new issuer and its suggested sector
        unknown_issuers.append({"issuer": issuer_lower, "sector": sector})

        # Write back to the file
        with open(UNKNOWN_ISSUERS_PATH, "w") as f:
            yaml.dump(unknown_issuers, f, sort_keys=False)
        logger.info(f"Recorded new unknown issuer '{issuer_lower}' with suggested sector '{sector}'")

    except (OSError, yaml.YAMLError) as e:
        logger.error(f"Error processing unknown issuers file: {e}")


def enrich_with_knowledge(context: FileContext, knowledge_base: KnowledgeBase) -> Result[FileContext, str]:
    """
    Enriches the context with sector information from the knowledge base.
    Can be impure if it needs to update the knowledge base (e.g., new issuer).
    """
    # Journaliser l'état du contexte avant l'enrichissement par la base de connaissances
    logger.debug(f"Before knowledge enrichment: sector={context.sector}, issuer={context.issuer}")

    # Si le secteur est déjà défini par l'IA, le préserver
    if context.sector and context.sector != "Secteur_Inconnu":
        logger.debug(f"Preserving AI-defined sector: {context.sector}")
        return Success(context)

    # Si nous avons une correspondance de règle ou pas d'émetteur, utiliser Secteur_Inconnu
    if context.rule_match_category or not context.issuer:
        updated_context = context.__class__(**{**context.__dict__, "sector": "Secteur_Inconnu"})
        logger.debug("Setting default sector due to rule match or missing issuer")
        return Success(updated_context)

    # Essayer de trouver le secteur dans la base de connaissances
    sector = knowledge_base.get_sector_for_issuer(context.issuer)
    if sector:
        logger.debug(f"Found sector in knowledge base: {sector}")

    if not sector:
        # This is an impure step that involves an AI call and file I/O
        try:
            sector = get_sector_with_ai(context.issuer, context.content, None)  # No logger
            if sector:
                logger.debug(f"Got sector from AI: {sector}")
                record_unknown_issuer(context.issuer, sector)
        except Exception as e:
            # If the AI call fails, we just fallback, not fail the whole pipeline
            logger.error(f"Error getting sector from AI: {e}")
            sector = "Secteur_Inconnu"

    # Mettre à jour le contexte avec le secteur déterminé
    updated_context = context.__class__(**{**context.__dict__, "sector": sector or "Secteur_Inconnu"})
    logger.debug(f"After knowledge enrichment: sector={updated_context.sector}")
    return Success(updated_context)
