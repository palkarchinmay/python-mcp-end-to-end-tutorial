# Python MCP Tutorial

End-to-end implementation of Model Context Protocol using Python.

## Features

- MCP Tools, Resources and Prompts
- MCP Client and Server
- Employee CRUD Operations
- FastAPI REST Integration
- STDIO Transport
- Streamable HTTP Transport
- Bearer Token Authentication
- Role-Based Authorization
- Correlation ID Propagation
- Structured Audit Logging
- Execution Latency Monitoring

## Technology Stack

- Python
- MCP Python SDK
- FastAPI
- HTTPX
- Pydantic
- Uvicorn

## Setup

1. Create Python virtual environment.
2. Install dependencies from requirements.txt.
3. Configure .env using .env.example.
4. Start FastAPI on port 8001.
5. Start authenticated MCP server on port 8002.
6. Execute employee_http_client.py.

## FastAPI

uvicorn employee_api:app --host 127.0.0.1 --port 8001

## MCP Server

python employee_authenticated_server.py

## MCP Client

python employee_http_client.py
