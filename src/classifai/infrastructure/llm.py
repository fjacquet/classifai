"""
This module provides functions for interacting with the Ollama API.
"""

from __future__ import annotations

from typing import Any

import httpx
from loguru import logger
from returns.result import Failure, Result, Success

from classifai.config import app_config
from classifai.core.types import AIResponse, FileContext
from classifai.localization import translate_category, translate_sector

# --- Constants ---
MAX_RETRIES = 3
TIMEOUT = 60  # seconds


def _make_request(
    endpoint: str, payload: dict[str, Any], logger_instance: Any | None = logger
) -> dict[str, Any]:
    """
    Makes a request to the Ollama API with retry logic.
    """
    for attempt in range(MAX_RETRIES):
        try:
            with httpx.Client(timeout=TIMEOUT) as client:
                response = client.post(f"{app_config.ollama_api_url}{endpoint}", json=payload)
                response.raise_for_status()
                return response.json()
        except httpx.RequestError as e:
            if logger_instance:
                logger_instance.warning(
                    f"Request to Ollama failed on attempt {attempt + 1}/{MAX_RETRIES}: {e}"
                )
            if attempt == MAX_RETRIES - 1:
                if logger_instance:
                    logger_instance.error("Ollama API request failed after all retries.")
                raise
        except httpx.HTTPStatusError as e:
            if logger_instance:
                logger_instance.error(f"Ollama API returned an error: {e.response.status_code}")
                logger_instance.error(f"Response body: {e.response.text}")
            raise
    return {}


def get_completion(
    prompt: str,
    model_name: str = app_config.ollama_model_name,
    logger_instance: Any | None = logger,
) -> dict[str, Any]:
    """
    Gets a completion from the Ollama API.
    """
    payload = {
        "model": model_name,
        "prompt": prompt,
        "stream": False,
        "format": "json",
    }
    return _make_request("/api/generate", payload, logger_instance)


def get_embedding(
    text: str,
    model_name: str = app_config.ollama_embedding_model_name,
    logger_instance: Any | None = logger,
) -> dict[str, Any]:
    """
    Gets an embedding from the Ollama API.
    """
    payload = {"model": model_name, "prompt": text}
    return _make_request("/api/embeddings", payload, logger_instance)


def get_vision_completion(
    prompt: str,
    image_bytes: bytes,
    model_name: str = app_config.ollama_vision_model_name,
    logger_instance: Any | None = logger,
) -> dict[str, Any]:
    """
    Gets a completion from the Ollama API using a vision model.
    """
    payload = {
        "model": model_name,
        "prompt": prompt,
        "stream": False,
        "format": "json",
        "images": [image_bytes.hex()],
    }
    return _make_request("/api/generate", payload, logger_instance)


def get_sector_with_ai(issuer_name: str, content: str, logger_instance: Any | None = logger) -> str | None:
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
        api_response = get_completion(prompt, logger_instance=logger_instance)
        logger_instance.debug(f"Sector API response: {api_response}")

        # Parse the JSON string from response['response']
        if "response" in api_response and isinstance(api_response["response"], str):
            try:
                import json

                response = json.loads(api_response["response"])
                logger_instance.debug(f"Parsed JSON from sector API response: {response}")
                sector = response.get("sector", None)
                logger.debug(f"Parsed JSON from sector API response: {sector}")
                # Traduire le secteur en français
                translated_sector = translate_sector(sector)
                logger.debug(f"Translated sector: {sector} -> {translated_sector}")
                return translated_sector
            except json.JSONDecodeError as e:
                logger_instance.error(f"Failed to parse JSON from sector API response: {e}")
        elif "sector" in api_response:
            sector = api_response["sector"]
            logger.debug(f"Parsed JSON from sector API response: {sector}")
            # Traduire le secteur en français
            translated_sector = translate_sector(sector)
            logger.debug(f"Translated sector: {sector} -> {translated_sector}")
            return translated_sector
    except Exception as e:
        if logger_instance:
            logger_instance.error(f"AI sector classification failed for '{issuer_name}': {e}")
    return None


