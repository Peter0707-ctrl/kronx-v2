from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Any

class Workspace(BaseModel):
    workspace_id: str
    root_path: str
    created_at: str
    status: str

class ScanJob(BaseModel):
    id: str
    workspace_id: str
    status: str  # QUEUED, RUNNING, COMPLETED, FAILED, CANCELLED
    started_at: str
    completed_at: Optional[str] = None
    progress: float = 0.0
    error: Optional[str] = None
    result: Optional[Dict[str, Any]] = None

class DependencyInfo(BaseModel):
    name: str
    version: str
    package_manager: str
    is_dev: bool = False

class EntryPointInfo(BaseModel):
    path: str
    confidence: str  # HIGH, MEDIUM, LOW
    reason: str

class RouteInfo(BaseModel):
    path: str
    method: str
    controller: Optional[str] = None
    source_file: str
    confidence: str  # HIGH, MEDIUM, LOW

class SensitiveFileInfo(BaseModel):
    path: str
    category: str
    sensitive: bool = True
    reason: str

class FileItem(BaseModel):
    path: str
    category: str  # source, test, configuration, documentation, dependency, generated, binary, asset, sensitive, unknown
    size_bytes: int
    modified_at: str

class ProjectProfile(BaseModel):
    project_name: str
    root_path: str
    languages: List[str]
    frameworks: List[Dict[str, Any]]  # {"name": ..., "confidence": ...}
    package_managers: List[str]
    dependencies: List[DependencyInfo]
    entry_points: List[EntryPointInfo]
    routes: List[RouteInfo]
    databases: List[Dict[str, Any]]  # {"name": ..., "confidence": ...}
    tests: List[Dict[str, Any]]  # {"framework": ..., "files": [...]}
    documentation: List[Dict[str, Any]]  # {"path": ..., "summary": ...}
    source_files: List[FileItem]
    sensitive_files: List[SensitiveFileInfo]
    generated_files: List[FileItem]
    architecture_summary: str
    project_structure: Dict[str, Any]
    statistics: Dict[str, Any]
    warnings: List[str]
    facts: List[str]
    inferences: List[str]
