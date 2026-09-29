"""
This module provides functions for interacting with the Ollama API.
"""

from __future__ import annotations

import base64
import json
from difflib import get_close_matches
from typing import Any

import httpx
from loguru import logger
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

from classifai.config import app_config
from classifai.core.types import AIResponse, FileContext
from classifai.exceptions import LLMError
from classifai.infrastructure import knowledge_base
from classifai.localization import translate_category, translate_sector
from classifai.utils import sanitize_filename

# --- Constants ---
MAX_RETRIES = 3
TIMEOUT = 60  # seconds
FUZZY_MATCH_CUTOFF = 0.85  # Threshold for fuzzy category matching
UNKNOWN_CATEGORY = "_UNKNOWN_"


def _format_categories_for_prompt(categories: list[str]) -> str:
    """
    Format categories as a numbered list for better LLM comprehension.

    Presenting categories as a numbered list instead of a Python list
    helps the LLM copy exact strings without introducing typos.

    Args:
        categories: List of allowed category names

    Returns:
        Formatted string with numbered categories
    """
    lines = ["ALLOWED CATEGORIES (copy EXACTLY as shown - do NOT modify spelling):"]
    for i, cat in enumerate(categories, 1):
        lines.append(f"    {i}. {cat}")
    return "\n".join(lines)


def _fuzzy_match_category(
    category: str, allowed: list[str], cutoff: float = FUZZY_MATCH_CUTOFF
) -> str | None:
    """
    Try to fuzzy match an invalid category to the allowed list.

    When the LLM returns a category with typos (e.g., 'Fichieurs Texte'),
    this function attempts to find the closest valid match.

    Args:
        category: The category string to match
        allowed: List of allowed category names
        cutoff: Minimum similarity ratio (0.0 to 1.0) for a match

    Returns:
        The matched category name, or None if no close match found
    """
    matches = get_close_matches(category, allowed, n=1, cutoff=cutoff)
    return matches[0] if matches else None


@retry(
    stop=stop_after_attempt(MAX_RETRIES),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    retry=retry_if_exception_type(httpx.RequestError),
    reraise=True,
)
def _make_request(endpoint: str, payload: dict[str, Any], api_url: str) -> dict[str, Any]:
    """
    Makes a request to the Ollama API with retry logic using tenacity.

    Args:
        endpoint: API endpoint path
        payload: Request payload
        api_url: Base URL of the Ollama API

    Returns:
        API response as dictionary

    Raises:
        LLMError: If the API returns an HTTP error status
        httpx.RequestError: If the request still fails after all retries
    """
    try:
        with httpx.Client(timeout=TIMEOUT) as client:
            response = client.post(f"{api_url}{endpoint}", json=payload)
            response.raise_for_status()
            return response.json()
    except httpx.HTTPStatusError as e:
        logger.error(f"Ollama API returned an error: {e.response.status_code}")
        logger.error(f"Response body: {e.response.text}")
        raise LLMError(f"Ollama API error: {e.response.status_code}") from e
    except httpx.RequestError as e:
        logger.warning(f"Request to Ollama failed: {e}")
        raise  # Let tenacity handle the retry


def get_completion(prompt: str, model_name: str | None = None, api_url: str | None = None) -> dict[str, Any]:
    """
    Gets a completion from the Ollama API.

    ``model_name`` and ``api_url`` default to the configured values when None.
    """
    payload = {
        "model": model_name or app_config.ollama_model_name,
        "prompt": prompt,
        "stream": False,
        "format": "json",
    }
    return _make_request("/api/generate", payload, api_url or app_config.ollama_api_url)


def get_vision_completion(
    prompt: str,
    image_bytes: bytes,
    model_name: str | None = None,
    api_url: str | None = None,
) -> dict[str, Any]:
    """
    Gets a completion from the Ollama API using a vision model.

    Ollama expects images as base64-encoded strings.
    """
    payload = {
        "model": model_name or app_config.ollama_vision_model_name,
        "prompt": prompt,
        "stream": False,
        "format": "json",
        "images": [base64.b64encode(image_bytes).decode("ascii")],
    }
    return _make_request("/api/generate", payload, api_url or app_config.ollama_api_url)


def _parse_json_response(api_response: dict[str, Any]) -> dict[str, Any]:
    """
    Extract the JSON object Ollama returns as a string under ``response``.

    Returns an empty dict when the response is missing or not a JSON object.
    """
    raw = api_response.get("response")
    if not isinstance(raw, str):
        logger.error(f"Unexpected Ollama response shape: {list(api_response)}")
        return {}
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse JSON from Ollama response: {e}")
        return {}
    return parsed if isinstance(parsed, dict) else {}


