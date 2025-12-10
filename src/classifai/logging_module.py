"""
Logging module for ClassifAI.

This module provides a centralized logging setup for the application using Loguru.
"""

import sys

from loguru import logger


def setup_logger(log_level="INFO", log_file=None, quiet_modules=None):
    """
    Set up the logger for the application.

    Args:
        log_level (str): The logging level (e.g., "INFO", "DEBUG").
        log_file (str, optional): Path to a file to save logs. Defaults to None.
        quiet_modules (list, optional): List of module names to suppress DEBUG logs from.
            These modules will only show INFO and above.
    """
    quiet_modules = quiet_modules or []

    def module_filter(record):
        """Filter to suppress DEBUG logs from specified modules."""
        if record["level"].name == "DEBUG":
            for module in quiet_modules:
                if module in record["name"]:
                    return False
        return True

    logger.remove()  # Remove default handler

    # Console handler
    logger.add(
        sys.stdout,
        level=log_level.upper(),
        format=(
            "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
            "<level>{level: <8}</level> | "
            "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - "
            "<level>{message}</level>"
        ),
        colorize=True,
        filter=module_filter,
    )

    # File handler
    if log_file:
        logger.add(
            log_file,
            level=log_level.upper(),
            format=("{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}"),
            rotation="10 MB",  # Rotates the file when it reaches 10 MB
            retention="7 days",  # Keeps logs for 7 days
            enqueue=True,  # Makes logging thread-safe
            backtrace=True,  # Shows full stack trace on exceptions
            diagnose=True,  # Adds exception variable values
            filter=module_filter,
        )
    return logger


# Alias for setup_logger to maintain backward compatibility
setup_logging = setup_logger
