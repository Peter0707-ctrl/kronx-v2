from typing import List
from memory.store import MemoryStore

class MemoryManager:
    def __init__(self):
        self.store = MemoryStore()

    def extract_and_save(
        self,
        conversation_id: str,
        user_message: str,
        ai_response: str
    ):
        """
        Analyze conversation and save important memories.
        """
        memories = []

        # Check for important keywords to remember
        important_keywords = [
            # Goals
            "nataka", "I want", "I plan", "ninapanga", "goal", "lengo",
            # Personal info
            "my name", "jina langu", "I am", "mimi ni", "I live", "naishi",
            # Business
            "biashara", "business", "startup", "investment", "uwekezaji",
            # Learning
            "nifundishe", "teach me", "I want to learn", "nataka kujifunza",
            # Money
            "budget", "bajeti", "save", "akiba", "TZS", "shilingi",
        ]

        message_lower = user_message.lower()
        is_important = any(kw.lower() in message_lower for kw in important_keywords)

        if is_important:
            # Save the user message as a memory
            self.store.save_memory(
                conversation_id=conversation_id,
                content=f"User said: {user_message}",
                memory_type="conversation",
                importance=1.5
            )

        # Always save last exchange as short term memory
        self.store.save_memory(
            conversation_id=conversation_id,
            content=f"Q: {user_message[:100]} | A: {ai_response[:100]}",
            memory_type="short_term",
            importance=1.0
        )

        return memories

    def get_context(self, conversation_id: str) -> str:
        """
        Build a memory context string to inject into prompts.
        """
        memories = self.store.get_memories(
            conversation_id=conversation_id,
            limit=5
        )

        if not memories:
            return ""

        context_lines = ["Previous context from this conversation:"]
        for m in memories:
            if m["type"] != "short_term":
                context_lines.append(f"- {m['content']}")

        if len(context_lines) == 1:
            return ""

        return "\n".join(context_lines)

    def get_user_context(self, user_id: str) -> str:
        """
        Get known facts about the user.
        """
        facts = self.store.get_user_facts(user_id)
        if not facts:
            return ""

        lines = ["Known facts about this user:"]
        for f in facts:
            lines.append(f"- {f['content']}")

        return "\n".join(lines)

    def remember_user_fact(self, user_id: str, fact: str):
        """
        Save an important fact about the user.
        """
        self.store.save_user_fact(user_id, fact)

    def clear(self, conversation_id: str):
        self.store.clear_conversation(conversation_id)