def get_sector_with_ai(
    issuer_name: str,
    content: str,
    model_name: str | None = None,
    api_url: str | None = None,
) -> str | None:
    """
    Uses an AI model to determine the business sector of an issuer.
    """
    prompt = f"""
    Based on the issuer name '{issuer_name}' and the following document text,
    what is the most likely business sector for this issuer?

    Document Text:
    ---
    {content[:2000]}
    ---

    Return a single, general business sector (e.g., "Telecommunications", "Finance", "Retail").
    Respond with only the sector name in a JSON object under the key "sector".
    Example: {{"sector": "Finance"}}
    """
    try:
        sector = _parse_json_response(get_completion(prompt, model_name=model_name, api_url=api_url)).get(
            "sector"
        )
    except (LLMError, httpx.RequestError) as e:
        logger.error(f"AI sector classification failed for '{issuer_name}': {e}")
        return None
    if not isinstance(sector, str) or not sector:
        return None
    # Traduire le secteur en français
    return translate_sector(sector)


def _build_metadata_hints(metadata: dict[str, Any]) -> str:
    """
    Build metadata hints section for the LLM prompt.

    Extracts useful metadata fields and formats them as hints
    to help the LLM with classification.

    Args:
        metadata: Dictionary of file metadata

    Returns:
        Formatted metadata hints string, or empty string if no useful metadata
    """
    if not metadata:
        return ""

    hints: list[str] = []

    # Author/creator information
    if metadata.get("author"):
        hints.append(f"- Author/Creator: {metadata['author']}")

    # Title information
    if metadata.get("title"):
        hints.append(f"- Document Title: {metadata['title']}")

    # Subject/description
    if metadata.get("subject"):
        hints.append(f"- Subject: {metadata['subject']}")
    if metadata.get("description"):
        hints.append(f"- Description: {metadata['description']}")

    # Keywords
    keywords = metadata.get("keywords")
    if keywords:
        if isinstance(keywords, list):
            keywords = ", ".join(keywords)
        hints.append(f"- Keywords: {keywords}")

    # Creation date
    if metadata.get("creation_date"):
        hints.append(f"- Creation Date: {metadata['creation_date']}")

    # Location information (for photos)
    if metadata.get("city") or metadata.get("country"):
        location_parts = []
        if metadata.get("city"):
            location_parts.append(metadata["city"])
        if metadata.get("country"):
            location_parts.append(metadata["country"])
        hints.append(f"- Location: {', '.join(location_parts)}")

    if not hints:
        return ""

    return "\n        # DOCUMENT METADATA (use as hints)\n" + "\n".join(f"        {h}" for h in hints) + "\n"


def _get_category_suggestion(
    content: str,
    categories: list[str],
    model_name: str | None = None,
    api_url: str | None = None,
) -> str | None:
    """
    Gets a category suggestion from the AI when no predefined category fits.
    This is used for the _UNKNOWN_ workflow.
    """
    prompt = f"""
    # ROLE
    You are a document classification expert.

    # TASK
    The document below could not be classified into any of the existing categories.
    Suggest a NEW category name that would be appropriate for this type of document.

    # EXISTING CATEGORIES (for reference only - do NOT use these)
    {categories}

    # RULES
    1. Suggest a concise, descriptive category name (2-4 words maximum)
    2. Use French language for the category name
    3. Make it general enough to apply to similar documents
    4. Respond with a JSON object under the key "category", e.g. {{"category": "Frais Médicaux"}}

    # DOCUMENT TO ANALYZE
    ---
    {content[:2000]}
    ---
    """
    try:
        suggestion = _parse_json_response(get_completion(prompt, model_name=model_name, api_url=api_url)).get(
            "category"
        )
    except (LLMError, httpx.RequestError) as e:
        logger.error(f"Failed to get category suggestion: {e}")
        return None
    if not isinstance(suggestion, str):
        return None
    return sanitize_filename(suggestion, allowed=" -_", replace_spaces_with="-") or None


def _vision_prompt(categories: list[str]) -> str:
    """Build the prompt for image classification with a vision model."""
    formatted_categories = _format_categories_for_prompt(categories)
    return f"""
        # ROLE
        You are a highly accurate image analysis service.

        # TASK
        Analyze the image and return a single, well-formed JSON object.

        # {formatted_categories}

        # CRITICAL RULES FOR CATEGORY
        - Copy the category string EXACTLY as shown in the numbered list above
        - Do NOT translate the category name
        - Do NOT modify the spelling or add accents
        - Do NOT create new categories that are not in the list
        - If you are unsure or no category fits, set category to `null`

        # OTHER FIELDS TO EXTRACT
        1. `issuer`: The name of the company or person that created the document.
        2. `short_title`: A very short, descriptive title for the image.
        3. `language`: The primary language (ISO 639-1 code: 'en', 'fr', 'de', etc.).

        # JSON OUTPUT SPECIFICATION
        {{
            "issuer": "string or null",
            "category": "string from the ALLOWED CATEGORIES list or null",
            "short_title": "string or null",
            "language": "string in ISO 639-1 format or null"
        }}
        """


