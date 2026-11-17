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
            "employee_server.py",
        ],
    )

    print("Starting Employee MCP Client...")

    async with Client(server_params) as client:

        print("Connected to Employee MCP Server!")

        # ---------------------------------
        # 1. Discover Tools
        # ---------------------------------

        tools = await client.list_tools()

        print("\nAvailable MCP Tools:")

        for tool in tools.tools:
            print(f"- {tool.name}")

        # ---------------------------------
        # 2. List Employees
        # ---------------------------------

        result = await client.call_tool(
            "list_employees",
            {},
        )

        print("\n=== INITIAL EMPLOYEES ===")
        print(result.structured_content)

        # ---------------------------------
        # 3. Create Employee
        # ---------------------------------

        result = await client.call_tool(
            "create_employee",
            {
                "employee_id": 103,
                "name": "Amit",
                "department": "Data Science",
                "salary": 180000,
            },
        )

        print("\n=== CREATE EMPLOYEE ===")
        print(result.structured_content)

        # ---------------------------------
        # 4. Get Employee
        # ---------------------------------

        result = await client.call_tool(
            "get_employee",
            {
                "employee_id": 103,
            },
        )

        print("\n=== GET EMPLOYEE ===")
        print(result.structured_content)

        # ---------------------------------
        # 5. Update Employee
        # ---------------------------------

        result = await client.call_tool(
            "update_employee",
            {
                "employee_id": 103,
                "salary": 200000,
            },
        )

        print("\n=== UPDATE EMPLOYEE ===")
        print(result.structured_content)

        # ---------------------------------
        # 6. Verify Update
        # ---------------------------------

        result = await client.call_tool(
            "get_employee",
            {
                "employee_id": 103,
            },
        )

        print("\n=== VERIFY UPDATED EMPLOYEE ===")
        print(result.structured_content)

        # ---------------------------------
        # 7. Delete Employee
        # ---------------------------------

        result = await client.call_tool(
            "delete_employee",
            {
                "employee_id": 103,
            },
        )

        print("\n=== DELETE EMPLOYEE ===")
        print(result.structured_content)

        # ---------------------------------
        # 8. Verify Deletion
        # ---------------------------------

        result = await client.call_tool(
            "get_employee",
            {
                "employee_id": 103,
            },
        )

        print("\n=== VERIFY DELETION ===")
        print(result.structured_content)


if __name__ == "__main__":
    asyncio.run(main())