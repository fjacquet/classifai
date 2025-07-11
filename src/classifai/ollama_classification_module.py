"""
Ollama classification module for ClassifAI.

This module handles the interaction with the Ollama API via litellm
to classify the content of documents.
"""

import base64
import json
import mimetypes

from litellm import completion

from classifai.config import OLLAMA_API_URL, OLLAMA_MODEL_NAME, OLLAMA_VISION_MODEL_NAME
from classifai.knowledge_base_module import KnowledgeBase
from classifai.rules_engine_module import RulesEngine

# Initialize the engines
rules_engine = RulesEngine()
knowledge_base = KnowledgeBase()


def classify_content(content: str, categories: list[str], file_path: str, logger) -> dict:
    """
    Classifies the given content and suggests a new filename using a hybrid
    approach (rules -> knowledge base -> AI).

    Args:
        content (str): The content to classify.
        categories (list[str]): A list of possible categories.
        file_path (str): The path to the file being classified.
        logger: The logger instance.

    Returns:
        dict: A dictionary containing the category and a suggested new filename.
              Example: {"category": "Invoices", "new_filename": "2025-07-11-invoice-acme.pdf"}
    """
    # 1. Attempt pre-classification with the rules engine
    rule_category = rules_engine.match_category(file_path)
    if rule_category:
        return {"category": rule_category, "new_filename": None}

    # 2. Attempt pre-classification with the knowledge base
    kb_category = knowledge_base.match_category(content)
    if kb_category:
        return {"category": kb_category, "new_filename": None}

    # 3. Fallback to AI classification
    prompt = """
    Analyze the following document content and return a JSON object with three keys:
    1. "category": Classify the document into one of the following categories: {", ".join(categories)}.
    2. "new_filename": Suggest a new filename in the format YYYY-MM-DD-issuer-short_description.ext.
       - The date should be the most relevant date from the document.
       - The issuer should be the name of the company or person who created the document.
       - The description should be a 1-3 word summary.
       - Use the original file extension.
    3. "issuer": The name of the company or person who created the document.

    Content:
    ---
    {content[:4000]}
    ---

    Return only the JSON object, with no other text or explanations.
    """

    try:
        model_prefix = "ollama_chat/" if "chat" in OLLAMA_MODEL_NAME.lower() else "ollama/"
        model_to_use = f"{model_prefix}{OLLAMA_MODEL_NAME}"

        response = completion(
            model=model_to_use,
            messages=[{"content": prompt, "role": "user"}],
            api_base=OLLAMA_API_URL,
            response_format={"type": "json_object"},
        )

        response_text = response.choices[0].message.content.strip()
        response_data = json.loads(response_text)

        category = response_data.get("category")
        new_filename = response_data.get("new_filename")
        issuer = response_data.get("issuer")

        if category not in categories:
            logger.warning(f"Model returned an unexpected category: {category}")
            category = "Unknown"

        return {"category": category, "new_filename": new_filename, "issuer": issuer}

    except (json.JSONDecodeError, KeyError) as e:
        logger.error(f"Error parsing JSON response from Ollama: {e}")
        return {"category": "Unknown", "new_filename": None, "issuer": None}
    except Exception as e:
        logger.error(f"Error classifying content with Ollama: {e}")
        return {"category": "Unknown", "new_filename": None, "issuer": None}


def extract_issuer(content: str, logger) -> str | None:
    """
    Extracts the issuer from the given document content using an AI model.

    Args:
        content (str): The content to extract the issuer from.
        logger: The logger instance.

    Returns:
        The name of the issuer, or None if it cannot be determined.
    """
    prompt = f"""
    Analyze the following document content and identify the issuer
    (the company or person who created it).
    Return a JSON object with a single key: "issuer".

    Content:
    ---
    {content[:4000]}
    ---

    Return only the JSON object.
    """
    try:
        model_prefix = "ollama_chat/" if "chat" in OLLAMA_MODEL_NAME.lower() else "ollama/"
        model_to_use = f"{model_prefix}{OLLAMA_MODEL_NAME}"

        response = completion(
            model=model_to_use,
            messages=[{"content": prompt, "role": "user"}],
            api_base=OLLAMA_API_URL,
            response_format={"type": "json_object"},
        )

        response_text = response.choices[0].message.content.strip()
        response_data = json.loads(response_text)
        issuer = response_data.get("issuer")
        return issuer

    except (json.JSONDecodeError, KeyError) as e:
        logger.error(f"Error parsing JSON response from Ollama for issuer: {e}")
        return None
    except Exception as e:
        logger.error(f"Error extracting issuer with Ollama: {e}")
        return None


def classify_image_with_vision(file_path: str, logger) -> str | None:
    """
    Generates a description of an image using a vision model.

    Args:
        file_path (str): The path to the image file.
        logger: The logger instance.

    Returns:
        A string description of the image, or None if an error occurs.
    """
    try:
        with open(file_path, "rb") as image_file:
            base64_image = base64.b64encode(image_file.read()).decode("utf-8")

        mime_type, _ = mimetypes.guess_type(file_path)
        if not mime_type or not mime_type.startswith("image"):
            logger.warning(f"Cannot determine mime type for image: {file_path}")
            return None

        model_to_use = f"ollama/{OLLAMA_VISION_MODEL_NAME}"

        response = completion(
            model=model_to_use,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": "Describe this image in detail. What is the subject? What is happening?",
                        },
                        {
                            "type": "image_url",
                            "image_url": {"url": f"data:{mime_type};base64,{base64_image}"},
                        },
                    ],
                }
            ],
            api_base=OLLAMA_API_URL,
        )

        description = response.choices[0].message.content.strip()
        return description

    except Exception as e:
        logger.error(f"Error classifying image with vision model: {e}")
        return None