def enrich_with_ai(context: FileContext) -> Result[FileContext, str]:
    """
    Enriches the file context with AI-powered classification.
    This is an impure function that makes a network call.
    """
    logger.debug(f"Starting AI enrichment for {context.source_path.name}")

    if context.rule_match_category:
        logger.debug(f"Skipping AI enrichment for {context.source_path.name} due to rule match")
        return Success(context)

    # Choose the right prompt and model based on file type
    if context.file_type == "image" and context.use_vision:
        prompt = f"""
        Analyze the image and provide the following information in a JSON object:
        1.  `issuer`: The name of the company or person that created the document.
        2.  `category`: Classify the image into one of the following categories: {context.categories}.
        3.  `short_title`: A very short, descriptive title for the image.
        4.  `language`: The primary language of the document (e.g., 'en', 'fr', 'de', etc.). Use ISO 639-1 codes.
        """
        try:
            logger.debug(f"Calling vision model API for {context.source_path.name}")
            api_response = get_vision_completion(prompt, context.content)
            logger.debug(f"Vision model API response: {api_response}")

            # Parse the JSON string from response['response']
            if "response" in api_response and isinstance(api_response["response"], str):
                try:
                    import json

                    response = json.loads(api_response["response"])
                    logger.debug(f"Parsed JSON from vision API response: {response}")

                    # Traduire la catégorie en français si nécessaire
                    if "category" in response:
                        original_category = response["category"]
                        response["category"] = translate_category(original_category, context.content)
                        logger.debug(f"Translated category: {original_category} -> {response['category']}")
                except json.JSONDecodeError as e:
                    logger.error(f"Failed to parse JSON from vision API response: {e}")
                    response = {}
            else:
                response = api_response
        except Exception as e:
            logger.error(f"Vision model processing failed for {context.source_path.name}: {e}")
            return Failure(f"Vision model processing failed: {e}")
    else:
        prompt = f"""
        Analyze the following document text and provide the following information in a JSON object:
        1.  `issuer`: The name of the company or person that created the document.
        2.  `category`: Classify the document into one of the following categories: {context.categories}.
        3.  `date`: The date of the document in YYYY-MM-DD format.
        4.  `short_title`: A very short, descriptive title for the document.
        5.  `language`: The primary language of the document (e.g., 'en', 'fr', 'de', etc.). Use ISO 639-1 codes.

        Document Text:
        ---
        {context.content[:4000]}
        ---
        """
        try:
            logger.debug(f"Calling LLM API for {context.source_path.name}")
            api_response = get_completion(prompt)
            logger.debug(f"LLM API response: {api_response}")

            # Parse the JSON string from response['response']
            if "response" in api_response and isinstance(api_response["response"], str):
                try:
                    import json

                    response = json.loads(api_response["response"])
                    logger.debug(f"Parsed JSON from LLM API response: {response}")

                    # Traduire la catégorie en français si nécessaire
                    if "category" in response:
                        original_category = response["category"]
                        response["category"] = translate_category(original_category, context.content)
                        logger.debug(f"Translated category: {original_category} -> {response['category']}")
                except json.JSONDecodeError as e:
                    logger.error(f"Failed to parse JSON from LLM API response: {e}")
                    response = {}
            else:
                response = api_response
        except Exception as e:
            logger.error(f"LLM processing failed for {context.source_path.name}: {e}")
            return Failure(f"LLM processing failed: {e}")

    # Create a validated AIResponse object from the LLM response
    try:
        # Add language detection to prompt in future iterations
        response["language"] = response.get("language", "N/A")
        logger.debug(f"Creating AIResponse from: {response}")
        ai_response = AIResponse(**response)

        # Update context with validated AI results
        ai_results = ai_response.dict(exclude_none=True)

        # Transfer AI results to main FileContext fields
        logger.debug(f"Updating FileContext with AI results: {ai_results}")

        # Determine sector using issuer name and content
        sector = None
        if ai_response.issuer:
            logger.debug(f"Determining sector for issuer: {ai_response.issuer}")
            sector = get_sector_with_ai(ai_response.issuer, context.content)
            logger.debug(f"Determined sector: {sector}")

        updated_context = context.copy(
            update={
                "ai_results": ai_results,
                "issuer": ai_response.issuer,
                "language": ai_response.language,
                "category": ai_response.category,  # Ensure category is also transferred
                "sector": sector,  # Set the sector field
            }
        )
        logger.debug(
            f"Updated FileContext: issuer={updated_context.issuer}, language={updated_context.language}, category={updated_context.category}, sector={updated_context.sector}"
        )
    except Exception as e:
        logger.error(f"Failed to parse AI response: {e}")
        # Fallback to basic mapping if validation fails
        ai_results = {
            "issuer": response.get("issuer"),
            "category": response.get("category"),
            "date": response.get("date"),
            "short_title": response.get("short_title"),
        }
        logger.debug(f"Fallback mapping: {ai_results}")

        # Determine sector using issuer name and content
        sector = None
        issuer = response.get("issuer")
        if issuer:
            logger.debug(f"Determining sector for issuer: {issuer}")
            sector = get_sector_with_ai(issuer, context.content)
            logger.debug(f"Determined sector: {sector}")

        updated_context = context.copy(
            update={
                "ai_results": ai_results,
                "issuer": response.get("issuer"),
                "language": response.get("language", "N/A"),
                "category": response.get("category"),  # Ensure category is also transferred
                "sector": sector,  # Set the sector field
            }
        )
        logger.debug(
            f"Updated FileContext (fallback): issuer={updated_context.issuer}, language={updated_context.language}, category={updated_context.category}, sector={updated_context.sector}"
        )
    logger.debug(f"AI enrichment complete for {context.source_path.name}")
    return Success(updated_context)
