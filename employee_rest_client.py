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
            "employee_rest_mcp_server.py",
        ],
    )

    print("Starting MCP REST Client...")

    async with Client(server_params) as client:

        print("Connected to MCP Server!")

        # Discover tools
        tools = await client.list_tools()

        print("\nAvailable Tools:")
        for tool in tools.tools:
            print(f"- {tool.name}")

        async def execute_tool(name, arguments):
            print(f"\nExecuting: {name}")

            result = await client.call_tool(
                name,
                arguments,
            )

            if result.is_error:
                raise RuntimeError(
                    f"MCP tool {name} failed: {result.content}"
                )

            print("Result:", result.structured_content)
            return result.structured_content

        # 1. CREATE
        await execute_tool(
            "create_employee",
            {
                "employee_id": 104,
                "name": "Karan",
                "department": "Data Science",
                "salary": 180000,
            },
        )

        # 2. READ
        await execute_tool(
            "get_employee",
            {"employee_id": 104},
        )

        # 3. UPDATE
        await execute_tool(
            "update_employee",
            {
                "employee_id": 104,
                "name": "Karan",
                "department": "Data Science",
                "salary": 220000,
            },
        )

        # 4. VERIFY UPDATE
        updated = await execute_tool(
            "get_employee",
            {"employee_id": 104},
        )

        assert updated["salary"] == 220000

        # 5. DELETE
        await execute_tool(
            "delete_employee",
            {"employee_id": 104},
        )

        # 6. VERIFY DELETION
        result = await client.call_tool(
            "get_employee",
            {"employee_id": 104},
        )

        if result.is_error:
            print("\nDeletion verified: employee no longer exists.")
        else:
            raise AssertionError(
                "Employee still exists after deletion"
            )

        print("\nAll MCP REST CRUD tests passed!")


if __name__ == "__main__":
    asyncio.run(main())