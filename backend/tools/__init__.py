from tools.registry import registry, ToolDescriptor
from tools.filesystem.read_file import read_file_handler
from tools.filesystem.list_directory import list_directory_handler
from tools.filesystem.search_code import search_code_handler
from tools.filesystem.inspect_file import inspect_file_handler

# Register READ tools
registry.register(ToolDescriptor(
    name="read_file",
    description="Read content of a source file safely inside workspace boundaries.",
    required_permission="READ",
    handler=read_file_handler
))

registry.register(ToolDescriptor(
    name="list_directory",
    description="List file metadata details in directory path inside workspace.",
    required_permission="READ",
    handler=list_directory_handler
))

registry.register(ToolDescriptor(
    name="search_code",
    description="Search source code files in workspace for literal query substring.",
    required_permission="READ",
    handler=search_code_handler
))

registry.register(ToolDescriptor(
    name="inspect_file",
    description="Inspect path metadata category, size, language, and line count.",
    required_permission="READ",
    handler=inspect_file_handler
))

# Register disabled WRITE interfaces (structured but disabled in 2B)
def disabled_write_handler(context, arguments):
    # Strictly raise permission denied if execution is attempted
    raise ValueError("PERMISSION_DENIED")

registry.register(ToolDescriptor(
    name="create_file",
    description="Create a new file with content inside workspace (requires WRITE authorization).",
    required_permission="WRITE",
    handler=disabled_write_handler
))

registry.register(ToolDescriptor(
    name="edit_file",
    description="Modify block range in file (requires WRITE authorization).",
    required_permission="WRITE",
    handler=disabled_write_handler
))
