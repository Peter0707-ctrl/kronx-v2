import os
import re
from typing import List, Dict, Any
from workspace.detectors.base import EcosystemDetector
from workspace.schema import EntryPointInfo, RouteInfo, DependencyInfo
from utils.logger import logger

class SpringDetector(EcosystemDetector):
    def detect_frameworks(self, files: List[str], workspace_root: str) -> List[Dict[str, Any]]:
        frameworks = []
        has_java = any(f.endswith(".java") for f in files)
        if not has_java:
            return frameworks

        # Maven / Gradle detection
        is_spring = False
        for rel_path in files:
            if rel_path.endswith("pom.xml") or rel_path.endswith("build.gradle"):
                abs_path = os.path.join(workspace_root, rel_path)
                try:
                    with open(abs_path, "r", encoding="utf-8", errors="ignore") as f:
                        content = f.read()
                        if "spring-boot" in content or "springframework" in content:
                            is_spring = True
                            break
                except Exception:
                    pass

        if is_spring:
            frameworks.append({"name": "Spring Boot", "confidence": "HIGH"})
        return frameworks

    def detect_entry_points(self, files: List[str], workspace_root: str) -> List[EntryPointInfo]:
        entry_points = []
        for rel_path in files[:500]: # limit scanning
            if not rel_path.endswith(".java"):
                continue
            abs_path = os.path.join(workspace_root, rel_path)
            try:
                with open(abs_path, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read()
                    if "@SpringBootApplication" in content and "public static void main" in content:
                        entry_points.append(EntryPointInfo(
                            path=rel_path,
                            confidence="HIGH",
                            reason="Contains Spring Boot Application entrypoint annotation"
                        ))
                    elif "public static void main" in content and "String[] args" in content:
                        entry_points.append(EntryPointInfo(
                            path=rel_path,
                            confidence="MEDIUM",
                            reason="Standard Java execution entry point"
                        ))
            except Exception:
                pass
        return entry_points

    def detect_routes(self, files: List[str], workspace_root: str) -> List[RouteInfo]:
        routes = []
        # Support GetMapping, PostMapping, RequestMapping
        mapping_pattern = re.compile(r'@(?:Get|Post|Put|Delete|Request)Mapping\(\s*(?:value\s*=\s*)?["\']([^"\']+)["\']')
        
        for rel_path in files[:200]:
            if not rel_path.endswith(".java"):
                continue
            abs_path = os.path.join(workspace_root, rel_path)
            try:
                with open(abs_path, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read()
                    if "@RestController" in content or "@Controller" in content:
                        # Find mapping lines
                        f.seek(0)
                        for line_idx, line in enumerate(f, 1):
                            match = mapping_pattern.search(line)
                            if match:
                                path = match.group(1)
                                method = "ANY"
                                if "Get" in line:
                                    method = "GET"
                                elif "Post" in line:
                                    method = "POST"
                                elif "Put" in line:
                                    method = "PUT"
                                elif "Delete" in line:
                                    method = "DELETE"
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
        for rel_path in files:
            if rel_path.endswith("pom.xml") or rel_path.endswith("build.gradle") or rel_path.endswith("application.properties") or rel_path.endswith("application.yml"):
                abs_path = os.path.join(workspace_root, rel_path)
                try:
                    with open(abs_path, "r", encoding="utf-8", errors="ignore") as f:
                        content = f.read().lower()
                        db_keywords = {
                            "postgresql": ["postgresql", "postgres"],
                            "mysql": ["mysql-connector", "mysql"],
                            "h2": ["h2database", "jdbc:h2"],
                            "mongodb": ["mongodb", "mongo"]
                        }
                        for db, keywords in db_keywords.items():
                            for kw in keywords:
                                if kw in content:
                                    databases.append({"name": db.capitalize(), "confidence": "HIGH"})
                                    break
                except Exception:
                    pass
        return databases

    def detect_tests(self, files: List[str], workspace_root: str) -> List[Dict[str, Any]]:
        test_files = []
        for rel_path in files:
            name = os.path.basename(rel_path)
            if (name.endswith("Test.java") or name.endswith("Tests.java")) and rel_path.endswith(".java"):
                test_files.append(rel_path)

        if test_files:
            return [{"framework": "JUnit", "files": test_files[:20]}]
        return []

    def parse_dependencies(self, files: List[str], workspace_root: str) -> List[DependencyInfo]:
        dependencies = []
        for rel_path in files:
            if rel_path.endswith("pom.xml"):
                abs_path = os.path.join(workspace_root, rel_path)
                try:
                    with open(abs_path, "r", encoding="utf-8", errors="ignore") as f:
                        content = f.read()
                        # Match dependency blocks using regex
                        dep_blocks = re.findall(r'<dependency>([\s\S]*?)</dependency>', content)
                        for block in dep_blocks:
                            group_id_match = re.search(r'<groupId>([^<]+)</groupId>', block)
                            artifact_id_match = re.search(r'<artifactId>([^<]+)</artifactId>', block)
                            version_match = re.search(r'<version>([^<]+)</version>', block)
                            
                            if group_id_match and artifact_id_match:
                                name = f"{group_id_match.group(1)}:{artifact_id_match.group(1)}"
                                version = version_match.group(1) if version_match else "latest"
                                dependencies.append(DependencyInfo(
                                    name=name,
                                    version=version,
                                    package_manager="maven"
                                ))
                except Exception as e:
                    logger.warning(f"pom.xml parse error: {e}")
        return dependencies
