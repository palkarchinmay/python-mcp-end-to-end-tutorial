import json
import os
import secrets
import uuid
import logging

from dotenv import load_dotenv
from starlette.datastructures import Headers

from request_context import correlation_id_var, role_var
from audit_logger import audit_event


# ============================================================
# 1. Configuration
# ============================================================

load_dotenv()

logger = logging.getLogger("mcp-auth")


READ_TOOLS = {
    "list_employees",
    "get_employee",
}

WRITE_TOOLS = {
    "create_employee",
    "update_employee",
    "delete_employee",
}

ALL_TOOLS = READ_TOOLS | WRITE_TOOLS

MAX_REQUEST_BYTES = 1024 * 1024


# ============================================================
# 2. MCP Authentication and Authorization Middleware
# ============================================================

class MCPAuthMiddleware:

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):

        # ----------------------------------------------------
        # 2.1 Handle non-HTTP ASGI events
        # ----------------------------------------------------

        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        # ----------------------------------------------------
        # 2.2 Extract correlation ID
        # ----------------------------------------------------

        headers = Headers(scope=scope)

        incoming_id = headers.get("x-correlation-id")

        try:
            correlation_id = (
                str(uuid.UUID(incoming_id))
                if incoming_id
                else str(uuid.uuid4())
            )

        except (ValueError, AttributeError):
            correlation_id = str(uuid.uuid4())

        # Set request-specific correlation context
        context_token = correlation_id_var.set(correlation_id)

        try:

            logger.info(
                "MCP request received | correlation_id=%s | method=%s",
                correlation_id,
                scope.get("method"),
            )

            # ------------------------------------------------
            # 2.3 Read authentication configuration
            # ------------------------------------------------

            read_token = os.getenv("MCP_READ_TOKEN")
            write_token = os.getenv("MCP_WRITE_TOKEN")

            if (
                not read_token
                or not write_token
                or read_token == write_token
            ):

                logger.error(
                    "MCP authentication configuration error"
                )

                await self.reject(
                    send,
                    500,
                    "Authentication configuration error",
                )

                return

            # ------------------------------------------------
            # 2.4 Extract Bearer token
            # ------------------------------------------------

            authorization = headers.get(
                "authorization",
                "",
            )

            scheme, separator, supplied_token = (
                authorization.partition(" ")
            )

            if (
                not separator
                or scheme.lower() != "bearer"
                or not supplied_token
            ):

                audit_event(
                    event="mcp_authentication",
                    correlation_id=correlation_id,
                    status="denied",
                    error_type="MissingOrInvalidBearerToken",
                )

                await self.reject(
                    send,
                    401,
                    "Unauthorized",
                )

                return

            # ------------------------------------------------
            # 2.5 Authenticate and resolve role
            # ------------------------------------------------

            if secrets.compare_digest(
                supplied_token,
                read_token,
            ):
                role = "read"

            elif secrets.compare_digest(
                supplied_token,
                write_token,
            ):
                role = "write"

            else:

                audit_event(
                    event="mcp_authentication",
                    correlation_id=correlation_id,
                    status="denied",
                    error_type="InvalidToken",
                )

                await self.reject(
                    send,
                    401,
                    "Unauthorized",
                )

                return

            # Store authenticated role in request context
            role_token = role_var.set(role)

            try:

                # --------------------------------------------
                # 2.6 Handle non-POST MCP HTTP requests
                # --------------------------------------------

                if scope["method"] != "POST":

                    await self.app(
                        scope,
                        receive,
                        send,
                    )

                    return

                # --------------------------------------------
                # 2.7 Read request body
                # --------------------------------------------

                body = bytearray()

                while True:

                    message = await receive()

                    if message["type"] == "http.disconnect":
                        return

                    if message["type"] != "http.request":
                        continue

                    body.extend(
                        message.get("body", b"")
                    )

                    if len(body) > MAX_REQUEST_BYTES:

                        await self.reject(
                            send,
                            413,
                            "Request too large",
                        )

                        return

                    if not message.get(
                        "more_body",
                        False,
                    ):
                        break

                # --------------------------------------------
                # 2.8 Parse JSON-RPC request
                # --------------------------------------------

                try:
                    request_data = json.loads(body)

                except (
                    json.JSONDecodeError,
                    UnicodeDecodeError,
                ):

                    await self.reject(
                        send,
                        400,
                        "Invalid JSON",
                    )

                    return

                # This tutorial supports individual JSON-RPC
                # request objects, not batches.

                if not isinstance(request_data, dict):

                    await self.reject(
                        send,
                        400,
                        "Invalid JSON-RPC request",
                    )

                    return

                method = request_data.get("method")

                # --------------------------------------------
                # 2.9 Tool-level RBAC
                # --------------------------------------------

                if method == "tools/call":

                    params = request_data.get(
                        "params",
                        {},
                    )

                    if not isinstance(params, dict):

                        await self.reject(
                            send,
                            400,
                            "Invalid tool parameters",
                        )

                        return

                    tool_name = params.get("name")

                    # Reject unknown tools
                    if tool_name not in ALL_TOOLS:

                        audit_event(
                            event="mcp_authorization",
                            correlation_id=correlation_id,
                            role=role,
                            tool=tool_name,
                            status="denied",
                            error_type="ToolNotPermitted",
                        )

                        await self.reject(
                            send,
                            403,
                            "Tool not permitted",
                        )

                        return

                    # Read-only users cannot execute write tools
                    if (
                        role == "read"
                        and tool_name not in READ_TOOLS
                    ):

                        audit_event(
                            event="mcp_authorization",
                            correlation_id=correlation_id,
                            role=role,
                            tool=tool_name,
                            status="denied",
                            error_type="InsufficientPermission",
                        )

                        await self.reject(
                            send,
                            403,
                            "Forbidden",
                        )

                        return

                    # Authorized tool execution
                    audit_event(
                        event="mcp_authorization",
                        correlation_id=correlation_id,
                        role=role,
                        tool=tool_name,
                        status="allowed",
                    )

                # --------------------------------------------
                # 2.10 Replay request body to MCP application
                # --------------------------------------------

                delivered = False

                async def replay_receive():

                    nonlocal delivered

                    if not delivered:

                        delivered = True

                        return {
                            "type": "http.request",
                            "body": bytes(body),
                            "more_body": False,
                        }

                    return await receive()

                # --------------------------------------------
                # 2.11 Execute MCP application
                # --------------------------------------------

                await self.app(
                    scope,
                    replay_receive,
                    send,
                )

            finally:

                # --------------------------------------------
                # 2.12 Reset authenticated role context
                # --------------------------------------------

                role_var.reset(role_token)

        finally:

            # ------------------------------------------------
            # 2.13 Reset correlation context
            # ------------------------------------------------

            correlation_id_var.reset(context_token)

    # ========================================================
    # 3. HTTP Error Response Handler
    # ========================================================

    @staticmethod
    async def reject(send, status, message):

        body = json.dumps({
            "error": message,
        }).encode("utf-8")

        headers = [
            (
                b"content-type",
                b"application/json",
            ),
            (
                b"content-length",
                str(len(body)).encode("ascii"),
            ),
        ]

        if status == 401:
            headers.append(
                (
                    b"www-authenticate",
                    b"Bearer",
                )
            )

        # Send HTTP response headers
        await send({
            "type": "http.response.start",
            "status": status,
            "headers": headers,
        })

        # Send HTTP response body
        await send({
            "type": "http.response.body",
            "body": body,
            "more_body": False,
        })