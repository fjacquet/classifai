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
    endpoint: str,
    payload: dict[str, Any],
    logger_instance: Any | None = logger,
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
                    f"Request to Ollama failed on attempt {attempt + 1}/{MAX_RETRIES}: {e}",
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


def _get_category_suggestion(
    content: str,
    categories: list[str],
    logger_instance: Any | None = logger,
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
    4. Return ONLY the category name, nothing else

    # DOCUMENT TO ANALYZE
    ---
    {content[:2000]}
    ---
    """

    try:
        api_response = get_completion(prompt, logger_instance=logger_instance)
        if "response" in api_response:
            suggestion = api_response["response"].strip()
            # Clean the suggestion to be filename-safe
            suggestion = "".join(c for c in suggestion if c.isalnum() or c in " -_").strip()
            suggestion = suggestion.replace(" ", "-")
            logger.debug(f"Category suggestion: {suggestion}")
            return suggestion
    except Exception as e:
        if logger_instance:
            logger_instance.error(f"Failed to get category suggestion: {e}")
    return None


def enrich_with_ai(context: FileContext) -> Result[FileContext, str]:
    """
    Enriches the file context with AI-powered classification.
    This is an impure function that makes a network call.
    Implements strict category enforcement with _UNKNOWN_ handling per functional specification.
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
        2.  `category`: Classify the image into ONE of the following categories EXACTLY as written
        - do not modify, translate or add typos: {context.categories}.
        - IMPORTANT: You must select a category from the list above EXACTLY as written.
         Do not modify the spelling or add any typos.
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
        # prompt = f"""
        # Analyze the following document text and provide the following information in a JSON object:
        # 1.  `issuer`: The name of the company or person that created the document.
        # 2.  `category`: Classify the document into ONE of the following categories EXACTLY as written
        #     - do not modify, translate or add typos: {context.categories}.
        #     - IMPORTANT: You must select a category from the list above EXACTLY as written.
        #       Do not modify the spelling or add any typos.
        # 3.  `date`: The date of the document in YYYY-MM-DD format.
        # 4.  `short_title`: A very short, descriptive title for the document.
        # 5.  `language`: The primary language of the document (e.g., 'en', 'fr', 'de', etc.). Use ISO 639-1 codes.

        # Document Text:
        prompt = f"""
        # ROLE
        You are a highly accurate data extraction service.

        # TASK
        Analyze the provided document text and return a single, well-formed JSON object containing the extracted information.
        Adhere strictly to the rules and formats defined below.

        # RULES
        1.  **Issuer Priority:** To determine the `issuer`, check in this order:
            1) The company on the letterhead.
            2) The signatory of the document.
            3) The main company the document is about.
        2.  **CRITICAL - Strict Categorization:** The `category` value MUST be an EXACT match to one of these options:
            {context.categories}
            - You MUST select from this list EXACTLY as written
            - Do NOT translate, modify, or add typos
            - Do NOT create new categories
            - If NONE of these categories fit the document, set category to `null`
        3.  **Date Logic:** Find the main document date. Convert it to `YYYY-MM-DD` format.
            If there are multiple dates, use the issue date.
        4.  **Title Conciseness:** The `short_title` should be a concise summary of 5-10 words.
        5.  **Language Code:** The `language` must be a valid ISO 639-1 code.
        6.  **Missing Data:** If any piece of information cannot be reliably determined from the text,
            its corresponding value in the JSON must be `null`. Do not omit the key.

        # JSON OUTPUT SPECIFICATION
        {{
            "issuer": "string or null",
            "category": "string or null",
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

                    # Strict category validation per functional specification
                    if "category" in response and response["category"]:
                        category = response["category"]
                        # Validate category is in the allowed list
                        if category not in context.categories:
                            logger.warning(
                                f"Invalid category '{category}' not in allowed list. Setting to null.",
                            )
                            response["category"] = None
                        else:
                            logger.debug(f"Valid category selected: {category}")

                    # Handle _UNKNOWN_ workflow if no valid category was assigned
                    if not response.get("category"):
                        logger.info(
                            f"No valid category found for {context.source_path.name}. Implementing _UNKNOWN_ workflow.",
                        )
                        response["category"] = "_UNKNOWN_"

                        # Get category suggestion for filename
                        suggestion = _get_category_suggestion(context.content, context.categories)
                        if suggestion:
                            response["category_suggestion"] = suggestion
                            logger.info(f"Category suggestion for _UNKNOWN_ document: {suggestion}")
                        else:
                            logger.warning("Failed to get category suggestion for _UNKNOWN_ document")
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

        # Determine sector using issuer name with knowledge base lookup first
        sector = None
        if ai_response.issuer:
            logger.debug(f"Determining sector for issuer: {ai_response.issuer}")

            # First try knowledge base lookup (step 1 of two-step process)
            from classifai.infrastructure.knowledge_base import get_sector_for_issuer

            sector_result = get_sector_for_issuer(ai_response.issuer)

            if isinstance(sector_result, Success):
                sector = sector_result.unwrap()
                logger.debug(f"Found sector in knowledge base: {sector}")
            else:
                # Fallback to AI classification (step 2 of two-step process)
                logger.debug("Sector not found in knowledge base, using AI fallback")
                sector = get_sector_with_ai(ai_response.issuer, context.content)
                logger.debug(f"AI determined sector: {sector}")

        updated_context = context.copy(
            update={
                "ai_results": ai_results,
                "issuer": ai_response.issuer,
                "language": ai_response.language,
                "category": ai_response.category,  # Ensure category is also transferred
                "sector": sector,  # Set the sector field
            },
        )
        logger.debug(
            f"Updated FileContext: issuer={updated_context.issuer}, language={updated_context.language}, category={updated_context.category}, sector={updated_context.sector}",
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

        # Determine sector using issuer name with knowledge base lookup first
        sector = None
        issuer = response.get("issuer")
        if issuer:
            logger.debug(f"Determining sector for issuer: {issuer}")

            # First try knowledge base lookup (step 1 of two-step process)
            from classifai.infrastructure.knowledge_base import get_sector_for_issuer

            sector_result = get_sector_for_issuer(issuer)

            if isinstance(sector_result, Success):
                sector = sector_result.unwrap()
                logger.debug(f"Found sector in knowledge base: {sector}")
            else:
                # Fallback to AI classification (step 2 of two-step process)
                logger.debug("Sector not found in knowledge base, using AI fallback")
                sector = get_sector_with_ai(issuer, context.content)
                logger.debug(f"AI determined sector: {sector}")

        updated_context = context.copy(
            update={
                "ai_results": ai_results,
                "issuer": response.get("issuer"),
                "language": response.get("language", "N/A"),
                "category": response.get("category"),  # Ensure category is also transferred
                "sector": sector,  # Set the sector field
            },
        )
        logger.debug(
            f"Updated FileContext (fallback): issuer={updated_context.issuer}, language={updated_context.language}, category={updated_context.category}, sector={updated_context.sector}",
        )
    logger.debug(f"AI enrichment complete for {context.source_path.name}")
    return Success(updated_context)
