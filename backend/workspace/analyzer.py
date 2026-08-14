import os
from typing import List, Dict, Any, Tuple
from workspace.schema import ProjectProfile, FileItem, SensitiveFileInfo, DependencyInfo, EntryPointInfo, RouteInfo
from workspace.detectors.python import PythonDetector
from workspace.detectors.node import NodeDetector
from workspace.detectors.laravel import LaravelDetector
from workspace.detectors.spring import SpringDetector
from workspace.detectors.generic import GenericDetector
from utils.logger import logger
import threading

class ProjectAnalyzer:
    def __init__(self):
        # Register modular ecosystem detectors
        self.detectors = [
            PythonDetector(),
            NodeDetector(),
            LaravelDetector(),
            SpringDetector(),
            GenericDetector()
        ]

    def analyze(
        self,
        workspace_root: str,
        files: List[FileItem],
        sensitive_files: List[SensitiveFileInfo],
        scan_stats: Dict[str, Any],
        cancellation_token: threading.Event = None
    ) -> ProjectProfile:
        """
        Analyze files list and generate complete structured ProjectProfile.
        Separates FACTS from INFERENCES and provides confidence metrics.
        """
        rel_paths = [f.path for f in files]
        
        # 1. Fact/Inference extraction initialization
        facts = []
        inferences = []
        warnings = []
        languages = set()

        # Map file extensions to languages
        lang_extensions = {
            ".py": "Python",
            ".js": "JavaScript",
            ".ts": "TypeScript",
            ".tsx": "TypeScript",
            ".jsx": "JavaScript",
            ".java": "Java",
            ".php": "PHP",
            ".c": "C",
            ".cpp": "C++",
            ".go": "Go",
            ".rs": "Rust",
            ".rb": "Ruby"
        }
        for f in files:
            _, ext = os.path.splitext(f.path.lower())
            if ext in lang_extensions:
                languages.add(lang_extensions[ext])

        # Add facts about manifests
        manifests = {
            "requirements.txt": "Python dependencies requirements file",
            "package.json": "NPM package definition file",
            "composer.json": "Composer PHP dependencies file",
            "pom.xml": "Maven Java dependencies definition file",
            "build.gradle": "Gradle Java build configuration file",
            "pyproject.toml": "Python build system manifest file",
            "artisan": "Laravel CLI entry tool file"
        }
        for path in rel_paths:
            name = os.path.basename(path)
            if name in manifests:
                facts.append(f"Fact: '{name}' exists in workspace.")
                inferences.append(f"Inference: Project is configured as a {manifests[name]} ecosystem.")

        if cancellation_token and cancellation_token.is_set():
            logger.info("Scan job cancelled cooperatively during analysis step.")
            raise ValueError("SCAN_CANCELLED")

        # 2. Invoke modular detectors
        frameworks = []
        entry_points = []
        routes = []
        databases = []
        tests = []
        dependencies = []

        for detector in self.detectors:
            if cancellation_token and cancellation_token.is_set():
                raise ValueError("SCAN_CANCELLED")

            # Frameworks
            fws = detector.detect_frameworks(rel_paths, workspace_root)
            if fws:
                frameworks.extend(fws)
                for fw in fws:
                    facts.append(f"Fact: Source file imports or manifest declarations matching framework '{fw['name']}' found.")
                    inferences.append(f"Inference: Project relies on the '{fw['name']}' framework (Confidence: {fw['confidence']}).")

            # Entry Points
            eps = detector.detect_entry_points(rel_paths, workspace_root)
            if eps:
                entry_points.extend(eps)
                for ep in eps:
                    facts.append(f"Fact: Entry point candidate '{ep.path}' resolved on disk.")
                    inferences.append(f"Inference: Entry point resolved with '{ep.confidence}' confidence: {ep.reason}")

            # Routes
            rts = detector.detect_routes(rel_paths, workspace_root)
            if rts:
                routes.extend(rts)

            # Databases
            dbs = detector.detect_databases(rel_paths, workspace_root)
            if dbs:
                databases.extend(dbs)
                for db in dbs:
                    facts.append(f"Fact: Database connection library or setup declarations for '{db['name']}' discovered.")
                    inferences.append(f"Inference: Project uses '{db['name']}' database engine.")

            # Tests
            tsts = detector.detect_tests(rel_paths, workspace_root)
            if tsts:
                tests.extend(tsts)

            # Dependencies
            deps = detector.parse_dependencies(rel_paths, workspace_root)
            if deps:
                dependencies.extend(deps)

        if cancellation_token and cancellation_token.is_set():
            raise ValueError("SCAN_CANCELLED")

        # 3. Generate Architecture Summary from evidence
        arch_parts = []
        if languages:
            arch_parts.append(f"Ecosystem Languages: {', '.join(languages)}")
        if frameworks:
            fw_names = [f["name"] for f in frameworks]
            arch_parts.append(f"Frameworks: {', '.join(fw_names)}")
        if databases:
            db_names = [d["name"] for d in databases]
            arch_parts.append(f"Databases: {', '.join(db_names)}")
        if tests:
            test_fw_names = [t["framework"] for t in tests]
            arch_parts.append(f"Testing Frameworks: {', '.join(test_fw_names)}")

        architecture_summary = " | ".join(arch_parts) if arch_parts else "Generic or Unknown project architecture structure."

        # Project structure map
        project_structure = {
            "root": os.path.basename(workspace_root),
            "children": {}
        }
        for f in files[:200]: # top 200 files representation
            parts = f.path.split("/")
            curr = project_structure["children"]
            for part in parts[:-1]:
                if part not in curr:
                    curr[part] = {}
                curr = curr[part]

        # Filter out generated files list (just represent them if categorised)
        generated_files = [f for f in files if f.category in ["binary", "generated"]]

        # Statistics
        statistics = {
            "total_files": scan_stats.get("total_files", 0),
            "total_size_bytes": scan_stats.get("total_size_bytes", 0),
            "category_counts": scan_stats.get("category_counts", {}),
            "ignored_counts": scan_stats.get("ignored_counts", 0),
            "sensitive_counts": len(sensitive_files)
        }

        # Build Project Profile
        profile = ProjectProfile(
            project_name=os.path.basename(workspace_root),
            root_path=workspace_root,
            languages=list(languages),
            frameworks=frameworks,
            package_managers=list(set(dep.package_manager for dep in dependencies)) if dependencies else [],
            dependencies=dependencies,
            entry_points=entry_points,
            routes=routes,
            databases=databases,
            tests=tests,
            documentation=[],  # populated if readme found
            source_files=files,
            sensitive_files=sensitive_files,
            generated_files=generated_files,
            architecture_summary=architecture_summary,
            project_structure=project_structure,
            statistics=statistics,
            warnings=warnings,
            facts=facts,
            inferences=inferences
        )
        return profile
