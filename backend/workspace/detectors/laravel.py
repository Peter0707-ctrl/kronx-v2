import os
import re
import json
from typing import List, Dict, Any
from workspace.detectors.base import EcosystemDetector
from workspace.schema import EntryPointInfo, RouteInfo, DependencyInfo
from utils.logger import logger

class LaravelDetector(EcosystemDetector):
    def detect_frameworks(self, files: List[str], workspace_root: str) -> List[Dict[str, Any]]:
        frameworks = []
        is_laravel = "artisan" in [os.path.basename(f) for f in files]
        if is_laravel:
            frameworks.append({"name": "Laravel", "confidence": "HIGH"})
        elif any(f.endswith("composer.json") for f in files):
            composer_path = next((f for f in files if f.endswith("composer.json")), None)
            abs_path = os.path.join(workspace_root, composer_path)
            try:
                with open(abs_path, "r", encoding="utf-8", errors="ignore") as f:
                    data = json.load(f)
                    reqs = data.get("require", {})
                    if "laravel/framework" in reqs:
                        frameworks.append({"name": "Laravel", "confidence": "HIGH"})
            except Exception:
                pass
        return frameworks

    def detect_entry_points(self, files: List[str], workspace_root: str) -> List[EntryPointInfo]:
        entry_points = []
        for rel_path in files:
            name = os.path.basename(rel_path)
            if name == "artisan":
                entry_points.append(EntryPointInfo(
                    path=rel_path,
                    confidence="HIGH",
                    reason="Laravel CLI Console entrypoint"
                ))
            elif name == "index.php" and "public/" in rel_path:
                entry_points.append(EntryPointInfo(
                    path=rel_path,
                    confidence="HIGH",
                    reason="Laravel public web controller entrypoint"
                ))
        return entry_points

    def detect_routes(self, files: List[str], workspace_root: str) -> List[RouteInfo]:
        routes = []
        laravel_route_pattern = re.compile(r'Route::(get|post|put|delete|patch)\(\s*["\']([^"\']+)["\']')
        
        for rel_path in files:
            # Check route config files
            if "routes/" in rel_path and rel_path.endswith(".php"):
                abs_path = os.path.join(workspace_root, rel_path)
                try:
                    with open(abs_path, "r", encoding="utf-8", errors="ignore") as f:
                        for line_idx, line in enumerate(f, 1):
                            match = laravel_route_pattern.search(line)
                            if match:
                                method = match.group(1).upper()
                                path = match.group(2)
                                routes.append(RouteInfo(
                                    path=path,
                                    method=method,
                                    controller=f"Line {line_idx}",
                                    source_file=rel_path,
                                    confidence="HIGH"
                                ))
                except Exception:
                    pass
        return routes

    def detect_databases(self, files: List[str], workspace_root: str) -> List[Dict[str, Any]]:
        databases = []
        # Search config/database.php or .env references
        for rel_path in files:
            if rel_path.endswith("config/database.php"):
                abs_path = os.path.join(workspace_root, rel_path)
                try:
                    with open(abs_path, "r", encoding="utf-8", errors="ignore") as f:
                        content = f.read().lower()
                        db_drivers = {"pgsql": "PostgreSQL", "mysql": "MySQL", "sqlite": "SQLite"}
                        for drv, name in db_drivers.items():
                            if f"'driver' => '{drv}'" in content or f'"driver" => "{drv}"' in content:
                                databases.append({"name": name, "confidence": "HIGH"})
                except Exception:
                    pass
        return databases

    def detect_tests(self, files: List[str], workspace_root: str) -> List[Dict[str, Any]]:
        test_files = []
        has_phpunit = False

        for rel_path in files:
            name = os.path.basename(rel_path)
            if name == "phpunit.xml":
                has_phpunit = True
            elif (name.endswith("Test.php") or "tests/" in rel_path) and rel_path.endswith(".php"):
                test_files.append(rel_path)

        if has_phpunit or test_files:
            return [{"framework": "PHPUnit", "files": test_files[:20]}]
        return []

    def parse_dependencies(self, files: List[str], workspace_root: str) -> List[DependencyInfo]:
        dependencies = []
        composer_path = next((f for f in files if f.endswith("composer.json")), None)
        if not composer_path:
            return dependencies

        abs_path = os.path.join(workspace_root, composer_path)
        try:
            with open(abs_path, "r", encoding="utf-8", errors="ignore") as f:
                data = json.load(f)
                
                # Composer require
                for name, version in data.get("require", {}).items():
                    dependencies.append(DependencyInfo(
                        name=name,
                        version=str(version),
                        package_manager="composer",
                        is_dev=False
                    ))
                
                # Composer require-dev
                for name, version in data.get("require-dev", {}).items():
                    dependencies.append(DependencyInfo(
                        name=name,
                        version=str(version),
                        package_manager="composer",
                        is_dev=True
                    ))
        except Exception as e:
            logger.warning(f"composer.json parse error: {e}")
        return dependencies
