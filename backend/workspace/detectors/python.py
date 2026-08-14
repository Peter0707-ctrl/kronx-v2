import os
import re
from typing import List, Dict, Any
from workspace.detectors.base import EcosystemDetector
from workspace.schema import EntryPointInfo, RouteInfo, DependencyInfo

class PythonDetector(EcosystemDetector):
    def detect_frameworks(self, files: List[str], workspace_root: str) -> List[Dict[str, Any]]:
        frameworks = []
        has_python = any(f.endswith(".py") for f in files)
        if not has_python:
            return frameworks

        # Framework detection by looking at source files
        fastapi_count = 0
        flask_count = 0
        django_count = 0

        for rel_path in files[:200]: # limit parsing for performance
            abs_path = os.path.join(workspace_root, rel_path)
            if not os.path.isfile(abs_path) or rel_path.endswith(".pyc"):
                continue
            try:
                with open(abs_path, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read()
                    if "from fastapi" in content or "import fastapi" in content:
                        fastapi_count += 1
                    if "from flask" in content or "import flask" in content:
                        flask_count += 1
                    if "django.core" in content or "from django." in content:
                        django_count += 1
            except Exception:
                pass

        if fastapi_count > 0:
            frameworks.append({"name": "FastAPI", "confidence": "HIGH" if fastapi_count > 1 else "MEDIUM"})
        if flask_count > 0:
            frameworks.append({"name": "Flask", "confidence": "HIGH" if flask_count > 1 else "MEDIUM"})
        if django_count > 0:
            frameworks.append({"name": "Django", "confidence": "HIGH"})

        return frameworks

    def detect_entry_points(self, files: List[str], workspace_root: str) -> List[EntryPointInfo]:
        entry_points = []
        for rel_path in files:
            name = os.path.basename(rel_path)
            if name in ["main.py", "app.py", "run.py", "wsgi.py", "asgi.py"]:
                abs_path = os.path.join(workspace_root, rel_path)
                try:
                    with open(abs_path, "r", encoding="utf-8", errors="ignore") as f:
                        content = f.read()
                        if "app = FastAPI(" in content or "FastAPI()" in content:
                            entry_points.append(EntryPointInfo(
                                path=rel_path,
                                confidence="HIGH",
                                reason="Declares a FastAPI app instance"
                            ))
                        elif "Flask(__name__)" in content:
                            entry_points.append(EntryPointInfo(
                                path=rel_path,
                                confidence="HIGH",
                                reason="Declares a Flask app instance"
                            ))
                        elif "import uvicorn" in content and "uvicorn.run(" in content:
                            entry_points.append(EntryPointInfo(
                                path=rel_path,
                                confidence="HIGH",
                                reason="Contains uvicorn runner execution code"
                            ))
                        elif "if __name__ == '__main__':" in content:
                            entry_points.append(EntryPointInfo(
                                path=rel_path,
                                confidence="MEDIUM",
                                reason="Contains Python main block definition"
                            ))
                except Exception:
                    pass
        return entry_points

    def detect_routes(self, files: List[str], workspace_root: str) -> List[RouteInfo]:
        routes = []
        route_pattern = re.compile(r'@(?:app|router|blueprint)\.(get|post|put|delete|patch)\(\s*["\']([^"\']+)["\']')
        
        for rel_path in files[:200]:
            if not rel_path.endswith(".py"):
                continue
            abs_path = os.path.join(workspace_root, rel_path)
            try:
                with open(abs_path, "r", encoding="utf-8", errors="ignore") as f:
                    for line_idx, line in enumerate(f, 1):
                        match = route_pattern.search(line)
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
        db_keywords = {
            "postgresql": ["psycopg2", "postgresql", "asyncpg"],
            "mysql": ["mysqlclient", "pymysql", "mysql+pymysql"],
            "sqlite": ["sqlite3", "sqlite"],
            "mongodb": ["pymongo", "motor"],
            "redis": ["redis", "aioredis"]
        }

        found_db_counts = {db: 0 for db in db_keywords}

        # Check in package manifests or settings
        for rel_path in files:
            if rel_path.endswith("requirements.txt") or rel_path.endswith("settings.py") or rel_path.endswith("config.py"):
                abs_path = os.path.join(workspace_root, rel_path)
                try:
                    with open(abs_path, "r", encoding="utf-8", errors="ignore") as f:
                        content = f.read().lower()
                        for db, keywords in db_keywords.items():
                            for kw in keywords:
                                if kw in content:
                                    found_db_counts[db] += 1
                except Exception:
                    pass

        for db, count in found_db_counts.items():
            if count > 0:
                databases.append({"name": db.capitalize(), "confidence": "HIGH" if count > 1 else "MEDIUM"})

        return databases

    def detect_tests(self, files: List[str], workspace_root: str) -> List[Dict[str, Any]]:
        test_files = []
        frameworks = set()

        for rel_path in files:
            name = os.path.basename(rel_path)
            if (name.startswith("test_") or name.endswith("_test.py")) and rel_path.endswith(".py"):
                test_files.append(rel_path)
                abs_path = os.path.join(workspace_root, rel_path)
                try:
                    with open(abs_path, "r", encoding="utf-8", errors="ignore") as f:
                        content = f.read()
                        if "pytest" in content:
                            frameworks.add("pytest")
                        if "unittest" in content:
                            frameworks.add("unittest")
                except Exception:
                    pass

        if not test_files and "tests" in [os.path.basename(f) for f in files]:
            # Found test directory
            return [{"framework": "pytest/unittest (Detected Directory)", "files": []}]

        results = []
        for fw in frameworks:
            results.append({"framework": fw, "files": test_files[:20]})
        if test_files and not frameworks:
            results.append({"framework": "unittest/pytest", "files": test_files[:20]})

        return results

    def parse_dependencies(self, files: List[str], workspace_root: str) -> List[DependencyInfo]:
        dependencies = []
        for rel_path in files:
            if rel_path.endswith("requirements.txt"):
                abs_path = os.path.join(workspace_root, rel_path)
                try:
                    with open(abs_path, "r", encoding="utf-8", errors="ignore") as f:
                        for line in f:
                            line = line.strip()
                            if not line or line.startswith("#") or line.startswith("-r"):
                                continue
                            # requirements formats: package==version, package>=version, package
                            parts = re.split(r'==|>=|<=|>|<|~=', line)
                            name = parts[0].strip()
                            version = parts[1].strip() if len(parts) > 1 else "latest"
                            dependencies.append(DependencyInfo(
                                name=name,
                                version=version,
                                package_manager="pip"
                            ))
                except Exception as e:
                    # requirement manifest parse error is caught but does not crash the scan
                    logger.warning(f"requirements.txt parse error: {e}")
        return dependencies
