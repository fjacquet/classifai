"""
RESTful API interface for ClassifAI.

This module provides a RESTful API for ClassifAI using FastAPI.
It allows programmatic access to ClassifAI's classification functionality.
"""

import tempfile
from pathlib import Path

from fastapi import FastAPI, File, Form, UploadFile
from loguru import logger
from pydantic import BaseModel
from returns.result import Success

from classifai.config import app_config
from classifai.core.workflow import process_single_file
from classifai.logging_module import setup_logging

# Create FastAPI app
app = FastAPI(
    title="ClassifAI API",
    description="API for document classification using ClassifAI",
    version="0.2.0",
)


class ClassificationOptions(BaseModel):
    """Options for classification."""

    rename_files: bool = False
    use_vision: bool = False
    language_subfolders: bool = True
    dest_dir: str = str(Path.home() / "ClassifAI_Output")


class ClassificationResponse(BaseModel):
    """Response model for classification results."""

    success: bool
    message: str
    category: str | None = None
    issuer: str | None = None
    sector: str | None = None
    language: str | None = None
    final_path: str | None = None
    ai_results: dict | None = None


@app.post("/classify", response_model=ClassificationResponse)
async def classify_file(
    file: UploadFile = File(...),  # noqa: B008 - FastAPI dependency injection pattern
    options: ClassificationOptions = Form(...),  # noqa: B008 - FastAPI dependency injection pattern
):
    """
    Classify a file according to its content.

    - **file**: The file to classify
    - **options**: Classification options
    """
    setup_logging()
    logger.info(f"API: Classifying file {file.filename}")

    # Create a temporary directory to safely store the uploaded file
    # The directory auto-cleans on exit, avoiding manual unlink on potentially influenced paths
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_dir_path = Path(tmp_dir)
        safe_suffix = Path(file.filename).suffix  # only use suffix, not the full (potentially unsafe) name
        tmp_path = tmp_dir_path / f"upload{safe_suffix}"
        content = await file.read()
        tmp_path.write_bytes(content)

        try:
            # Process the file
            result = process_single_file(
                file_path=tmp_path,
                dest_dir=Path(options.dest_dir),
                rename_files=options.rename_files,
                use_vision=options.use_vision,
                language_subfolders=options.language_subfolders,
            )

            # Return appropriate response
            if isinstance(result, Success):
                context = result.unwrap()
                return ClassificationResponse(
                    success=True,
                    message="File classified successfully",
                    category=context.category,
                    issuer=context.issuer,
                    sector=context.sector,
                    language=context.language,
                    final_path=str(context.final_destination_path)
                    if context.final_destination_path
                    else None,
                    ai_results=context.ai_results,
                )
            error = result.failure()
            return ClassificationResponse(
                success=False,
                message=f"Classification failed: {error}",
            )
        except Exception as e:
            logger.error(f"API error: {e}")
            return ClassificationResponse(
                success=False,
                message=f"An error occurred: {str(e)}",
            )


@app.get("/health")
async def health_check():
    """
    Health check endpoint.
    """
    return {"status": "ok"}


@app.get("/supported-extensions")
async def get_supported_extensions():
    """
    Get list of supported file extensions.
    """
    return {"extensions": app_config.supported_extensions}


def start_api_server(host="0.0.0.0", port=8000):
    """
    Start the API server.
    """
    import uvicorn

    setup_logging()
    logger.info(f"Starting ClassifAI API server on {host}:{port}")
    uvicorn.run(app, host=host, port=port)


if __name__ == "__main__":
    start_api_server()
