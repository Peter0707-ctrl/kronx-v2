import os
from typing import Dict, Any
from tools.path_verify import verify_safe_path
from tools.errors import PATH_OUTSIDE_WORKSPACE
from workspace.scanner import WorkspaceScanner, DEFAULT_IGNORED_DIRS

MAX_DIRECTORY_ENTRIES = 500

def list_directory_handler(context: Any, arguments: Dict[str, Any]) -> Dict[str, Any]:
    """
    Safely list directories within workspace root.
    Filters ignored directories and limits response size.
    """
    workspace_root = context.canonical_workspace_root
    rel_path = arguments.get("path") or ""

    try:
        abs_path = verify_safe_path(workspace_root, rel_path)
    except ValueError as ve:
        if str(ve) == "PATH_OUTSIDE_WORKSPACE":
            raise ValueError(PATH_OUTSIDE_WORKSPACE)
        raise ve

    if not os.path.exists(abs_path) or not os.path.isdir(abs_path):
        raise ValueError("Directory does not exist or is not a directory.")

    entries = []
    dirs_count = 0
    files_count = 0
    truncated = False

    scanner = WorkspaceScanner()

    try:
        raw_entries = sorted(os.listdir(abs_path))
    except Exception as e:
        raise ValueError(f"Failed to list directory: {str(e)}")

    for name in raw_entries:
        # 1. Skip ignored directories
        if name in DEFAULT_IGNORED_DIRS:
            continue

        if len(entries) >= MAX_DIRECTORY_ENTRIES:
            truncated = True
            break

        item_abs_path = os.path.join(abs_path, name)
        item_rel_path = os.path.relpath(item_abs_path, workspace_root).replace("\\", "/")

        # Containment check for safety
        try:
            verify_safe_path(workspace_root, item_rel_path)
        except ValueError:
            continue

        is_dir = os.path.isdir(item_abs_path)
        is_sens, _ = scanner.is_sensitive(name)

        if is_dir:
            dirs_count += 1
            entries.append({
                "name": name,
                "path": item_rel_path,
                "type": "directory",
                "size": 0
            })
        else:
            files_count += 1
            # Hide actual secret value indicators by flagging
            entries.append({
                "name": name,
                "path": item_rel_path,
                "type": "file",
                "size": os.path.getsize(item_abs_path) if not is_sens else 0,
                "sensitive": is_sens
            })

    return {
        "directory": os.path.relpath(abs_path, workspace_root).replace("\\", "/"),
        "entries": entries,
        "dirs_count": dirs_count,
        "files_count": files_count,
        "truncated": truncated
    }
