import os
from typing import Dict, Any
from tools.path_verify import verify_safe_path
from tools.errors import PATH_OUTSIDE_WORKSPACE
from workspace.scanner import WorkspaceScanner

def inspect_file_handler(context: Any, arguments: Dict[str, Any]) -> Dict[str, Any]:
    """
    Safely inspect a file's metadata stats within workspace root.
    Never exposes file contents.
    """
    workspace_root = context.canonical_workspace_root
    rel_path = arguments.get("path")

    if not rel_path:
        raise ValueError("Missing 'path' argument.")

    try:
        abs_path = verify_safe_path(workspace_root, rel_path)
    except ValueError as ve:
        if str(ve) == "PATH_OUTSIDE_WORKSPACE":
            raise ValueError(PATH_OUTSIDE_WORKSPACE)
        raise ve

    if not os.path.exists(abs_path) or not os.path.isfile(abs_path):
        raise ValueError("File does not exist or is not a file.")

    filename = os.path.basename(abs_path)
    file_size = os.path.getsize(abs_path)

    scanner = WorkspaceScanner()
    is_sens, reason = scanner.is_sensitive(filename)
    category = scanner.classify_file(rel_path, filename, file_size)

    # Resolve language type
    _, ext = os.path.splitext(filename.lower())
    lang_mappings = {
        ".py": "Python", ".js": "JavaScript", ".ts": "TypeScript", 
        ".tsx": "TypeScript", ".jsx": "JavaScript", ".java": "Java", 
        ".php": "PHP", ".c": "C", ".cpp": "C++", ".go": "Go", 
        ".rs": "Rust", ".rb": "Ruby", ".html": "HTML", ".css": "CSS",
        ".sh": "Shell", ".md": "Markdown", ".json": "JSON", ".toml": "TOML"
    }
    language = lang_mappings.get(ext, "Unknown")

    # Binary check
    binary_exts = {".pyc", ".class", ".o", ".dll", ".so", ".exe", ".bin", ".zip", ".tar", ".gz"}
    is_binary = ext in binary_exts

    # Line count (safe calculation)
    line_count = 0
    if not is_binary and not is_sens and file_size <= 2 * 1024 * 1024:
        try:
            with open(abs_path, "r", encoding="utf-8", errors="ignore") as f:
                # Count newlines in chunks to keep memory usage low
                for chunk in iter(lambda: f.read(65536), ""):
                    line_count += chunk.count("\n")
                line_count += 1
        except Exception:
            pass

    return {
        "path": os.path.relpath(abs_path, workspace_root).replace("\\", "/"),
        "size_bytes": file_size,
        "category": category,
        "language": language,
        "binary": is_binary,
        "sensitive": is_sens,
        "line_count": line_count
    }
