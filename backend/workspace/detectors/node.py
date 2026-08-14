import os
import re
import json
from typing import List, Dict, Any
from workspace.detectors.base import EcosystemDetector
from workspace.schema import EntryPointInfo, RouteInfo, DependencyInfo
from utils.logger import logger

class NodeDetector(EcosystemDetector):
    def detect_frameworks(self, files: List[str], workspace_root: str) -> List[Dict[str, Any]]:
        frameworks = []
        package_json_path = next((f for f in files if f.endswith("package.json")), None)
        if not package_json_path:
            return frameworks

        abs_path = os.path.join(workspace_root, package_json_path)
        try:
            with open(abs_path, "r", encoding="utf-8", errors="ignore") as f:
                data = json.load(f)
                deps = {**data.get("dependencies", {}), **data.get("devDependencies", {})}
                
                if "next" in deps:
                    frameworks.append({"name": "Next.js", "confidence": "HIGH"})
                if "react" in deps:
                    frameworks.append({"name": "React", "confidence": "HIGH"})
                if "vue" in deps:
                    frameworks.append({"name": "Vue", "confidence": "HIGH"})
                if "express" in deps:
                    frameworks.append({"name": "Express", "confidence": "HIGH"})
        except Exception:
            pass
        return frameworks

    def detect_entry_points(self, files: List[str], workspace_root: str) -> List[EntryPointInfo]:
        entry_points = []
        package_json_path = next((f for f in files if f.endswith("package.json")), None)
        
        if package_json_path:
            abs_path = os.path.join(workspace_root, package_json_path)
            try:
                with open(abs_path, "r", encoding="utf-8", errors="ignore") as f:
                    data = json.load(f)
                    # 1. Check main field
                    main_file = data.get("main")
                    if main_file:
                        entry_points.append(EntryPointInfo(
                            path=os.path.join(os.path.dirname(package_json_path), main_file).replace("\\", "/"),
                            confidence="HIGH",
                            reason="Declared in package.json main field"
                        ))
                    # 2. Check scripts start field
                    start_script = data.get("scripts", {}).get("start", "")
                    if "node" in start_script or "next start" in start_script:
                        # Extract script target file name
                        target = next((word for word in start_script.split() if word.endswith(".js")), None)
                        if target:
                            entry_points.append(EntryPointInfo(
                                path=os.path.join(os.path.dirname(package_json_path), target).replace("\\", "/"),
                                confidence="HIGH",
                                reason="Declared in package.json start script"
                            ))
            except Exception:
                pass

        # Check standard default filenames
        for rel_path in files:
            name = os.path.basename(rel_path)
            if name in ["server.js", "index.js", "app.js", "server.ts", "index.ts"]:
                # Avoid duplicate entry points if already added via package.json
                if not any(ep.path == rel_path for ep in entry_points):
                    entry_points.append(EntryPointInfo(
                        path=rel_path,
                        confidence="MEDIUM",
                        reason=f"Standard default Node/TS entry filename: {name}"
                    ))
        return entry_points

    def detect_routes(self, files: List[str], workspace_root: str) -> List[RouteInfo]:
        routes = []
        express_route_pattern = re.compile(r'(?:app|router)\.(get|post|put|delete|patch)\(\s*["\']([^"\']+)["\']')
        
        for rel_path in files[:200]:
            if not (rel_path.endswith(".js") or rel_path.endswith(".ts") or rel_path.endswith(".tsx")):
                continue
            abs_path = os.path.join(workspace_root, rel_path)
            try:
                with open(abs_path, "r", encoding="utf-8", errors="ignore") as f:
                    # 1. Express routing checks
                    for line_idx, line in enumerate(f, 1):
                        match = express_route_pattern.search(line)
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

        # 2. Next.js App Router / Pages Router checks
        # Check files matching app/api/page.ts or pages/api/...
        for rel_path in files:
            normalized = rel_path.replace("\\", "/")
            if "app/api/" in normalized and (normalized.endswith("/route.ts") or normalized.endswith("/route.js")):
                # Extract path
                api_path = normalized.split("app")[-1].replace("/route.ts", "").replace("/route.js", "")
                routes.append(RouteInfo(
                    path=api_path,
                    method="ANY",
                    controller="Next.js App Router Handler",
                    source_file=rel_path,
                    confidence="HIGH"
                ))
            elif "pages/api/" in normalized and (normalized.endswith(".ts") or normalized.endswith(".js")):
                api_path = normalized.split("pages")[-1].replace(".ts", "").replace(".js", "")
                routes.append(RouteInfo(
                    path=api_path,
                    method="ANY",
                    controller="Next.js Pages API Handler",
                    source_file=rel_path,
                    confidence="HIGH"
                ))
        return routes

    def detect_databases(self, files: List[str], workspace_root: str) -> List[Dict[str, Any]]:
        databases = []
        package_json_path = next((f for f in files if f.endswith("package.json")), None)
        if not package_json_path:
            return databases

        abs_path = os.path.join(workspace_root, package_json_path)
        try:
            with open(abs_path, "r", encoding="utf-8", errors="ignore") as f:
                data = json.load(f)
                deps = {**data.get("dependencies", {}), **data.get("devDependencies", {})}
                
                db_mappings = {
                    "pg": "PostgreSQL",
                    "mysql2": "MySQL",
                    "mongodb": "MongoDB",
                    "mongoose": "MongoDB",
                    "redis": "Redis",
                    "sqlite3": "SQLite"
                }
                
                for pkg, db_name in db_mappings.items():
                    if pkg in deps:
                        databases.append({"name": db_name, "confidence": "HIGH"})
        except Exception:
            pass
        return databases

    def detect_tests(self, files: List[str], workspace_root: str) -> List[Dict[str, Any]]:
        test_files = []
        frameworks = set()
        package_json_path = next((f for f in files if f.endswith("package.json")), None)
        
        if package_json_path:
            abs_path = os.path.join(workspace_root, package_json_path)
            try:
                with open(abs_path, "r", encoding="utf-8", errors="ignore") as f:
                    data = json.load(f)
                    deps = {**data.get("dependencies", {}), **data.get("devDependencies", {})}
                    if "jest" in deps:
                        frameworks.add("Jest")
                    if "mocha" in deps:
                        frameworks.add("Mocha")
                    if "vitest" in deps:
                        frameworks.add("Vitest")
            except Exception:
                pass

        for rel_path in files:
            name = os.path.basename(rel_path)
            if (".test." in name or ".spec." in name) and (rel_path.endswith(".js") or rel_path.endswith(".ts") or rel_path.endswith(".tsx")):
                test_files.append(rel_path)

        results = []
        for fw in frameworks:
            results.append({"framework": fw, "files": test_files[:20]})
        if test_files and not frameworks:
            results.append({"framework": "Jest/Mocha/Vitest", "files": test_files[:20]})
            
        return results

    def parse_dependencies(self, files: List[str], workspace_root: str) -> List[DependencyInfo]:
        dependencies = []
        package_json_path = next((f for f in files if f.endswith("package.json")), None)
        if not package_json_path:
            return dependencies

        abs_path = os.path.join(workspace_root, package_json_path)
        try:
            with open(abs_path, "r", encoding="utf-8", errors="ignore") as f:
                data = json.load(f)
                
                # Normal dependencies
                for name, version in data.get("dependencies", {}).items():
                    dependencies.append(DependencyInfo(
                        name=name,
                        version=str(version),
                        package_manager="npm",
                        is_dev=False
                    ))
                
                # Dev dependencies
                for name, version in data.get("devDependencies", {}).items():
                    dependencies.append(DependencyInfo(
                        name=name,
                        version=str(version),
                        package_manager="npm",
                        is_dev=True
                    ))
        except Exception as e:
            # manifest parse error should be handled cleanly, warning generated
            logger.warning(f"package.json parse error: {e}")
        return dependencies
