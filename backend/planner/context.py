"""
Phase 2C — Context Builder
Combines Phase 2A ProjectProfile + user objective into a structured context.

CRITICAL SECURITY:
  - Never reads workspace files directly (all inspection goes via ToolRuntime)
  - Sensitive file contents are NEVER loaded; only metadata is exposed
  - Statements are strictly partitioned into FACT / INFERENCE / ASSUMPTION
"""
from __future__ import annotations
from typing import List, Optional, Dict, Any, Tuple

from workspace.schema import ProjectProfile
from planner.schemas import MAX_FACTS, MAX_INFERENCES


# Sensitive category names that must never contribute file *contents* to context
_SENSITIVE_CATEGORIES = frozenset(["sensitive"])


class ContextBuilder:
    """
    Constructs a planning context from a workspace ProjectProfile and objective.
    Never accesses the filesystem directly.
    """

    def __init__(self, profile: Optional[ProjectProfile], objective: str):
        self._profile = profile
        self._objective = objective

    # ------------------------------------------------------------------
    # Public
    # ------------------------------------------------------------------

    def build(self) -> Tuple[List[str], List[str], List[str]]:
        """Return (facts, inferences, assumptions) — all plain strings."""
        facts: List[str] = []
        inferences: List[str] = []
        assumptions: List[str] = []

        if self._profile is None:
            # No scan profile available — everything is an assumption
            assumptions.append("No workspace scan profile available; project structure is unknown.")
            assumptions.append(f"Objective: '{self._objective[:200]}'.")
            return facts[:MAX_FACTS], inferences[:MAX_INFERENCES], assumptions

        p = self._profile

        # ---- FACTS (directly evidenced by scan) ----
        if p.languages:
            facts.append(f"Detected languages: {', '.join(p.languages)}.")
        if p.frameworks:
            for fw in p.frameworks:
                conf = fw.get("confidence", "UNKNOWN")
                facts.append(f"Framework detected: {fw['name']} (confidence: {conf}).")
        if p.package_managers:
            facts.append(f"Package managers present: {', '.join(p.package_managers)}.")
        if p.entry_points:
            for ep in p.entry_points[:5]:      # cap at 5 to avoid verbosity
                facts.append(f"Entry point: '{ep.path}' (confidence: {ep.confidence}).")
        if p.databases:
            for db in p.databases:
                facts.append(f"Database indicator detected: {db.get('name', 'unknown')} (confidence: {db.get('confidence', '?')}).")
        if p.tests:
            for t in p.tests[:5]:
                facts.append(f"Test framework detected: {t.get('framework', 'unknown')}.")
        if p.sensitive_files:
            for sf in p.sensitive_files[:10]:
                # ONLY log path and category — never content
                facts.append(f"Sensitive file found (metadata only): '{sf.path}' category='{sf.category}'.")
        # Source file count
        src_count = len(p.source_files)
        if src_count:
            facts.append(f"Total source files scanned: {src_count}.")
        if p.statistics:
            total = p.statistics.get("total_files")
            if total is not None:
                facts.append(f"Total workspace files: {total}.")
        if p.warnings:
            for w in p.warnings[:5]:
                facts.append(f"Scanner warning: {w}")
        # Incorporate existing Phase 2A facts
        for f in (p.facts or [])[:50]:
            facts.append(f)

        # ---- INFERENCES (derived from evidence) ----
        if p.frameworks:
            names = [fw["name"] for fw in p.frameworks]
            if "FastAPI" in names or "Flask" in names or "Django" in names:
                inferences.append("Project appears to be a Python web application.")
            if "React" in names or "Next.js" in names:
                inferences.append("Project appears to include a JavaScript/TypeScript frontend.")
            if "Spring Boot" in names:
                inferences.append("Project appears to be a Java Spring Boot application.")
            if "Laravel" in names:
                inferences.append("Project appears to be a PHP Laravel application.")
        if p.databases:
            inferences.append("Application likely uses persistent data storage.")
        if p.routes:
            inferences.append(f"Project exposes approximately {len(p.routes)} HTTP route(s).")
        # Incorporate existing Phase 2A inferences
        for inf in (p.inferences or [])[:50]:
            inferences.append(inf)

        # ---- ASSUMPTIONS (user-dependent or uncertain) ----
        assumptions.append(f"Objective (user-provided): '{self._objective[:200]}'.")
        assumptions.append("Changes to the project are authorized by the workspace owner.")
        assumptions.append("The current scan profile reflects the latest workspace state.")

        # Cap at resource limits
        return facts[:MAX_FACTS], inferences[:MAX_INFERENCES], assumptions

    def summary_for_mode(self, mode: str) -> str:
        """Generate a mode-appropriate one-paragraph context summary."""
        if self._profile is None:
            return f"No workspace profile available. Planning based on objective only."
        p = self._profile
        lang_str = ", ".join(p.languages) if p.languages else "unknown"
        fw_str = ", ".join(fw["name"] for fw in p.frameworks) if p.frameworks else "none detected"
        return (
            f"Workspace '{p.project_name}' uses {lang_str} "
            f"with frameworks: {fw_str}. "
            f"Planning mode: {mode}."
        )
