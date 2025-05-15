import asyncio
import json
import os
from contextlib import AsyncExitStack
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from typing import Optional
from .shared import Tool, Toolset


class MCPToolset(Toolset):
    def __init__(self, *, name: str, npm_package: str, env: dict[str, str] | None):
        self.name = name
        self.env = env
        self.npm_package = npm_package

        self.session: Optional[ClientSession] = None
        self.exit_stack = AsyncExitStack()

        super().__init__(name=name, tools=[])

    async def connect(self):
        server_params = StdioServerParameters(
            command="npx",
            args=[self.npm_package],
            env=self.env
        )

        stdio_transport = await self.exit_stack.enter_async_context(stdio_client(server_params))
        self.stdio, self.write = stdio_transport
        self.session = await self.exit_stack.enter_async_context(ClientSession(self.stdio, self.write))

        await self.session.initialize()

        response = await self.session.list_tools()

        self.tools = []
        for tool in response.tools:
            if tool.name == "hubspot-search-objects":
                continue

            tool_name = tool.name
            tool_description = tool.description
            tool_parameters = tool.inputSchema

            async def handle_tool_request(args: str, tool_name=tool_name) -> any:
                try:
                    args_dict = json.loads(args)
                    result = await self.session.call_tool(tool_name, args_dict)
                    return result.model_dump_json()
                except json.JSONDecodeError:
                    return {"error": "Invalid JSON arguments"}
                except Exception as e:
                    raise e

            self.tools.append(
                Tool(
                    name=tool_name,
                    description=tool_description,
                    parameters=tool_parameters,
                    handler=handle_tool_request
                )
            )

    async def close(self):
        await self.exit_stack.aclose()


async def test_mcp():
    toolset = MCPToolset(
        name="HubSpot MCP Toolset",
        npm_package="@hubspot/mcp-server",
        env={
            "PRIVATE_APP_ACCESS_TOKEN": os.getenv("HUBSPOT_API_KEY"),
        }
    )
    try:
        await toolset.connect()
        print("Connected to MCP Toolset")

        tool = toolset.tools[0]
        result = await tool.run('{}')

        print(f"Tool result: {result}")
    finally:
        await toolset.close()


if __name__ == "__main__":
    asyncio.run(test_mcp())