"""Main MCP server implementation for NFL data."""

import asyncio
import json

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import TextContent, Tool

from .config import Settings
from .tools import TOOLS, handle_tool_call

# Initialize settings and server
settings = Settings()
app = Server("nfl-data-server")


@app.list_tools()
async def list_tools() -> list[Tool]:
    """Return list of available tools.

    Returns:
        List of Tool objects describing available NFL data queries
    """
    return TOOLS


@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    """Handle tool invocation.

    Args:
        name: Tool name to invoke
        arguments: Tool arguments as dict

    Returns:
        List containing TextContent with JSON response
    """
    try:
        result = await handle_tool_call(name, arguments, settings)
        return [TextContent(type="text", text=result)]
    except Exception as e:
        error_response = {"error": str(e), "tool": name, "arguments": arguments}
        return [TextContent(type="text", text=json.dumps(error_response, indent=2))]


async def main():
    """Run the MCP server via stdio."""
    async with stdio_server() as (read_stream, write_stream):
        await app.run(read_stream, write_stream, app.create_initialization_options())


if __name__ == "__main__":
    asyncio.run(main())
