"""
Phase 2I.1 — Multimodal File Type Classifier & Safety Filter
Validates file extensions, MIME types, and blocks unsafe binaries & sensitive paths.
"""
import os
import re
from enum import Enum
from typing import Tuple, Optional
from multimodal.errors import MultimodalError, UNSUPPORTED_FILE_TYPE, SENSITIVE_FILE_BLOCKED

class FileCategory(str, Enum):
    SOURCE_CODE       = "SOURCE_CODE"
    MARKDOWN          = "MARKDOWN"
    TEXT              = "TEXT"
    STRUCTURED_DATA   = "STRUCTURED_DATA"
    DOCUMENT          = "DOCUMENT"
    IMAGE             = "IMAGE"
    UNSUPPORTED_BINARY = "UNSUPPORTED_BINARY"
    BLOCKED_SENSITIVE = "BLOCKED_SENSITIVE"


# Extensions mapping
EXT_CATEGORY_MAP = {
    # Source Code
    ".py": FileCategory.SOURCE_CODE,
    ".js": FileCategory.SOURCE_CODE,
    ".ts": FileCategory.SOURCE_CODE,
    ".jsx": FileCategory.SOURCE_CODE,
    ".tsx": FileCategory.SOURCE_CODE,
    ".html": FileCategory.SOURCE_CODE,
    ".htm": FileCategory.SOURCE_CODE,
    ".css": FileCategory.SOURCE_CODE,
    ".scss": FileCategory.SOURCE_CODE,
    ".c": FileCategory.SOURCE_CODE,
    ".cpp": FileCategory.SOURCE_CODE,
    ".h": FileCategory.SOURCE_CODE,
    ".java": FileCategory.SOURCE_CODE,
    ".go": FileCategory.SOURCE_CODE,
    ".rs": FileCategory.SOURCE_CODE,
    ".rb": FileCategory.SOURCE_CODE,
    ".php": FileCategory.SOURCE_CODE,
    ".sh": FileCategory.SOURCE_CODE,
    ".bash": FileCategory.SOURCE_CODE,
    ".sql": FileCategory.SOURCE_CODE,
    ".vue": FileCategory.SOURCE_CODE,
    ".svelte": FileCategory.SOURCE_CODE,
    # Markdown
    ".md": FileCategory.MARKDOWN,
    ".markdown": FileCategory.MARKDOWN,
    ".rst": FileCategory.MARKDOWN,
    # Text
    ".txt": FileCategory.TEXT,
    ".log": FileCategory.TEXT,
    ".cfg": FileCategory.TEXT,
    ".ini": FileCategory.TEXT,
    ".conf": FileCategory.TEXT,
    # Structured Data
    ".json": FileCategory.STRUCTURED_DATA,
    ".yaml": FileCategory.STRUCTURED_DATA,
    ".yml": FileCategory.STRUCTURED_DATA,
    ".csv": FileCategory.STRUCTURED_DATA,
    ".tsv": FileCategory.STRUCTURED_DATA,
    ".xml": FileCategory.STRUCTURED_DATA,
    ".toml": FileCategory.STRUCTURED_DATA,
    # Document
    ".pdf": FileCategory.DOCUMENT,
    ".docx": FileCategory.DOCUMENT,
    ".doc": FileCategory.DOCUMENT,
    ".rtf": FileCategory.DOCUMENT,
    # Image
    ".png": FileCategory.IMAGE,
    ".jpg": FileCategory.IMAGE,
    ".jpeg": FileCategory.IMAGE,
    ".webp": FileCategory.IMAGE,
    ".svg": FileCategory.IMAGE,
    ".gif": FileCategory.IMAGE,
    ".bmp": FileCategory.IMAGE,
    ".tiff": FileCategory.IMAGE,
}

# Unsafe executables and binaries explicitly blocked from processing
BLOCKED_BINARY_EXTENSIONS = {
    ".exe", ".dll", ".so", ".dylib", ".bin", ".pyc", ".pyd", ".o", ".a",
    ".class", ".jar", ".war", ".zip", ".tar", ".gz", ".7z", ".iso", ".img",
    ".dmg", ".msi", ".pkg", ".app", ".bat", ".cmd", ".vbs", ".ps1"
}

