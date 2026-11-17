import asyncio

from mcp import Client


MCP_SERVER_URL = "http://127.0.0.1:8000/mcp"


async def main():

    print("Connecting to remote MCP server...")

    async with Client(MCP_SERVER_URL) as client:

        print("Connected successfully!")

        # Discover tools
        tools = await client.list_tools()

        print("\nAvailable MCP Tools:")

        for tool in tools.tools:
            print(f"- {tool.name}")

        # Execute tool
        result = await client.call_tool(
            "list_employees",
            {},
        )

        if result.is_error:
            raise RuntimeError(
                f"MCP tool failed: {result.content}"
            )

        print("\nEmployee Records:")
        print(result.structured_content)


if __name__ == "__main__":
    asyncio.run(main())