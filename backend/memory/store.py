import json
import os
import threading
import shutil
import tempfile
from datetime import datetime
from typing import List, Optional
from utils.logger import logger

MEMORY_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), "memory_store.json")

# Global thread lock for serialize read/write filesystem access
_file_lock = threading.Lock()

class MemoryStore:
    def __init__(self):
        self.path = MEMORY_FILE
        self._cache: Optional[dict] = None
        self._ensure_file()

    def _ensure_file(self):
        with _file_lock:
            if not os.path.exists(self.path):
                try:
                    with open(self.path, "w", encoding="utf-8") as f:
                        json.dump({}, f)
                except Exception as e:
                    logger.error(f"Failed to create memory store file: {e}", exc_info=True)

    def _load(self) -> dict:
        if self._cache is not None:
            return self._cache

        with _file_lock:
            if not os.path.exists(self.path):
                self._cache = {}
                return self._cache

            try:
                with open(self.path, "r", encoding="utf-8") as f:
                    self._cache = json.load(f)
            except json.JSONDecodeError as jde:
                logger.error(f"Memory store JSON corrupted: {jde}", exc_info=True)
                # Recover safely: copy corrupted file to a backup diagnosis path
                corrupt_backup = f"{self.path}.corrupt.{int(datetime.now().timestamp())}"
                try:
                    if os.path.exists(self.path):
                        shutil.copy2(self.path, corrupt_backup)
                        logger.warning(f"Saved corrupted memory file to {corrupt_backup}")
                except Exception as backup_err:
                    logger.error(f"Failed to backup corrupted file: {backup_err}", exc_info=True)
                
                # Recover safely with empty dictionary
                self._cache = {}
                try:
                    with open(self.path, "w", encoding="utf-8") as f:
                        json.dump({}, f)
                except Exception as write_err:
                    logger.error(f"Failed to write fresh file during recovery: {write_err}", exc_info=True)
            except Exception as e:
                logger.error(f"Failed to load memory store: {e}", exc_info=True)
                self._cache = {}

        return self._cache

    def _save(self, data: dict):
        self._cache = data
        dir_name = os.path.dirname(self.path)
        with _file_lock:
            # Create a temp file in the same folder to guarantee atomic rename capability
            temp_fd, temp_path = tempfile.mkstemp(dir=dir_name, prefix="memory_store_tmp_", suffix=".json")
            try:
                with os.fdopen(temp_fd, "w", encoding="utf-8") as f:
                    json.dump(data, f, indent=2, default=str)
                    f.flush()
                    try:
                        os.fsync(temp_fd)
                    except Exception:
                        pass
                # Atomic swap file replace
                os.replace(temp_path, self.path)
            except Exception as e:
                logger.error(f"Failed to save memory store atomically: {e}", exc_info=True)
                if os.path.exists(temp_path):
                    try:
                        os.remove(temp_path)
                    except Exception:
                        pass

    def save_memory(
        self,
        conversation_id: str,
        content: str,
        memory_type: str = "general",
        importance: float = 1.0
    ):
        data = self._load()

        if conversation_id not in data:
            data[conversation_id] = []

        memory = {
            "id": f"{conversation_id}_{len(data[conversation_id])}",
            "content": content,
            "type": memory_type,
            "importance": importance,
            "created_at": datetime.now().isoformat()
        }

        data[conversation_id].append(memory)

        # Prune conversation memories if count exceeds 40 to preserve low RAM & disk usage
        if len(data[conversation_id]) > 40:
            # Keep highest importance and most recent memories
            sorted_memories = sorted(data[conversation_id], key=lambda x: (x.get("importance", 1.0), x.get("created_at", "")), reverse=True)
            data[conversation_id] = sorted_memories[:30]

        self._save(data)
        return memory

    def get_memories(
        self,
        conversation_id: str,
        limit: int = 10
    ) -> List[dict]:
        data = self._load()
        memories = data.get(conversation_id, [])
        memories.sort(key=lambda x: x.get("importance", 1.0), reverse=True)
        return memories[:limit]

    def get_all_memories(self, conversation_id: str) -> List[dict]:
        data = self._load()
        return data.get(conversation_id, [])

    def delete_memory(self, conversation_id: str, memory_id: str):
        data = self._load()
        if conversation_id in data:
            data[conversation_id] = [
                m for m in data[conversation_id]
                if m.get("id") != memory_id
            ]
            self._save(data)

    def clear_conversation(self, conversation_id: str):
        data = self._load()
        if conversation_id in data:
            del data[conversation_id]
            self._save(data)

    def save_user_fact(self, user_id: str, fact: str, importance: float = 2.0):
        """Save important facts about the user permanently."""
        return self.save_memory(
            conversation_id=f"user_{user_id}",
            content=fact,
            memory_type="user_fact",
            importance=importance
        )

    def get_user_facts(self, user_id: str) -> List[dict]:
        """Get all known facts about a user."""
        return self.get_all_memories(f"user_{user_id}")