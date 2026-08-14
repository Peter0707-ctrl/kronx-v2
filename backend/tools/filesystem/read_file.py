import os
from typing import Dict, Any
from tools.path_verify import verify_safe_path
from tools.errors import SENSITIVE_FILE, PATH_OUTSIDE_WORKSPACE
from workspace.scanner import WorkspaceScanner

# Safety limits
MAX_READ_FILE_BYTES = 1 * 1024 * 1024  # 1MB

def read_file_handler(context: Any, arguments: Dict[str, Any]) -> Dict[str, Any]:
    """
    Safely read files inside workspace boundaries.
    Truncates content and filters binary/sensitive data.
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

    filename = os.path.basename(abs_path)
    
    # 1. Sensitive file check
    scanner = WorkspaceScanner()
    is_sens, reason = scanner.is_sensitive(filename)
    if is_sens:
        raise ValueError(SENSITIVE_FILE)

    # 2. Exists and is file check
    if not os.path.exists(abs_path) or not os.path.isfile(abs_path):
        raise ValueError("File does not exist or is not a file.")

    # 3. Size check and truncation
    file_size = os.path.getsize(abs_path)
    
    # 4. Binary check
    # Check binary extensions or check for null bytes in first 8KB
    _, ext = os.path.splitext(filename.lower())
    binary_exts = {".pyc", ".class", ".o", ".dll", ".so", ".exe", ".bin", ".zip", ".tar", ".gz"}
    is_binary = ext in binary_exts
    
    if not is_binary:
        try:
            with open(abs_path, "rb") as f:
                chunk = f.read(8000)
                if b"\0" in chunk:
                    is_binary = True
        except Exception:
            is_binary = True

    if is_binary:
        return {
            "path": os.path.relpath(abs_path, workspace_root).replace("\\", "/"),
            "content": "[Binary Content Blocked]",
            "size": file_size,
            "line_count": 0,
            "truncated": False,
            "binary": True
        }

    # 5. Read text file safely with truncation bounds
    try:
        with open(abs_path, "r", encoding="utf-8", errors="ignore") as f:
            # Bounded read to prevent memory exhaustion
            content = f.read(MAX_READ_FILE_BYTES)
            
        truncated = (file_size > MAX_READ_FILE_BYTES)
        line_count = content.count("\n") + 1
        
        return {
            "path": os.path.relpath(abs_path, workspace_root).replace("\\", "/"),
            "content": content,
            "size": file_size,
            "line_count": line_count,
            "truncated": truncated,
            "binary": False
        }
    except Exception as e:
        raise ValueError(f"Failed to read file: {str(e)}")
