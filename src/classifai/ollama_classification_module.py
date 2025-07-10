"""
Ollama classification module for ClassifAI.

This module handles the interaction with the Ollama API via litellm
to classify the content of documents.
"""

from litellm import completion
from loguru import logger

from classifai.config import OLLAMA_API_URL, OLLAMA_MODEL_NAME


def classify_content(content: str, categories: list[str], logger) -> str:
    """
    Classifies the given content into one of the provided categories using Ollama.

    Args:
        content (str): The content to classify.
        categories (list[str]): A list of possible categories.

    Returns:
        str: The most appropriate category, or "Unknown" if classification fails.
    """
    prompt = f"""
    Given the following document content, please classify it into one of the
    following categories: {", ".join(categories)}.

    Content:
    ---
    {content[:4000]}
    ---

    Please return only the name of the category.
    """

    try:
        model_prefix = (
            "ollama_chat/" if "chat" in OLLAMA_MODEL_NAME.lower() else "ollama/"
        )
        model_to_use = f"{model_prefix}{OLLAMA_MODEL_NAME}"

        response = completion(
            model=model_to_use,
            messages=[{"content": prompt, "role": "user"}],
            api_base=OLLAMA_API_URL,
        )

        category = response.choices[0].message.content.strip()

        if category in categories:
            return category
        else:
            logger.warning(f"Model returned an unexpected category: {category}")
            return "Unknown"

    except Exception as e:
        logger.error(f"Error classifying content with Ollama: {e}")
        return "Unknown"
