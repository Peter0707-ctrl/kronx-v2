"""
Phase 2I.1 — Multimodal Resource Limits & Bounds
Guarantees memory containment and prevents resource exhaustion.
"""
import os
from typing import Optional
from multimodal.errors import (
    MultimodalError,
    FILE_TOO_LARGE,
    DOCUMENT_TOO_LARGE,
    IMAGE_TOO_LARGE,
    OCR_TOO_LARGE,
    TOO_MANY_FILES,
)

# Configurable byte and count limits
MAX_UPLOAD_BYTES: int             = int(os.getenv("KRONX_MAX_UPLOAD_BYTES", 10 * 1024 * 1024))          # 10 MB
MAX_DOCUMENT_TEXT_BYTES: int      = int(os.getenv("KRONX_MAX_DOCUMENT_TEXT_BYTES", 1 * 1024 * 1024))    # 1 MB
MAX_IMAGE_BYTES: int              = int(os.getenv("KRONX_MAX_IMAGE_BYTES", 10 * 1024 * 1024))          # 10 MB
MAX_IMAGE_DIMENSION: int          = int(os.getenv("KRONX_MAX_IMAGE_DIMENSION", 4096))                  # 4096px
MAX_OCR_TEXT_BYTES: int           = int(os.getenv("KRONX_MAX_OCR_TEXT_BYTES", 500 * 1024))            # 500 KB
MAX_FILES_PER_REQUEST: int        = int(os.getenv("KRONX_MAX_FILES_PER_REQUEST", 10))                  # 10 files
MAX_MULTIMODAL_CONTEXT_ITEMS: int = int(os.getenv("KRONX_MAX_MULTIMODAL_CONTEXT_ITEMS", 50))          # 50 facts/inferences
MAX_STORED_RECORDS_PER_TENANT: int = int(os.getenv("KRONX_MAX_STORED_MULTIMODAL_RECORDS", 500))      # 500 records


def check_file_size(size_bytes: int, max_allowed: Optional[int] = None, error_code: str = FILE_TOO_LARGE) -> None:
    """Enforce size bounds on raw file byte content."""
    limit = max_allowed or MAX_UPLOAD_BYTES
    if size_bytes > limit:
        raise MultimodalError(
            error_code,
            f"File size {size_bytes} bytes exceeds maximum permitted limit of {limit} bytes."
        )


def check_document_text_size(text_length_bytes: int) -> None:
    """Enforce bounds on extracted document text."""
    if text_length_bytes > MAX_DOCUMENT_TEXT_BYTES:
        raise MultimodalError(
            DOCUMENT_TOO_LARGE,
            f"Extracted document text size {text_length_bytes} bytes exceeds limit of {MAX_DOCUMENT_TEXT_BYTES} bytes."
        )


def check_image_size(size_bytes: int) -> None:
    """Enforce bounds on image uploads."""
    if size_bytes > MAX_IMAGE_BYTES:
        raise MultimodalError(
            IMAGE_TOO_LARGE,
            f"Image size {size_bytes} bytes exceeds maximum limit of {MAX_IMAGE_BYTES} bytes."
        )


def check_ocr_text_size(text_length_bytes: int) -> None:
    """Enforce bounds on OCR extracted text output."""
    if text_length_bytes > MAX_OCR_TEXT_BYTES:
        raise MultimodalError(
            OCR_TOO_LARGE,
            f"OCR extracted text size {text_length_bytes} bytes exceeds limit of {MAX_OCR_TEXT_BYTES} bytes."
        )


def check_file_count(count: int) -> None:
    """Enforce maximum files per batch request."""
    if count > MAX_FILES_PER_REQUEST:
        raise MultimodalError(
            TOO_MANY_FILES,
            f"File count {count} exceeds maximum allowed limit of {MAX_FILES_PER_REQUEST} files per request."
        )
