import sys

from contextlib import AsyncExitStack
from pathlib import Path
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


class MCPClient:
    """
    Client used by FastAPI to communicate with the MCP server.
    """

    def __init__(self):
        self.session: ClientSession | None = None
        self.exit_stack = AsyncExitStack()

    async def connect(self):
        """
        Start the MCP server and establish a connection.
        """

        server_path = Path(
            "app/server/server.py",
        ).resolve()

        if not server_path.exists():
            raise FileNotFoundError(f"MCP server not found: {server_path}")

        server_params = StdioServerParameters(
            command=sys.executable,
            args=[str(server_path)],
        )

        # Start the MCP server process
        stdio_transport = await self.exit_stack.enter_async_context(
            stdio_client(server_params)
        )

        read, write = stdio_transport

        self.session = await self.exit_stack.enter_async_context(
            ClientSession(read, write)
        )

        await self.session.initialize()
        
        response = await self.session.list_tools()

        print("Connected to MCP server.")

    async def list_tools(self):
        """
        Return all tools exposed by the MCP server.
        """

        if self.session is None:
            raise RuntimeError("MCP client is not connected.")

        response = await self.session.list_tools()

        return response.tools

    async def call_tool(
        self,
        tool_name: str,
        arguments: dict | None = None,
    ):
        """
        Call a tool on the MCP server.
        """

        if self.session is None:
            raise RuntimeError("MCP client is not connected.")

        result = await self.session.call_tool(
            tool_name,
            arguments=arguments or {},
        )

        return result

    async def close(self):
        """
        Close the MCP connection and server process.
        """

        await self.exit_stack.aclose()
