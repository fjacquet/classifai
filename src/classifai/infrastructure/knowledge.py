"""
Knowledge module for backward compatibility.

This module re-exports functionality from knowledge_base.py to maintain
backward compatibility with existing code that imports from this module.
"""

from classifai.infrastructure.knowledge_base import (
    UNKNOWN_ISSUERS_PATH,
    KnowledgeBase,
    load_categories,
    load_sector_issuer_mapping,
    record_unknown_issuer,
)

__all__ = [
    "KnowledgeBase",
    "load_categories",
    "load_sector_issuer_mapping",
    "record_unknown_issuer",
    "UNKNOWN_ISSUERS_PATH",
]
