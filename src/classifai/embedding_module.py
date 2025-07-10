"""
Embedding module for ClassifAI.

This module handles the generation of text embeddings using Ollama.
"""

from litellm import embedding
from loguru import logger
from numpy import dot
from numpy.linalg import norm

from classifai.config import OLLAMA_API_URL, OLLAMA_EMBEDDING_MODEL_NAME


def get_embedding(text: str, model: str = None) -> list[float]:
    """
    Generates an embedding for the given text.

    Args:
        text (str): The text to embed.
        model (str, optional): The name of the embedding model to use. 
                               Defaults to the one in the config.

    Returns:
        list[float]: The embedding vector, or an empty list if generation fails.
    """
    if model is None:
        model = OLLAMA_EMBEDDING_MODEL_NAME

    try:
        response = embedding(
            model=f"ollama/{model}",
            input=[text],
            api_base=OLLAMA_API_URL,
        )
        return response.data[0]["embedding"]
    except Exception as e:
        logger.error(f"Error generating embedding: {e}")
        return []


def cosine_similarity(vec1: list[float], vec2: list[float]) -> float:
    """
    Calculates the cosine similarity between two vectors.

    Args:
        vec1 (list[float]): The first vector.
        vec2 (list[float]): The second vector.

    Returns:
        float: The cosine similarity, or 0.0 if calculation fails.
    """
    try:
        return dot(vec1, vec2) / (norm(vec1) * norm(vec2))
    except Exception as e:
        logger.error(f"Error calculating cosine similarity: {e}")
        return 0.0
