import os
import re
import threading
from datetime import datetime
from typing import List, Dict, Any, Tuple, Set
from utils.logger import logger
from workspace.schema import FileItem, SensitiveFileInfo

# Configurable Safety Limits
DEFAULT_IGNORED_DIRS = {
    ".git", "node_modules", "vendor", "__pycache__", "dist", "build", 
    "coverage", ".next", "target", "venv", ".venv", "env", "bin", "obj"
}
MAX_FILE_SIZE_BYTES = 5 * 1024 * 1024  # 5MB
MAX_TOTAL_FILES = 5000
MAX_TOTAL_SCAN_SIZE_BYTES = 100 * 1024 * 1024  # 100MB
MAX_DOCUMENT_SIZE_BYTES = 1 * 1024 * 1024  # 1MB

# Sensitive files patterns
SENSITIVE_PATTERNS = [
    re.compile(r'^\.env(?:\..*)?$'),
    re.compile(r'^credentials(?:\..*)?$'),
    re.compile(r'^secrets(?:\..*)?$'),
    re.compile(r'^id_(?:rsa|dsa|ecdsa|ed25519)$'),
    re.compile(r'^.*\.pem$'),
    re.compile(r'^.*\.key$'),
    re.compile(r'^.*token.*$'),
    re.compile(r'^db_password$'),
]

