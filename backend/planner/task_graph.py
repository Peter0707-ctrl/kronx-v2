"""
Phase 2C — Task Graph Engine
Dependency-aware graph construction with cycle detection, duplicate detection,
and impossible-dependency detection.  Never executes tasks — purely structural.
"""
from __future__ import annotations
from typing import Dict, List, Optional, Set, Tuple

from planner.schemas import PlanningTask, MAX_TASKS, MAX_DEPENDENCIES_PER_TASK


class PlanningGraphError(Exception):
    """Raised for structural graph violations (cycle, missing dep, duplicate)."""
    def __init__(self, code: str, detail: str):
        super().__init__(detail)
        self.code = code
        self.detail = detail


class TaskGraph:
    """
    Builds and validates a directed acyclic task graph.
    All validation errors are raised as PlanningGraphError (never hung).
    """

    def __init__(self, tasks: List[PlanningTask]):
        self._validate_count(tasks)
        self._tasks: Dict[str, PlanningTask] = {}
        self._build(tasks)

    # ------------------------------------------------------------------
    # Public helpers
    # ------------------------------------------------------------------

    @property
    def task_ids(self) -> List[str]:
        return list(self._tasks.keys())

    def get_execution_order(self) -> List[str]:
        """Topological sort — raises PlanningGraphError if a cycle exists."""
        return self._topological_sort()

    def dependency_graph(self) -> Dict[str, List[str]]:
        return {tid: list(t.dependencies) for tid, t in self._tasks.items()}

    # ------------------------------------------------------------------
    # Internal build + validation
    # ------------------------------------------------------------------

    def _validate_count(self, tasks: List[PlanningTask]):
        if len(tasks) > MAX_TASKS:
            raise PlanningGraphError(
                "RESOURCE_LIMIT",
                f"Plan has {len(tasks)} tasks which exceeds the limit of {MAX_TASKS}."
            )

    def _build(self, tasks: List[PlanningTask]):
        seen_ids: Set[str] = set()
        for task in tasks:
            if task.task_id in seen_ids:
                raise PlanningGraphError(
                    "DUPLICATE_TASK_ID",
                    f"Duplicate task_id detected: '{task.task_id}'."
                )
            seen_ids.add(task.task_id)
            self._tasks[task.task_id] = task

        # Check self-dependency and excessive deps
        for task in tasks:
            if task.task_id in task.dependencies:
                raise PlanningGraphError(
                    "SELF_DEPENDENCY",
                    f"Task '{task.task_id}' depends on itself."
                )
            if len(task.dependencies) > MAX_DEPENDENCIES_PER_TASK:
                raise PlanningGraphError(
                    "TOO_MANY_DEPENDENCIES",
                    f"Task '{task.task_id}' has {len(task.dependencies)} dependencies (max {MAX_DEPENDENCIES_PER_TASK})."
                )
            # Validate all dependencies reference existing tasks
            for dep in task.dependencies:
                if dep not in self._tasks:
                    raise PlanningGraphError(
                        "MISSING_DEPENDENCY",
                        f"Task '{task.task_id}' references unknown dependency '{dep}'."
                    )

        # Cycle detection via DFS
        self._detect_cycles()

    def _detect_cycles(self):
        """DFS-based cycle detection.  Raises PlanningGraphError on first cycle found."""
        WHITE, GRAY, BLACK = 0, 1, 2
        color: Dict[str, int] = {tid: WHITE for tid in self._tasks}
        path: List[str] = []

        def dfs(node: str):
            color[node] = GRAY
            path.append(node)
            for dep in self._tasks[node].dependencies:
                if color[dep] == GRAY:
                    cycle_start = path.index(dep)
                    cycle = " → ".join(path[cycle_start:]) + f" → {dep}"
                    raise PlanningGraphError(
                        "CIRCULAR_DEPENDENCY",
                        f"Circular dependency detected: {cycle}"
                    )
                if color[dep] == WHITE:
                    dfs(dep)
            path.pop()
            color[node] = BLACK

        for tid in self._tasks:
            if color[tid] == WHITE:
                dfs(tid)

    def _topological_sort(self) -> List[str]:
        """Kahn's algorithm for topological sort."""
        in_degree: Dict[str, int] = {tid: 0 for tid in self._tasks}
        for task in self._tasks.values():
            for dep in task.dependencies:
                in_degree[task.task_id] = in_degree.get(task.task_id, 0) + 1

        queue = [tid for tid, deg in in_degree.items() if deg == 0]
        result: List[str] = []

        # Adjacency: dep → [tasks that depend on dep]
        adjacency: Dict[str, List[str]] = {tid: [] for tid in self._tasks}
        for task in self._tasks.values():
            for dep in task.dependencies:
                adjacency[dep].append(task.task_id)

        while queue:
            node = queue.pop(0)
            result.append(node)
            for dependent in adjacency[node]:
                in_degree[dependent] -= 1
                if in_degree[dependent] == 0:
                    queue.append(dependent)

        if len(result) != len(self._tasks):
            raise PlanningGraphError(
                "CIRCULAR_DEPENDENCY",
                "Graph contains a cycle that prevents topological ordering."
            )
        return result
