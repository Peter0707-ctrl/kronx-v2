"""
Phase 2I — Agent Orchestration & Lifecycle Engine
Manages agent execution instances, store persistence, cancellation, status retrieval, and trace queries.
Thread-safe, atomic, and strictly isolated per tenant.
"""
from __future__ import annotations
import json
import os
import shutil
import tempfile
import threading
import uuid
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any

from agent.schemas import AgentRequest, AgentResult, AgentStatus, DecisionTrace
from agent.errors import AgentError, AGENT_NOT_FOUND, AGENT_CANCELLED
from agent.agent import KronxAgent
from auth.schemas import AuthenticationContext
from utils.logger import logger

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
AGENT_STORE_FILE = os.path.join(BASE_DIR, "agent_store.json")

_orchestrator_lock = threading.RLock()
MAX_AGENT_RECORDS = 500


class AgentOrchestrator:
    """Coordinates agent execution requests and persistent state tracking."""

    def __init__(self, store_path: Optional[str] = None, agent: Optional[KronxAgent] = None):
        self.path = store_path or AGENT_STORE_FILE
        self._agent = agent or KronxAgent()
        self._cache: Optional[dict] = None
        self._cache_mtime: float = 0
        self._ensure_file()

    def _ensure_file(self):
        with _orchestrator_lock:
            if not os.path.exists(self.path):
                try:
                    with open(self.path, "w", encoding="utf-8") as f:
                        json.dump({}, f)
                    try:
                        self._cache_mtime = os.path.getmtime(self.path)
                    except Exception:
                        self._cache_mtime = 0
                except Exception as e:
                    logger.error(f"[agent_orchestrator] Failed to create {self.path}: {e}")

    def _load_under_lock(self) -> dict:
        if self._cache is not None and os.path.exists(self.path):
            try:
                mtime = os.path.getmtime(self.path)
                if mtime > self._cache_mtime:
                    self._cache = None
            except Exception:
                pass

        if self._cache is not None:
            return json.loads(json.dumps(self._cache))

        if not os.path.exists(self.path):
            self._cache = {}
            self._cache_mtime = 0
            return self._cache

        try:
            with open(self.path, "r", encoding="utf-8") as f:
                self._cache = json.load(f)
            try:
                self._cache_mtime = os.path.getmtime(self.path)
            except Exception:
                self._cache_mtime = 0
        except json.JSONDecodeError as jde:
            logger.error(f"[agent_orchestrator] Corrupted JSON in {self.path}: {jde}")
            corrupt_backup = f"{self.path}.corrupt.{int(datetime.now().timestamp())}"
            try:
                shutil.copy2(self.path, corrupt_backup)
            except Exception:
                pass
            self._cache = {}
            self._cache_mtime = 0
            try:
                with open(self.path, "w", encoding="utf-8") as f:
                    json.dump(self._cache, f)
            except Exception:
                pass
        except Exception as e:
            logger.error(f"[agent_orchestrator] Failed to load {self.path}: {e}")
            self._cache = {}
            self._cache_mtime = 0

        return json.loads(json.dumps(self._cache))

    def _save_under_lock(self, data: dict):
        self._cache = json.loads(json.dumps(data))
        dir_name = os.path.dirname(self.path)
        temp_fd, temp_path = tempfile.mkstemp(
            dir=dir_name, prefix="agent_store_tmp_", suffix=".json"
        )
        try:
            with os.fdopen(temp_fd, "w", encoding="utf-8") as f:
                json.dump(self._cache, f, indent=2, default=str)
                f.flush()
                try:
                    os.fsync(temp_fd)
                except Exception:
                    pass
            os.replace(temp_path, self.path)
            try:
                self._cache_mtime = os.path.getmtime(self.path)
            except Exception:
                self._cache_mtime = 0
        except Exception as e:
            logger.error(f"[agent_orchestrator] Atomic save failed: {e}")
            if os.path.exists(temp_path):
                try:
                    os.remove(temp_path)
                except Exception:
                    pass

    def run_agent_job(
        self,
        auth_context: AuthenticationContext,
        request: AgentRequest,
        has_write_authorization: bool = False,
    ) -> AgentResult:
        """Processes an agent request and saves the result in persistent storage."""
        result = self._agent.process_request(
            auth_context=auth_context,
            request=request,
            has_write_authorization=has_write_authorization,
        )

        with _orchestrator_lock:
            data = self._load_under_lock()
            tenant_records = data.get(auth_context.tenant_id, {})
            tenant_records[result.agent_id] = result.model_dump()

            if len(tenant_records) > MAX_AGENT_RECORDS:
                sorted_keys = sorted(
                    tenant_records.keys(),
                    key=lambda k: tenant_records[k].get("created_at", "")
                )
                for old_k in sorted_keys[:len(tenant_records) - MAX_AGENT_RECORDS]:
                    del tenant_records[old_k]

            data[auth_context.tenant_id] = tenant_records
            self._save_under_lock(data)

        return result

    def get_agent_result(self, tenant_id: str, agent_id: str) -> AgentResult:
        with _orchestrator_lock:
            data = self._load_under_lock()
            item = data.get(tenant_id, {}).get(agent_id)
            if not item:
                raise AgentError(AGENT_NOT_FOUND, f"Agent record '{agent_id}' not found.", status_code=404)
            return AgentResult(**item)

    def cancel_agent_job(self, tenant_id: str, agent_id: str) -> AgentResult:
        with _orchestrator_lock:
            data = self._load_under_lock()
            tenant_records = data.get(tenant_id, {})
            item = tenant_records.get(agent_id)
            if not item:
                raise AgentError(AGENT_NOT_FOUND, f"Agent record '{agent_id}' not found.", status_code=404)

            item["status"] = AgentStatus.CANCELLED.value
            item["summary"] = "Job cancelled cooperatively by user request."
            tenant_records[agent_id] = item
            data[tenant_id] = tenant_records
            self._save_under_lock(data)
            return AgentResult(**item)

    def get_agent_traces(self, tenant_id: str) -> List[Dict[str, Any]]:
        return self._agent._trace_store.get_traces_by_tenant(tenant_id)
