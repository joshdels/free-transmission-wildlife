import asyncio

from app.ai.mcp_client import MCPClient


async def main():
    mcp = MCPClient()

    try:
        await mcp.connect()

        tools = await mcp.list_tools()

        for tool in tools:
            print(tool.name)

        result = await mcp.call_tool("get_summary_transmission_lines")

        print("RESULT:")
        print(result)

    finally:
        await mcp.close()


asyncio.run(main())
