"""
Main entry point for ClassifAI.

This module provides the main entry points for the different interfaces:
- CLI
- Web UI
- API

It serves as a thin layer connecting the interfaces with the core functionality.
"""

import sys

from loguru import logger

from classifai.app.api import start_api_server
from classifai.app.cli import app as cli_app
from classifai.app.web_ui import main as web_ui_main
from classifai.logging_module import setup_logging


def run_cli():
    """Run the CLI interface."""
    setup_logging()
    logger.info("Starting ClassifAI CLI")
    cli_app()


def run_web_ui():
    """Run the Web UI interface."""
    setup_logging()
    logger.info("Starting ClassifAI Web UI")
    web_ui_main()


def run_api(host="0.0.0.0", port=8000):
    """Run the API interface."""
    setup_logging()
    logger.info(f"Starting ClassifAI API on {host}:{port}")
    start_api_server(host, port)


if __name__ == "__main__":
    # Default to CLI if no arguments are provided
    if len(sys.argv) < 2:
        run_cli()
    else:
        # Check which interface to run
        interface = sys.argv[1].lower()

        if interface == "cli":
            # Remove the interface argument to pass the rest to the CLI
            sys.argv.pop(1)
            run_cli()
        elif interface == "web":
            run_web_ui()
        elif interface == "api":
            # Check for host and port arguments
            host = "0.0.0.0"
            port = 8000

            if len(sys.argv) > 2:
                host = sys.argv[2]
            if len(sys.argv) > 3:
                try:
                    port = int(sys.argv[3])
                except ValueError:
                    logger.error(f"Invalid port: {sys.argv[3]}")
                    sys.exit(1)

            run_api(host, port)
        else:
            logger.error(f"Unknown interface: {interface}")
            logger.error("Usage: python -m classifai [cli|web|api] [host] [port]")
            sys.exit(1)
