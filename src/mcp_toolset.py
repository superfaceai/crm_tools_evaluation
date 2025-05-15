import asyncio
import json
import os
from contextlib import AsyncExitStack
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from .shared import Tool, Toolset

class MCPToolsetManager:
    def __init__(self):
        self.stack = AsyncExitStack()

    async def create_mcp_toolset(self, *, npm_package: str, name: str, env: dict[str, str] | None):
        await self.stack.__aenter__()  # Manually enter the AsyncExitStack

        server_params = StdioServerParameters(
            command="npx",
            args=[npm_package],
            env=env
        )

        client = await self.stack.enter_async_context(stdio_client(server_params))
        session = await self.stack.enter_async_context(ClientSession(*client))

        # Initialize the connection
        await session.initialize()
        mcp_tools = (await session.list_tools()).tools

        tools = []
        for tool in mcp_tools:
            tool_name = tool.name
            tool_description = tool.description
            tool_parameters = tool.inputSchema

            async def handle_tool_request(args: str, tool_name=tool_name) -> any:
                try:
                    args_dict = json.loads(args)
                    return await session.call_tool(tool_name, args_dict)
                except json.JSONDecodeError:
                    return {"error": "Invalid JSON arguments"}
                except Exception as e:
                    raise e

            tools.append(
                Tool(
                    name=tool_name,
                    description=tool_description,
                    parameters=tool_parameters,
                    handler=handle_tool_request
                )
            )

        return Toolset(
            name=name,
            tools=tools,
        )

    async def close(self):
        await self.stack.__aexit__(None, None, None)  # Manually exit the AsyncExitStack


async def test_mcp():
    manager = MCPToolsetManager()
    try:
        toolset = await manager.create_mcp_toolset(
            npm_package="@hubspot/mcp-server",
            name="HubSpot MCP Toolset",
            env={
                "PRIVATE_APP_ACCESS_TOKEN": os.getenv("HUBSPOT_API_KEY"),
            }
        )
        print("toolset", toolset)

        print("tool", toolset.tools[0])
        print("tool", toolset.tools[0].parameters)

        result = await toolset.tools[0].handler('{}')
        print("result", result)
    finally:
        await manager.close()  # Ensure resources are cleaned up


if __name__ == "__main__":
    asyncio.run(test_mcp())