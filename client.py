import asyncio

from mcp import Client
from mcp.client.stdio import StdioServerParameters


async def main():

    server_params = StdioServerParameters(
        command="uv",
        args=[
            "run",
            "--with",
            "mcp==2.3.0",
            "mcp",
            "run",
            "server.py",
        ],
    )

    print("Starting MCP client...")

    async with Client(server_params) as client:

        print("Connected to MCP Server!")

        tools = await client.list_tools()

        print("\nAvailable tools:")

        for tool in tools.tools:
            print(f"- {tool.name}")

        # 1. Execute MCP Tool
        result = await client.call_tool(
            "add",
            {
                "a": 100,
                "b": 250
            }
        )

        print("\n=== TOOL RESULT ===")
        print(result)


        # 2. Read MCP Resource
        resource = await client.read_resource(
            "tutorial://company-info"
        )

        print("\n=== RESOURCE RESULT ===")
        print(resource)


        # 3. Retrieve MCP Prompt
        prompt = await client.get_prompt(
            "analyze_company",
            {
                "company_name": "ABC Technologies",
                "objective": "Identify Generative AI opportunities"
            }
        )

        print("\n=== PROMPT RESULT ===")
        print(prompt)    


if __name__ == "__main__":
    asyncio.run(main())