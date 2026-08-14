import os
import re
from typing import Dict, Any, List
from tools.path_verify import verify_safe_path
from tools.errors import PATH_OUTSIDE_WORKSPACE, RESOURCE_LIMIT
from workspace.scanner import WorkspaceScanner, DEFAULT_IGNORED_DIRS

# Safety limits
MAX_QUERY_LENGTH = 120
MAX_SEARCH_RESULTS = 100
MAX_SEARCH_FILES = 1000
MAX_RESULT_BYTES = 500 * 1024  # 500KB

def search_code_handler(context: Any, arguments: Dict[str, Any]) -> Dict[str, Any]:
    """
    Safely search workspace source code files for a literal query query text.
    Regex search is disabled by default. Excludes sensitive/binary files and limits output size.
    """
    workspace_root = context.canonical_workspace_root
    query = arguments.get("query")
    sub_path = arguments.get("path") or ""
    extensions = arguments.get("file_extensions") # list of extension strings like [".py", ".ts"]

    if not query:
        raise ValueError("Missing 'query' argument.")

    if len(query) > MAX_QUERY_LENGTH:
        raise ValueError("Query string length exceeds limit of 120 characters.")

    # 1. Resolve safe target directory path
    try:
        search_root = verify_safe_path(workspace_root, sub_path)
    except ValueError as ve:
        if str(ve) == "PATH_OUTSIDE_WORKSPACE":
            raise ValueError(PATH_OUTSIDE_WORKSPACE)
        raise ve

    scanner = WorkspaceScanner()
    matches = []
    files_searched = 0
    total_result_bytes = 0
    results_count = 0
    truncated = False

    # 2. Convert extensions list to lowercase set
    ext_set = {ext.lower() for ext in extensions} if extensions else None

    # 3. Walk filesystem recursively to search content
    for root, dirs, files in os.walk(search_root, followlinks=False):
        if truncated:
            break

        # Prune ignored directories
        dirs[:] = [d for d in dirs if d not in DEFAULT_IGNORED_DIRS]

        for file in files:
            abs_filepath = os.path.join(root, file)
            rel_path = os.path.relpath(abs_filepath, workspace_root).replace("\\", "/")

            # Safe containment check
            try:
                verify_safe_path(workspace_root, rel_path)
            except ValueError:
                continue

            # 4. Skip sensitive file names
            is_sens, _ = scanner.is_sensitive(file)
            if is_sens:
                continue

            # 5. Skip based on extension filter if supplied
            _, ext = os.path.splitext(file.lower())
            if ext_set and ext not in ext_set:
                continue

            # 6. Skip binary extensions or file classifications
            binary_exts = {".pyc", ".class", ".o", ".dll", ".so", ".exe", ".bin", ".zip", ".tar", ".gz"}
            if ext in binary_exts:
                continue

            # Check max file scan limit
            files_searched += 1
            if files_searched > MAX_SEARCH_FILES:
                truncated = True
                break

            # 7. Safe read and search
            try:
                # Bounded read to avoid memory exhaustion
                file_size = os.path.getsize(abs_filepath)
                if file_size > 1 * 1024 * 1024:  # skip files > 1MB during search
                    continue

                with open(abs_filepath, "r", encoding="utf-8", errors="ignore") as f:
                    for line_idx, line in enumerate(f, 1):
                        if query.lower() in line.lower(): # Case-insensitive exact search
                            match_text = line.strip()
                            # Double check that we do not return sensitive values
                            if any(sec_word in match_text.lower() for sec_word in ["password", "secret", "private_key", "api_key", "token"]):
                                # Redact sensitive contents in line output
                                match_text = "[Redacted line containing potential secret]"

                            match_bytes = len(match_text.encode("utf-8"))
                            if total_result_bytes + match_bytes > MAX_RESULT_BYTES or len(matches) >= MAX_SEARCH_RESULTS:
                                truncated = True
                                break

                            matches.append({
                                "path": rel_path,
                                "line": line_idx,
                                "text": match_text
                            })
                            total_result_bytes += match_bytes
                            results_count += 1
            except Exception:
                # Continue if single file fails
                continue

    return {
        "query": query,
        "matches": matches,
        "files_searched": files_searched,
        "results_count": results_count,
        "truncated": truncated
    }