def _text_prompt(context: FileContext) -> str:
    """Build the prompt for document text classification."""
    metadata_hints = _build_metadata_hints(context.metadata)
    formatted_categories = _format_categories_for_prompt(context.categories)
    return f"""
        # ROLE
        You are a highly accurate data extraction service.

        # TASK
        Analyze the provided document text and return a single, well-formed JSON object containing the extracted information.
        Adhere strictly to the rules and formats defined below.
{metadata_hints}
        # {formatted_categories}

        # CRITICAL RULES FOR CATEGORY
        - Copy the category string EXACTLY as shown in the numbered list above
        - Do NOT translate the category name
        - Do NOT modify the spelling or add accents
        - Do NOT create new categories that are not in the list
        - If you are unsure or no category fits, set category to `null`

        # OTHER RULES
        1.  **Issuer Priority:** To determine the `issuer`, check in this order:
            1) The company on the letterhead.
            2) The signatory of the document.
            3) The main company the document is about.
        2.  **Date Logic:** Find the main document date. Convert it to `YYYY-MM-DD` format.
            If there are multiple dates, use the issue date.
        3.  **Title Conciseness:** The `short_title` should be a concise summary of 5-10 words.
        4.  **Language Code:** The `language` must be a valid ISO 639-1 code.
        5.  **Missing Data:** If any piece of information cannot be reliably determined from the text,
            its corresponding value in the JSON must be `null`. Do not omit the key.

        # JSON OUTPUT SPECIFICATION
        {{
            "issuer": "string or null",
            "category": "string from the ALLOWED CATEGORIES list or null",
            "date": "string in YYYY-MM-DD format or null",
            "short_title": "string or null",
            "language": "string in ISO 639-1 format or null"
        }}

        # DOCUMENT TO ANALYZE
        ---
        Document Text:
        ---
        {context.content[:4000]}
        ---
        """


def _query_model(context: FileContext) -> dict[str, Any]:
    """
    Ask the text or vision model to classify the file.

    Raises:
        LLMError: If the model cannot be reached
    """
    try:
        if context.file_type == "image" and context.use_vision:
            api_response = get_vision_completion(
                _vision_prompt(context.categories),
                context.source_path.read_bytes(),
                api_url=context.ollama_url,
            )
            response = _parse_json_response(api_response)
            if isinstance(response.get("category"), str):
                response["category"] = translate_category(response["category"], context.content)
            return response
        api_response = get_completion(
            _text_prompt(context), model_name=context.ollama_model, api_url=context.ollama_url
        )
        return _parse_json_response(api_response)
    except (LLMError, httpx.RequestError, OSError) as e:
        raise LLMError(f"LLM processing failed for {context.source_path.name}: {e}") from e


def _validate_category(category: Any, allowed: list[str]) -> str | None:
    """Return *category* if allowed, its close fuzzy match, or None."""
    if not isinstance(category, str) or not category:
        return None
    if category in allowed:
        return category
    fuzzy_match = _fuzzy_match_category(category, allowed)
    if fuzzy_match:
        logger.info(f"Fuzzy matched invalid category '{category}' → '{fuzzy_match}'")
    else:
        logger.warning(f"Invalid category '{category}' not in allowed list and no fuzzy match found.")
    return fuzzy_match


def _to_ai_response(response: dict[str, Any]) -> AIResponse:
    """Keep only the string fields AIResponse knows about, so validation cannot fail."""
    fields = {
        name: value
        for name in AIResponse.model_fields
        if isinstance(value := response.get(name), str) and value
    }
    return AIResponse(**fields)


def _determine_sector(issuer: str | None, context: FileContext) -> str | None:
    """Knowledge base lookup first, then AI fallback."""
    if not issuer:
        return None
    sector = knowledge_base.get_sector_for_issuer(issuer)
    if sector:
        return sector
    logger.debug(f"Sector not found in knowledge base for '{issuer}', using AI fallback")
    return get_sector_with_ai(issuer, context.content, context.ollama_model, context.ollama_url)


def enrich_with_ai(context: FileContext) -> FileContext:
    """
    Enriches the file context with AI-powered classification.
    This is an impure function that makes a network call.
    Implements strict category enforcement with _UNKNOWN_ handling per functional specification.

    Args:
        context: The file context to enrich

    Returns:
        Updated FileContext with AI classification results

    Raises:
        LLMError: If AI processing fails
    """
    if context.rule_match_category:
        logger.debug(f"Skipping AI enrichment for {context.source_path.name} due to rule match")
        return context

    response = _query_model(context)
    response["category"] = _validate_category(response.get("category"), context.categories)

    if not response["category"]:
        logger.info(
            f"No valid category found for {context.source_path.name}. Implementing _UNKNOWN_ workflow."
        )
        response["category"] = UNKNOWN_CATEGORY
        response["category_suggestion"] = _get_category_suggestion(
            context.content,
            context.categories,
            model_name=context.ollama_model,
            api_url=context.ollama_url,
        )

    ai_response = _to_ai_response(response)
    return context.model_copy(
        update={
            "ai_results": ai_response.model_dump(exclude_none=True),
            "issuer": ai_response.issuer,
            "language": ai_response.language,
            "category": ai_response.category,
            "sector": _determine_sector(ai_response.issuer, context),
        },
    )
