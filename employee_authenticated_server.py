import uvicorn

from dotenv import load_dotenv

from employee_rest_mcp_server import mcp
from mcp_auth import MCPAuthMiddleware


load_dotenv()


app = mcp.streamable_http_app()

app.add_middleware(MCPAuthMiddleware)


if __name__ == "__main__":

    uvicorn.run(
        app,
        host="127.0.0.1",
        port=8002,
        log_level="info",
    )