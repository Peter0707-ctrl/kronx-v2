"""
Phase 2C — Reasoning Engine
Deterministic structured reasoning helpers.
Returns concise decision summaries — never hidden chain-of-thought.
Each mode produces a deterministic task skeleton appropriate to that mode.
"""
from __future__ import annotations
import uuid
from typing import List, Tuple

from planner.schemas import (
    PlanningMode, PlanningTask, TaskType, TaskStatus,
    ComplexityLevel, RiskLevel, PermissionAnalysis, PermissionRequirement
)


def _t(
    title: str,
    description: str,
    task_type: TaskType,
    deps: List[str] = None,
    tools: List[str] = None,
    complexity: ComplexityLevel = ComplexityLevel.LOW,
    risk: RiskLevel = RiskLevel.LOW,
) -> PlanningTask:
    tid = f"task_{uuid.uuid4().hex[:6]}"
    return PlanningTask(
        task_id=tid,
        title=title,
        description=description,
        task_type=task_type,
        dependencies=deps or [],
        required_tools=tools or [],
        estimated_complexity=complexity,
        risk_level=risk,
        status=TaskStatus.PENDING,
    )


def _read_tools() -> List[str]:
    return ["read_file", "list_directory", "search_code", "inspect_file"]


class ReasoningEngine:
    """
    Produces mode-appropriate task skeletons.
    All tasks are INSPECT / ANALYZE / DESIGN / VERIFY / DOCUMENT / WAIT_FOR_PERMISSION.
    No task directly triggers WRITE or EXECUTE operations.
    """

    def build_tasks(
        self,
        mode: PlanningMode,
        objective: str,
        has_profile: bool,
    ) -> List[PlanningTask]:
        mode_val = mode.value if hasattr(mode, "value") else mode
        builders = {
            PlanningMode.ANALYZE.value:   self._analyze_tasks,
            PlanningMode.DESIGN.value:    self._design_tasks,
            PlanningMode.DEBUG.value:     self._debug_tasks,
            PlanningMode.REFACTOR.value:  self._refactor_tasks,
            PlanningMode.REVIEW.value:    self._review_tasks,
            PlanningMode.DOCUMENT.value:  self._document_tasks,
        }
        builder = builders.get(mode_val, self._analyze_tasks)
        return builder(objective, has_profile)

    # ------------------------------------------------------------------
    # Permission analysis (deterministic — never self-grants)
    # ------------------------------------------------------------------

    def permission_analysis(self) -> List[PermissionAnalysis]:
        return [
            PermissionAnalysis(
                permission="READ",
                status=PermissionRequirement.ALLOWED,
                reason="Safe read-only inspection is permitted within authorized workspace.",
            ),
            PermissionAnalysis(
                permission="WRITE",
                status=PermissionRequirement.REQUIRES_EXPLICIT_PERMISSION,
                reason="Write access is disabled in Phase 2B and requires explicit user grant.",
            ),
            PermissionAnalysis(
                permission="EXECUTE",
                status=PermissionRequirement.BLOCKED,
                reason="Shell/process execution is not available in the current phase.",
            ),
            PermissionAnalysis(
                permission="NETWORK",
                status=PermissionRequirement.BLOCKED,
                reason="Outbound network access from tools is blocked.",
            ),
            PermissionAnalysis(
                permission="ADMIN",
                status=PermissionRequirement.FORBIDDEN,
                reason="ADMIN permission is permanently forbidden for AI-initiated requests.",
            ),
        ]

    # ------------------------------------------------------------------
    # Mode task builders
    # ------------------------------------------------------------------

    def _analyze_tasks(self, objective: str, has_profile: bool) -> List[PlanningTask]:
        t1 = _t("Inspect project structure",
                "List top-level directories and entry points.",
                TaskType.INSPECT, tools=["list_directory"])
        t2 = _t("Inspect relevant source modules",
                "Read key source files identified from the project profile.",
                TaskType.INSPECT, deps=[t1.task_id], tools=["read_file", "inspect_file"],
                complexity=ComplexityLevel.MEDIUM)
        t3 = _t("Analyze component relationships",
                "Identify dependencies between modules relevant to the objective.",
                TaskType.ANALYZE, deps=[t2.task_id],
                complexity=ComplexityLevel.MEDIUM)
        t4 = _t("Identify potential impacts",
                "Document components that may be affected by the proposed change.",
                TaskType.ANALYZE, deps=[t3.task_id])
        t5 = _t("Summarise findings",
                "Produce structured analysis summary with evidence.",
                TaskType.DOCUMENT, deps=[t4.task_id])
        return [t1, t2, t3, t4, t5]

    def _design_tasks(self, objective: str, has_profile: bool) -> List[PlanningTask]:
        t1 = _t("Inspect current architecture",
                "Read architecture-relevant files and routing structure.",
                TaskType.INSPECT, tools=_read_tools())
        t2 = _t("Identify affected components",
                "Determine which modules require changes.",
                TaskType.ANALYZE, deps=[t1.task_id], complexity=ComplexityLevel.MEDIUM)
        t3 = _t("Design proposed changes",
                "Produce a structured design document describing the change.",
                TaskType.DESIGN, deps=[t2.task_id], complexity=ComplexityLevel.HIGH,
                risk=RiskLevel.MEDIUM)
        t4 = _t("Request WRITE permission",
                "Await explicit user authorisation before any file mutation.",
                TaskType.WAIT_FOR_PERMISSION, deps=[t3.task_id], risk=RiskLevel.HIGH)
        t5 = _t("Define verification tests",
                "Specify tests to confirm correct implementation.",
                TaskType.VERIFY, deps=[t4.task_id])
        return [t1, t2, t3, t4, t5]

    def _debug_tasks(self, objective: str, has_profile: bool) -> List[PlanningTask]:
        t1 = _t("Understand reported problem",
                "Parse objective for problem description and symptoms.",
                TaskType.ANALYZE)
        t2 = _t("Inspect relevant architecture",
                "Read files and modules most likely to contain the fault.",
                TaskType.INSPECT, deps=[t1.task_id], tools=_read_tools())
        t3 = _t("Search for error patterns",
                "Search codebase for error-related strings or patterns.",
                TaskType.INSPECT, deps=[t2.task_id], tools=["search_code"])
        t4 = _t("Identify likely fault locations",
                "Narrow down candidates based on evidence.",
                TaskType.ANALYZE, deps=[t3.task_id], complexity=ComplexityLevel.HIGH)
        t5 = _t("Produce hypotheses",
                "Generate ranked list of root-cause hypotheses with evidence.",
                TaskType.ANALYZE, deps=[t4.task_id])
        t6 = _t("Define verification steps",
                "Specify steps to confirm each hypothesis.",
                TaskType.VERIFY, deps=[t5.task_id])
        t7 = _t("Propose fix design",
                "Describe the fix approach without modifying files.",
                TaskType.DESIGN, deps=[t6.task_id], risk=RiskLevel.MEDIUM)
        t8 = _t("Define regression tests",
                "Specify tests to prevent recurrence.",
                TaskType.VERIFY, deps=[t7.task_id])
        return [t1, t2, t3, t4, t5, t6, t7, t8]

    def _refactor_tasks(self, objective: str, has_profile: bool) -> List[PlanningTask]:
        t1 = _t("Inspect current code structure",
                "Read targeted modules and understand current state.",
                TaskType.INSPECT, tools=_read_tools())
        t2 = _t("Identify refactor scope",
                "Determine which files and functions are in scope.",
                TaskType.ANALYZE, deps=[t1.task_id])
        t3 = _t("Evaluate dependency impact",
                "Check what depends on in-scope code.",
                TaskType.ANALYZE, deps=[t2.task_id], complexity=ComplexityLevel.HIGH)
        t4 = _t("Design refactor approach",
                "Specify the new structure without modifying files.",
                TaskType.DESIGN, deps=[t3.task_id], risk=RiskLevel.MEDIUM)
        t5 = _t("Request WRITE permission",
                "Await explicit authorisation before applying changes.",
                TaskType.WAIT_FOR_PERMISSION, deps=[t4.task_id], risk=RiskLevel.HIGH)
        t6 = _t("Define regression tests",
                "Verify equivalent behaviour before and after refactor.",
                TaskType.VERIFY, deps=[t5.task_id])
        return [t1, t2, t3, t4, t5, t6]

    def _review_tasks(self, objective: str, has_profile: bool) -> List[PlanningTask]:
        t1 = _t("Inspect review target",
                "Read files and modules under review.",
                TaskType.INSPECT, tools=_read_tools())
        t2 = _t("Evaluate code quality",
                "Assess correctness, style, and structure.",
                TaskType.ANALYZE, deps=[t1.task_id])
        t3 = _t("Evaluate security implications",
                "Check for potential security issues in the review target.",
                TaskType.ANALYZE, deps=[t1.task_id], risk=RiskLevel.MEDIUM)
        t4 = _t("Evaluate test coverage",
                "Check existing tests against the review target.",
                TaskType.VERIFY, deps=[t2.task_id])
        t5 = _t("Produce review report",
                "Document findings with evidence and severity.",
                TaskType.DOCUMENT, deps=[t3.task_id, t4.task_id])
        return [t1, t2, t3, t4, t5]

    def _document_tasks(self, objective: str, has_profile: bool) -> List[PlanningTask]:
        t1 = _t("Inspect documentation target",
                "Read the module or component to be documented.",
                TaskType.INSPECT, tools=_read_tools())
        t2 = _t("Identify public API surface",
                "Determine exported functions, classes, and routes.",
                TaskType.ANALYZE, deps=[t1.task_id])
        t3 = _t("Draft documentation structure",
                "Propose sections and content without writing files.",
                TaskType.DESIGN, deps=[t2.task_id])
        t4 = _t("Request WRITE permission",
                "Await authorisation before creating documentation files.",
                TaskType.WAIT_FOR_PERMISSION, deps=[t3.task_id])
        t5 = _t("Verify documentation completeness",
                "Check that all public API elements are covered.",
                TaskType.VERIFY, deps=[t4.task_id])
        return [t1, t2, t3, t4, t5]
