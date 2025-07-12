"""
Main pipeline orchestration for ClassifAI.

This module uses a functional approach with the `returns` library to create a
data processing pipeline. It orchestrates functions from the `core` and
`infrastructure` modules to process files.
"""

from pathlib import Path

import pandas as pd
from returns.maybe import Nothing
from returns.pipeline import flow
from returns.pointfree import bind
from returns.result import Result, Success

from classifai.config import app_config
from classifai.core.logic import create_summary, determine_final_path
from classifai.core.rules import RulesEngine, apply_rules
from classifai.core.types import FileContext
from classifai.infrastructure.file_system import read_and_parse_file
from classifai.infrastructure.knowledge import (
    KnowledgeBase,
    enrich_with_knowledge,
)
from classifai.infrastructure.llm import enrich_with_ai


def process_file_pipeline(
    file_path: Path,
    scan_config: dict,
    rules_engine: RulesEngine,
    knowledge_base: KnowledgeBase,
) -> Result[FileContext, str]:
    """
    Orchestrates the full processing pipeline for a single file using `flow`.
    """
    initial_context = FileContext(
        source_path=file_path,
        destination_dir=Path(scan_config["dest_dir_str"]),
        rename_files=scan_config["rename_files"],
        use_vision=scan_config["use_vision"],
        language_subfolders=scan_config["language_subfolders"],
        categories=scan_config["categories"],
    )

    pipeline = flow(
        Success(initial_context),
        bind(lambda ctx: apply_rules(ctx, rules_engine)),
        bind(read_and_parse_file),
        bind(enrich_with_ai),
        bind(lambda ctx: enrich_with_knowledge(ctx, knowledge_base)),
        bind(lambda ctx: Success(determine_final_path(ctx))),
    )

    return pipeline


def run_scan(
    source_dir_str: str,
    dest_dir_str: str,
    rename_files: bool,
    use_vision: bool,
    language_subfolders: bool,
    recursive: bool,
    categories: list[str],
) -> pd.DataFrame:
    """
    Scans the source directory, classifies files using the pipeline,
    and returns a DataFrame of the results.
    """
    source_path = Path(source_dir_str)
    if not source_path.is_dir():
        return pd.DataFrame()

    # Initialize engines once per scan, using the centralized config
    rules_engine = RulesEngine(app_config.rules)
    knowledge_base = KnowledgeBase(app_config.debitors)

    scan_config = {
        "dest_dir_str": dest_dir_str,
        "rename_files": rename_files,
        "use_vision": use_vision,
        "language_subfolders": language_subfolders,
        "categories": categories,
    }

    files = list(source_path.rglob("*")) if recursive else list(source_path.iterdir())
    file_paths = [f for f in files if f.is_file()]

    results = []
    for item in file_paths:
        result: Result[FileContext, str] = process_file_pipeline(
            item, scan_config, rules_engine, knowledge_base
        )
        summary = create_summary(result)
        if summary is not Nothing:
            results.append(summary.unwrap())

    return pd.DataFrame(results)
