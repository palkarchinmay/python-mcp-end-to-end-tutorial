import os
import logging
import sys
from typing import Any

import httpx

from mcp.server import MCPServer
from mcp.server.mcpserver.exceptions import ToolError
from pydantic import BaseModel, Field


# ============================================================
# 1. Logging Configuration
# ============================================================

# For STDIO MCP servers, logs must go to stderr.
# stdout is reserved for MCP protocol communication.

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    stream=sys.stderr
)

logger = logging.getLogger("employee_rest_mcp")


# ============================================================
# 2. Initialize MCP Server
# ============================================================

# IMPORTANT:
# This object must be globally defined so that
# `mcp dev` and `mcp run` can discover it.

mcp = MCPServer(
    "Employee REST MCP Server",
    instructions=(
        "This MCP server provides employee CRUD operations "
        "through an existing FastAPI REST service."
    )
)


# ============================================================
# 3. REST API Configuration
# ============================================================

API_BASE_URL = os.getenv(
    "EMPLOYEE_API_URL",
    "http://127.0.0.1:8001"
).rstrip("/")

API_TIMEOUT = 10.0


# ============================================================
# 4. Pydantic Models
# ============================================================

class Employee(BaseModel):
    employee_id: int = Field(gt=0)
    name: str = Field(min_length=2)
    department: str = Field(min_length=2)
    salary: float = Field(gt=0)


class DeleteResponse(BaseModel):
    success: bool
    message: str


# ============================================================
# 5. Common REST API Helper
# ============================================================

async def call_api(
    method: str,
    endpoint: str,
    **kwargs: Any
) -> Any:
    """
    Calls the FastAPI Employee REST service.

    Handles:
    - HTTP errors
    - Connection failures
    - Timeouts
    - Invalid JSON
    """

    url = f"{API_BASE_URL}{endpoint}"

    logger.info(
        "Calling REST API: %s %s",
        method,
        url
    )

    try:
        async with httpx.AsyncClient(
            timeout=API_TIMEOUT
        ) as client:

            response = await client.request(
                method=method,
                url=url,
                **kwargs
            )

            response.raise_for_status()

            return response.json()

    except httpx.HTTPStatusError as exc:

        status_code = exc.response.status_code

        try:
            error_data = exc.response.json()
            error_detail = error_data.get(
                "detail",
                exc.response.text
            )
        except (ValueError, AttributeError):
            error_detail = exc.response.text

        logger.error(
            "REST API returned HTTP %s",
            status_code
        )

        raise ToolError(
            f"Employee REST API error {status_code}: "
            f"{error_detail}"
        ) from exc

    except httpx.TimeoutException as exc:

        logger.error("REST API request timed out")

        raise ToolError(
            "Employee REST API request timed out."
        ) from exc

    except httpx.RequestError as exc:

        logger.error(
            "REST API connection error: %s",
            type(exc).__name__
        )

        raise ToolError(
            "Unable to connect to Employee REST API. "
            "Verify FastAPI is running on port 8001."
        ) from exc

    except ValueError as exc:

        logger.error("REST API returned invalid JSON")

        raise ToolError(
            "Employee REST API returned invalid JSON."
        ) from exc


# ============================================================
# 6. MCP TOOL: LIST EMPLOYEES
# ============================================================

@mcp.tool()
async def list_employees() -> list[Employee]:
    """
    Retrieve all employee records from FastAPI.
    """

    logger.info("Executing MCP tool: list_employees")

    data = await call_api(
        "GET",
        "/employees"
    )

    return [
        Employee.model_validate(item)
        for item in data
    ]


# ============================================================
# 7. MCP TOOL: GET EMPLOYEE
# ============================================================

@mcp.tool()
async def get_employee(
    employee_id: int = Field(gt=0)
) -> Employee:
    """
    Retrieve an employee by employee ID.
    """

    logger.info(
        "Executing MCP tool: get_employee(%s)",
        employee_id
    )

    data = await call_api(
        "GET",
        f"/employees/{employee_id}"
    )

    return Employee.model_validate(data)


# ============================================================
# 8. MCP TOOL: CREATE EMPLOYEE
# ============================================================

@mcp.tool()
async def create_employee(
    employee_id: int = Field(gt=0),
    name: str = Field(min_length=2),
    department: str = Field(min_length=2),
    salary: float = Field(gt=0)
) -> Employee:
    """
    Create an employee through the FastAPI REST service.
    """

    logger.info(
        "Executing MCP tool: create_employee(%s)",
        employee_id
    )

    employee = Employee(
        employee_id=employee_id,
        name=name,
        department=department,
        salary=salary
    )

    data = await call_api(
        "POST",
        "/employees",
        json=employee.model_dump()
    )

    return Employee.model_validate(data)


# ============================================================
# 9. MCP TOOL: UPDATE EMPLOYEE
# ============================================================

@mcp.tool()
async def update_employee(
    employee_id: int = Field(gt=0),
    name: str = Field(min_length=2),
    department: str = Field(min_length=2),
    salary: float = Field(gt=0)
) -> Employee:
    """
    Update an employee using HTTP PUT.

    All fields are required because the FastAPI
    endpoint performs a full record replacement.
    """

    logger.info(
        "Executing MCP tool: update_employee(%s)",
        employee_id
    )

    employee = Employee(
        employee_id=employee_id,
        name=name,
        department=department,
        salary=salary
    )

    data = await call_api(
        "PUT",
        f"/employees/{employee_id}",
        json=employee.model_dump()
    )

    return Employee.model_validate(data)


# ============================================================
# 10. MCP TOOL: DELETE EMPLOYEE
# ============================================

@mcp.tool()
async def delete_employee(
    employee_id: int = Field(gt=0)
) -> DeleteResponse:
    """
    Delete an employee through FastAPI.
    """

    logger.info(
        "Executing MCP tool: delete_employee(%s)",
        employee_id
    )

    data = await call_api(
        "DELETE",
        f"/employees/{employee_id}"
    )

    return DeleteResponse.model_validate(data)


# ============================================================
# 11. MCP RESOURCE: DEPARTMENTS
# ============================================================

@mcp.resource("employee://departments")
def get_departments() -> str:
    """
    Return available departments.
    """

    return """
Available Departments:

1. Data Science
2. Engineering
3. Human Resources
4. Finance
"""


# ============================================================
# 12. MCP PROMPT: EMPLOYEE ANALYSIS
# ============================================================

@mcp.prompt()
def employee_analysis(
    department: str
) -> str:
    """
    Generate a structured employee analysis prompt.
    """

    return f"""
You are an HR data analyst.

Analyze employees from the {department} department.

Provide:

1. Total employee count
2. Average salary
3. Minimum salary
4. Maximum salary
5. Salary distribution
6. Department overview
7. Recommendations

Use actual employee records.
Do not invent information.
"""


# ============================================================
# 13. MCP Server Entry Point
# ============================================================

# MCP CLI discovers the globally defined `mcp` object.
#
# Run:
#
# mcp dev employee_rest_mcp_server.py
#
# or:
#
# mcp run employee_rest_mcp_server.py