class WorkspaceScanner:
    def __init__(
        self,
        ignored_dirs: Set[str] = None,
        max_file_size: int = MAX_FILE_SIZE_BYTES,
        max_total_files: int = MAX_TOTAL_FILES,
        max_total_scan_size: int = MAX_TOTAL_SCAN_SIZE_BYTES
    ):
        self.ignored_dirs = ignored_dirs if ignored_dirs is not None else DEFAULT_IGNORED_DIRS
        self.max_file_size = max_file_size
        self.max_total_files = max_total_files
        self.max_total_scan_size = max_total_scan_size

    def verify_safe_path(self, workspace_root: str, target_path: str) -> str:
        """
        Verify that target_path is within workspace_root.
        Resolves symbolic links and raises ValueError("PATH_OUTSIDE_WORKSPACE") if outside.
        """
        real_root = os.path.realpath(workspace_root)
        
        # Build absolute path to ensure we resolve relative references before realpath
        joined_path = os.path.abspath(os.path.join(real_root, target_path))
        real_target = os.path.realpath(joined_path)

        # On Windows, drive letters must match and casing is normalized.
        # Check containment using os.path.commonpath
        try:
            common = os.path.commonpath([real_root, real_target])
            if common != real_root:
                raise ValueError("PATH_OUTSIDE_WORKSPACE")
        except Exception:
            raise ValueError("PATH_OUTSIDE_WORKSPACE")

        return real_target

    def is_sensitive(self, filename: str) -> Tuple[bool, str]:
        """Check if file matches sensitive pattern and return (is_sensitive, reason)."""
        filename_lower = filename.lower()
        for pattern in SENSITIVE_PATTERNS:
            if pattern.match(filename_lower):
                return True, f"Matches sensitive pattern: {pattern.pattern}"
        return False, ""

    def classify_file(self, rel_path: str, filename: str, size: int) -> str:
        """Classify files into deterministic categories."""
        filename_lower = filename.lower()
        rel_path_lower = rel_path.replace("\\", "/").lower()

        # 1. Sensitive (precedes all else)
        is_sens, _ = self.is_sensitive(filename)
        if is_sens:
            return "sensitive"

        # 2. Dependency Manifests
        dependency_names = [
            "requirements.txt", "package.json", "composer.json", 
            "pom.xml", "build.gradle", "pyproject.toml", "cargo.toml"
        ]
        if filename_lower in dependency_names:
            return "dependency"

        # 3. Documentation
        if filename_lower == "readme.md" or filename_lower.startswith("readme") or "docs/" in rel_path_lower or "documentation/" in rel_path_lower:
            return "documentation"

        # 4. Tests
        if "test/" in rel_path_lower or "tests/" in rel_path_lower or filename_lower.startswith("test_") or filename_lower.endswith("_test.py") or filename_lower.endswith("test.js") or filename_lower.endswith("spec.js") or filename_lower.endswith("test.ts") or filename_lower.endswith("spec.ts") or filename_lower.endswith("test.java"):
            return "test"

        # 5. Configuration Files
        config_exts = {".json", ".yaml", ".yml", ".xml", ".ini", ".toml", ".conf", ".cfg"}
        _, ext = os.path.splitext(filename_lower)
        if ext in config_exts:
            return "configuration"

        # 6. Source Files
        source_exts = {
            ".py", ".js", ".ts", ".tsx", ".jsx", ".java", ".php", 
            ".c", ".cpp", ".h", ".cs", ".go", ".rs", ".rb", ".sh", ".swift", ".kt"
        }
        if ext in source_exts:
            return "source"

        # 7. Assets
        asset_exts = {".png", ".jpg", ".jpeg", ".gif", ".svg", ".ico", ".mp3", ".mp4", ".pdf", ".css", ".html"}
        if ext in asset_exts:
            return "asset"

        # 8. Binary Files
        binary_exts = {".pyc", ".class", ".o", ".dll", ".so", ".exe", ".bin", ".tar", ".gz", ".zip"}
        if ext in binary_exts:
            return "binary"

        return "unknown"

    def scan(self, workspace_root: str, cancellation_token: threading.Event = None) -> Tuple[List[FileItem], List[SensitiveFileInfo], Dict[str, Any]]:
        """
        Recursively scan the workspace root and return lists of files, sensitive files, and statistics.
        Does not read contents of files.
        """
        # Ensure workspace root is verified
        real_root = os.path.realpath(workspace_root)
        if not os.path.isdir(real_root):
            raise ValueError("INVALID_WORKSPACE")

        files_list = []
        sensitive_list = []
        stats = {
            "total_files": 0,
            "total_size_bytes": 0,
            "category_counts": {},
            "ignored_counts": 0
        }

        # Safe traversal using os.walk
        for root, dirs, files in os.walk(real_root, followlinks=False):
            if cancellation_token and cancellation_token.is_set():
                logger.info("Scan job cancelled cooperatively during directory traversal.")
                return [], [], {}

            # Prune ignored directories in place
            dirs[:] = [d for d in dirs if d not in self.ignored_dirs]

            for file in files:
                if cancellation_token and cancellation_token.is_set():
                    logger.info("Scan job cancelled cooperatively during file processing.")
                    return [], [], {}

                abs_filepath = os.path.join(root, file)
                rel_path = os.path.relpath(abs_filepath, real_root).replace("\\", "/")

                # Path containment check (verify symlinks or odd files did not escape)
                try:
                    self.verify_safe_path(real_root, rel_path)
                except ValueError:
                    stats["ignored_counts"] += 1
                    continue

                try:
                    file_size = os.path.getsize(abs_filepath)
                    mtime = os.path.getmtime(abs_filepath)
                    mtime_str = datetime.fromtimestamp(mtime).isoformat()
                except Exception:
                    # Skip files that cannot be queried
                    continue

                # Safety Limits checks
                if stats["total_files"] >= self.max_total_files:
                    logger.warning(f"Scan limit reached: MAX_TOTAL_FILES={self.max_total_files}")
                    break
                if stats["total_size_bytes"] + file_size > self.max_total_scan_size:
                    logger.warning(f"Scan limit reached: MAX_TOTAL_SCAN_SIZE={self.max_total_scan_size}")
                    break

                category = self.classify_file(rel_path, file, file_size)

                # Check sensitive files
                is_sens, reason = self.is_sensitive(file)
                if is_sens:
                    sensitive_list.append(SensitiveFileInfo(
                        path=rel_path,
                        category=category,
                        sensitive=True,
                        reason=reason
                    ))
                    # Do not add to normal files_list or count total size to ensure secret contents are protected
                    stats["category_counts"][category] = stats["category_counts"].get(category, 0) + 1
                    continue

                # Exclude huge files
                if file_size > self.max_file_size:
                    stats["ignored_counts"] += 1
                    continue

                item = FileItem(
                    path=rel_path,
                    category=category,
                    size_bytes=file_size,
                    modified_at=mtime_str
                )
                files_list.append(item)

                # Update stats
                stats["total_files"] += 1
                stats["total_size_bytes"] += file_size
                stats["category_counts"][category] = stats["category_counts"].get(category, 0) + 1

        return files_list, sensitive_list, stats
