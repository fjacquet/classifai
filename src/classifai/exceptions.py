"""Custom exceptions for ClassifAI.

This module provides a hierarchy of custom exceptions for error handling
throughout the application. Using custom exceptions instead of the returns
library provides clearer error handling with native Python patterns.
"""


class ClassifAIError(Exception):
    """Base exception for all ClassifAI errors.

    All custom exceptions in the application inherit from this class,
    allowing for easy catching of any ClassifAI-specific error.
    """

    pass


class ParsingError(ClassifAIError):
    """Error during file parsing.

    Raised when a file cannot be parsed or its content cannot be extracted.
    This includes PDF parsing failures, OCR errors, and unsupported formats.
    """

    pass


class ClassificationError(ClassifAIError):
    """Error during document classification.

    Raised when the classification process fails, including rule matching
    failures and AI classification errors.
    """

    pass


class FileOperationError(ClassifAIError):
    """Error during file operations.

    Raised when file system operations fail, such as move, copy, or delete
    operations. Includes permission errors and path resolution failures.
    """

    pass


class ConfigurationError(ClassifAIError):
    """Error in configuration.

    Raised when configuration is invalid, missing, or cannot be loaded.
    This includes YAML parsing errors and missing required settings.
    """

    pass


class LLMError(ClassifAIError):
    """Error communicating with LLM.

    Raised when communication with the Ollama API fails, including
    connection errors, timeout errors, and invalid responses.
    """

    pass


class KnowledgeBaseError(ClassifAIError):
    """Error accessing or querying the knowledge base.

    Raised when knowledge base operations fail, such as sector lookup
    failures or mapping file errors.
    """

    pass


class ValidationError(ClassifAIError):
    """Error validating data.

    Raised when input data fails validation, including invalid file paths,
    malformed responses, and schema validation failures.
    """

    pass


class MetadataExtractionError(ClassifAIError):
    """Error extracting file metadata.

    Raised when metadata extraction via ExifTool or MIME detection fails.
    This includes binary availability issues and file access errors.
    """

    pass
