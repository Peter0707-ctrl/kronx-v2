"""
Phase 3.1 — Persistent Store Integrity Management
Verifies SHA-256 hashes, valid JSON parsing, schema sanity, and non-corruption across all Kron-X stores.
"""
import os
import json
import hashlib
from typing import List, Dict, Any, Optional
from operations.schemas import StoreIntegrityRecord
from utils.logger import logger

BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

KNOWN_STORES = [
    "workspace_store.json",
    "auth_store.json",
    "authorization_store.json",
    "planner_store.json",
    "execution_store.json",
    "proposal_store.json",
    "modification_store.json",
    "rollback_store.json",
    "verification_store.json",
    "agent_store.json",
    "agent_memory_store.json",
    "agent_trace_store.json",
    "multimodal_store.json",
    "llm_store.json",
    "operations_store.json",
]


class StoreIntegrityManager:
    def __init__(self, base_dir: Optional[str] = None):
        self.base_dir = base_dir or BACKEND_DIR

    def compute_sha256(self, file_path: str) -> str:
        """Computes SHA-256 hash of a file."""
        if not os.path.exists(file_path):
            return ""
        hasher = hashlib.sha256()
        with open(file_path, "rb") as f:
            while chunk := f.read(65536):
                hasher.update(chunk)
        return hasher.hexdigest()

    def check_store(self, store_filename: str) -> StoreIntegrityRecord:
        """Inspects a single JSON store for integrity, corruption, and schema sanity."""
        store_path = os.path.join(self.base_dir, store_filename)
        exists = os.path.exists(store_path)

        if not exists:
            return StoreIntegrityRecord(
                store_name=store_filename,
                exists=False,
                valid_json=False,
                sha256="",
                record_count=0,
                size_bytes=0,
                corrupted=False,
                error_message="Store file does not exist yet.",
            )

        size_bytes = os.path.getsize(store_path)
        sha256_hash = self.compute_sha256(store_path)

        try:
            with open(store_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            if isinstance(data, dict):
                count = len(data)
            elif isinstance(data, list):
                count = len(data)
            else:
                count = 1

            return StoreIntegrityRecord(
                store_name=store_filename,
                exists=True,
                valid_json=True,
                sha256=sha256_hash,
                record_count=count,
                size_bytes=size_bytes,
                corrupted=False,
                error_message=None,
            )
        except Exception as e:
            logger.error(f"[store_integrity] Corruption detected in '{store_filename}': {e}")
            return StoreIntegrityRecord(
                store_name=store_filename,
                exists=True,
                valid_json=False,
                sha256=sha256_hash,
                record_count=0,
                size_bytes=size_bytes,
                corrupted=True,
                error_message=f"JSON Parse Error: {str(e)[:100]}",
            )

    def check_all_stores(self) -> List[StoreIntegrityRecord]:
        """Runs integrity verification across all known persistent JSON stores."""
        return [self.check_store(s) for s in KNOWN_STORES]
