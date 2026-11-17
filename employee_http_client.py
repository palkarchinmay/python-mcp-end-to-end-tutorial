import uuid
import asyncio
import os

import httpx2

from dotenv import load_dotenv
from mcp import Client
from mcp.client.streamable_http import streamable_http_client


load_dotenv()

MCP_SERVER_URL = "http://127.0.0.1:8002/mcp"

MCP_ROLE = os.getenv("MCP_ROLE", "read")

if MCP_ROLE == "read":
    MCP_TOKEN = os.getenv("MCP_READ_TOKEN")
elif MCP_ROLE == "write":
    MCP_TOKEN = os.getenv("MCP_WRITE_TOKEN")
else:
    raise ValueError("MCP_ROLE must be 'read' or 'write'")


async def main():

    if not MCP_TOKEN:
        raise RuntimeError(
            "MCP_TOKEN is missing from .env"
        )

    print("Connecting to MCP server with Bearer token...")

    correlation_id = str(uuid.uuid4())
    print(f"\nCorrelation ID: {correlation_id}")

    async with httpx2.AsyncClient(
        headers={
            "Authorization": f"Bearer {MCP_TOKEN}",
            "X-Correlation-ID": correlation_id,
        },
        timeout=httpx2.Timeout(
            30.0,
            read=300.0
        ),
    ) as http_client:

        transport = streamable_http_client(
            MCP_SERVER_URL,
            http_client=http_client
        )

        async with Client(transport) as client:

            print("Connected successfully!")

            tools = await client.list_tools()

            print("\nAvailable MCP Tools:")

            for tool in tools.tools:
                print(f"- {tool.name}")

            result = await client.call_tool(
                "list_employees",
                {}
            )

            if result.is_error:
                raise RuntimeError(
                    f"MCP tool failed: {result.content}"
                )

            print("\nEmployee Records:")
            print(result.structured_content)

            if MCP_ROLE == "write":
                print("\n=== TEST: READ-WRITE USER CREATES EMPLOYEE ===")

                result = await client.call_tool(
                    "create_employee",
                    {
                        "employee_id": 99999,
                        "name": "Test Employee",
                        "department": "Data Science",
                        "salary": 150000,
                    },
                )

                if result.is_error:
                    raise RuntimeError(
                        f"Create employee failed: {result.content}"
                    )

                print("Create Result:")
                print(result.structured_content)

                print("\n=== VERIFY EMPLOYEE CREATED ===")

                result = await client.call_tool(
                    "get_employee",
                    {
                        "employee_id": 99999,
                    },
                )

                if result.is_error:
                    raise RuntimeError(
                        f"Get employee failed: {result.content}"
                    )

                print("Employee:")
                print(result.structured_content)

                print("\n=== CLEANUP: DELETE TEST EMPLOYEE ===")

                result = await client.call_tool(
                    "delete_employee",
                    {
                        "employee_id": 99999,
                    },
                )

                if result.is_error:
                    raise RuntimeError(
                        f"Delete employee failed: {result.content}"
                    )

                print("Delete Result:")
                print(result.structured_content)

                print("\nREAD-WRITE AUTHORIZATION TEST PASSED")


if __name__ == "__main__":
    asyncio.run(main())