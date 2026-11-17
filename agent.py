import asyncio
import json
import os
import sys

from dotenv import load_dotenv
from openai import AsyncOpenAI

from mcp import Client
from mcp.client.stdio import StdioServerParameters


load_dotenv()

MODEL = os.getenv("OPENAI_MODEL", "gpt-4.1-mini")


async def main():

    if not os.getenv("OPENAI_API_KEY"):
        raise RuntimeError("OPENAI_API_KEY is missing from .env")

    openai_client = AsyncOpenAI()

    # Start our existing MCP server
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

    print("Starting MCP Agent...")

    async with Client(server_params) as mcp_client:

        print("Connected to MCP Server!")

        # Discover available MCP tools
        tools_result = await mcp_client.list_tools()

        print("\nAvailable MCP Tools:")

        for tool in tools_result.tools:
            print(f"- {tool.name}")

        # Convert MCP tool schemas into OpenAI function schemas
        openai_tools = []

        for tool in tools_result.tools:

            openai_tools.append(
                {
                    "type": "function",
                    "name": tool.name,
                    "description": tool.description or "",
                    "parameters": tool.input_schema,
                }
            )

        user_question = "What is 125 + 375?"

        print(f"\nUser: {user_question}")

        # Ask OpenAI to decide whether to call a tool
        response = await openai_client.responses.create(
            model=MODEL,
            instructions=(
                "You are a helpful assistant. "
                "Use available MCP tools for arithmetic. "
                "Do not invent tool results."
            ),
            input=user_question,
            tools=openai_tools,
        )

        print(f"\nResponse type: {type(response)}")
        print(f"Response preview: {repr(response)[:1000]}")

        conversation = [
            {
                "role": "user",
                "content": user_question,
            }
        ]

        # Execute tool calls until OpenAI produces a final answer
        for _ in range(5):

            conversation.extend(
                item.model_dump(exclude_none=True)
                for item in response.output
            )

            function_calls = [
                item
                for item in response.output
                if item.type == "function_call"
            ]

            if not function_calls:
                print("\nFinal Answer:")
                print(response.output_text)
                return

            for tool_call in function_calls:

                print(f"\nOpenAI selected tool: {tool_call.name}")

                arguments = json.loads(tool_call.arguments)

                print(f"Arguments: {arguments}")

                # Execute selected MCP tool
                result = await mcp_client.call_tool(
                    tool_call.name,
                    arguments,
                )

                print(f"MCP Result: {result.structured_content}")

                if result.is_error:
                    tool_output = {
                        "error": [
                            item.text
                            for item in result.content
                            if item.type == "text"
                        ]
                    }
                elif result.structured_content is not None:
                    tool_output = result.structured_content
                else:
                    tool_output = [
                        item.text
                        for item in result.content
                        if item.type == "text"
                    ]

                conversation.append(
                    {
                        "type": "function_call_output",
                        "call_id": tool_call.call_id,
                        "output": json.dumps(tool_output),
                    }
                )

            # Send tool results back to OpenAI
            response = await openai_client.responses.create(
                model=MODEL,
                instructions=(
                    "You are a helpful assistant. "
                    "Use available MCP tools for arithmetic. "
                    "Do not invent tool results."
                ),
                input=conversation,
                tools=openai_tools,
            )

        raise RuntimeError("Maximum tool-calling iterations reached")


if __name__ == "__main__":
    asyncio.run(main())