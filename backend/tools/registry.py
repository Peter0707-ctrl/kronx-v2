from typing import Dict, Any, Callable, List, Optional
from tools.errors import TOOL_NOT_REGISTERED

class ToolDescriptor:
    def __init__(
        self,
        name: str,
        description: str,
        required_permission: str,
        handler: Callable[[Any, Dict[str, Any]], Any]
    ):
        self.name = name
        self.description = description
        self.required_permission = required_permission
        self.handler = handler

class ToolRegistry:
    def __init__(self):
        self._tools: Dict[str, ToolDescriptor] = {}

    def register(self, tool: ToolDescriptor):
        """Register a tool descriptor explicitly."""
        self._tools[tool.name] = tool

    def get(self, tool_name: str) -> Optional[ToolDescriptor]:
        return self._tools.get(tool_name)

    def list_tools(self) -> List[Dict[str, Any]]:
        return [
            {
                "name": t.name,
                "description": t.description,
                "required_permission": t.required_permission
            }
            for t in self._tools.values()
        ]

# Global registry instance
registry = ToolRegistry()
