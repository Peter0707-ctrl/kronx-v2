from abc import ABC, abstractmethod
from typing import List, Dict, Any
from workspace.schema import EntryPointInfo, RouteInfo, DependencyInfo

class EcosystemDetector(ABC):
    @abstractmethod
    def detect_frameworks(self, files: List[str], workspace_root: str) -> List[Dict[str, Any]]:
        """Return framework list of dictionaries with {"name": ..., "confidence": ...}."""
        pass

    @abstractmethod
    def detect_entry_points(self, files: List[str], workspace_root: str) -> List[EntryPointInfo]:
        """Return detected entry points with confidence values."""
        pass

    @abstractmethod
    def detect_routes(self, files: List[str], workspace_root: str) -> List[RouteInfo]:
        """Return static routes detected."""
        pass

    @abstractmethod
    def detect_databases(self, files: List[str], workspace_root: str) -> List[Dict[str, Any]]:
        """Return database list of dictionaries with {"name": ..., "confidence": ...}."""
        pass

    @abstractmethod
    def detect_tests(self, files: List[str], workspace_root: str) -> List[Dict[str, Any]]:
        """Return test definitions or directories."""
        pass

    @abstractmethod
    def parse_dependencies(self, files: List[str], workspace_root: str) -> List[DependencyInfo]:
        """Return parsed dependencies without installing any package."""
        pass
