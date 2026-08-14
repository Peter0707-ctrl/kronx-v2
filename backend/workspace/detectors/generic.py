from typing import List, Dict, Any
from workspace.detectors.base import EcosystemDetector
from workspace.schema import EntryPointInfo, RouteInfo, DependencyInfo

class GenericDetector(EcosystemDetector):
    def detect_frameworks(self, files: List[str], workspace_root: str) -> List[Dict[str, Any]]:
        return []

    def detect_entry_points(self, files: List[str], workspace_root: str) -> List[EntryPointInfo]:
        return []

    def detect_routes(self, files: List[str], workspace_root: str) -> List[RouteInfo]:
        return []

    def detect_databases(self, files: List[str], workspace_root: str) -> List[Dict[str, Any]]:
        return []

    def detect_tests(self, files: List[str], workspace_root: str) -> List[Dict[str, Any]]:
        return []

    def parse_dependencies(self, files: List[str], workspace_root: str) -> List[DependencyInfo]:
        return []