# Sensitive filename patterns that must NEVER be analyzed or read into multimodal context
SENSITIVE_FILENAME_PATTERNS = [
    re.compile(r"^\.env(\..+)?$", re.IGNORECASE),
    re.compile(r"^credentials(\..+)?$", re.IGNORECASE),
    re.compile(r"^secrets?(\..+)?$", re.IGNORECASE),
    re.compile(r".*\.pem$", re.IGNORECASE),
    re.compile(r".*\.key$", re.IGNORECASE),
    re.compile(r"^id_rsa(\.pub)?$", re.IGNORECASE),
    re.compile(r"^id_ed25519(\.pub)?$", re.IGNORECASE),
    re.compile(r"^private_key(\..+)?$", re.IGNORECASE),
]

# Safe MIME types
MIME_CATEGORY_MAP = {
    "text/plain": FileCategory.TEXT,
    "text/markdown": FileCategory.MARKDOWN,
    "text/x-python": FileCategory.SOURCE_CODE,
    "text/javascript": FileCategory.SOURCE_CODE,
    "text/typescript": FileCategory.SOURCE_CODE,
    "text/html": FileCategory.SOURCE_CODE,
    "text/css": FileCategory.SOURCE_CODE,
    "text/csv": FileCategory.STRUCTURED_DATA,
    "application/json": FileCategory.STRUCTURED_DATA,
    "application/xml": FileCategory.STRUCTURED_DATA,
    "text/xml": FileCategory.STRUCTURED_DATA,
    "application/x-yaml": FileCategory.STRUCTURED_DATA,
    "text/yaml": FileCategory.STRUCTURED_DATA,
    "application/pdf": FileCategory.DOCUMENT,
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": FileCategory.DOCUMENT,
    "application/msword": FileCategory.DOCUMENT,
    "image/png": FileCategory.IMAGE,
    "image/jpeg": FileCategory.IMAGE,
    "image/webp": FileCategory.IMAGE,
    "image/svg+xml": FileCategory.IMAGE,
    "image/gif": FileCategory.IMAGE,
    "image/bmp": FileCategory.IMAGE,
}


def is_sensitive_filename(filename: str) -> bool:
    """Check if the filename matches sensitive file blacklist."""
    base = os.path.basename(filename.strip().replace("\\", "/"))
    for pattern in SENSITIVE_FILENAME_PATTERNS:
        if pattern.match(base):
            return True
    return False


def is_blocked_binary(filename: str) -> bool:
    """Check if the file is an unsupported/executable binary."""
    ext = os.path.splitext(filename.lower())[1]
    return ext in BLOCKED_BINARY_EXTENSIONS


def classify_file_type(filename: str, mime_type: Optional[str] = None) -> Tuple[FileCategory, str]:
    """
    Deterministically classify file category and normalized mime type.
    Enforces security rejection of sensitive files and executables.
    """
    if is_sensitive_filename(filename):
        raise MultimodalError(
            SENSITIVE_FILE_BLOCKED,
            f"Access to sensitive file '{os.path.basename(filename)}' is blocked by security policy."
        )

    if is_blocked_binary(filename):
        raise MultimodalError(
            UNSUPPORTED_FILE_TYPE,
            f"Execution or analysis of binary/executable file '{os.path.basename(filename)}' is prohibited."
        )

    ext = os.path.splitext(filename.lower())[1]
    if ext in EXT_CATEGORY_MAP:
        category = EXT_CATEGORY_MAP[ext]
        norm_mime = mime_type or (
            "application/pdf" if category == FileCategory.DOCUMENT and ext == ".pdf"
            else f"image/{ext.lstrip('.')}" if category == FileCategory.IMAGE
            else "text/plain"
        )
        return category, norm_mime

    if mime_type and mime_type.lower() in MIME_CATEGORY_MAP:
        return MIME_CATEGORY_MAP[mime_type.lower()], mime_type.lower()

    raise MultimodalError(
        UNSUPPORTED_FILE_TYPE,
        f"Unsupported file type for file '{os.path.basename(filename)}' (extension: '{ext}')."
    )
