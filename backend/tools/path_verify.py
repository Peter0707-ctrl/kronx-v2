import os

def verify_safe_path(workspace_root: str, target_path: str) -> str:
    """
    Resolve realpath of target_path and check that it stays inside workspace_root.
    Also resolves symbolic links and rejects target if it escapes the root.
    """
    real_root = os.path.realpath(workspace_root)
    
    # Target path can be relative or absolute.
    # If absolute but inside workspace_root, it should be resolved correctly.
    if os.path.isabs(target_path):
        joined_path = os.path.abspath(target_path)
    else:
        joined_path = os.path.abspath(os.path.join(real_root, target_path))
        
    real_target = os.path.realpath(joined_path)
    
    try:
        common = os.path.commonpath([real_root, real_target])
        if common != real_root:
            raise ValueError("PATH_OUTSIDE_WORKSPACE")
    except Exception:
        raise ValueError("PATH_OUTSIDE_WORKSPACE")
        
    return real_target
