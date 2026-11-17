from typing import Optional

from mcp.server import MCPServer
from pydantic import BaseModel, Field


# Initialize MCP Server
mcp = MCPServer("Employee Management MCP Server")


# --------------------------------------------------
# 1. Employee Data Model
# --------------------------------------------------

class Employee(BaseModel):
    employee_id: int
    name: str
    department: str
    salary: float


class EmployeeInput(BaseModel):
    name: str = Field(min_length=2)
    department: str = Field(min_length=2)
    salary: float = Field(gt=0)


class OperationResult(BaseModel):
    success: bool
    message: str


# --------------------------------------------------
# 2. In-Memory Database
# --------------------------------------------------

employees = {
    101: Employee(
        employee_id=101,
        name="Rahul",
        department="Data Science",
        salary=120000,
    ),
    102: Employee(
        employee_id=102,
        name="Priya",
        department="Engineering",
        salary=150000,
    ),
}


# --------------------------------------------------
# 3. READ Employee
# --------------------------------------------------

@mcp.tool()
def get_employee(employee_id: int) -> Optional[Employee]:
    """Retrieve an employee using employee ID."""

    return employees.get(employee_id)


# --------------------------------------------------
# 4. LIST Employees
# --------------------------------------------------

@mcp.tool()
def list_employees() -> list[Employee]:
    """Retrieve all employees."""

    return list(employees.values())


# --------------------------------------------------
# 5. CREATE Employee
# --------------------------------------------------

@mcp.tool()
def create_employee(
    employee_id: int,
    name: str,
    department: str,
    salary: float,
) -> OperationResult:
    """Create a new employee."""

    if employee_id in employees:
        return OperationResult(
            success=False,
            message="Employee already exists",
        )

    employee_data = EmployeeInput(
        name=name,
        department=department,
        salary=salary,
    )

    employees[employee_id] = Employee(
        employee_id=employee_id,
        **employee_data.model_dump(),
    )

    return OperationResult(
        success=True,
        message=f"Employee {employee_id} created successfully",
    )


# --------------------------------------------------
# 6. UPDATE Employee
# --------------------------------------------------

@mcp.tool()
def update_employee(
    employee_id: int,
    name: Optional[str] = None,
    department: Optional[str] = None,
    salary: Optional[float] = None,
) -> OperationResult:
    """Update an existing employee."""

    employee = employees.get(employee_id)

    if employee is None:
        return OperationResult(
            success=False,
            message="Employee not found",
        )

    updates = {}

    if name is not None:
        updates["name"] = name

    if department is not None:
        updates["department"] = department

    if salary is not None:
        updates["salary"] = salary

    updated_data = employee.model_dump()
    updated_data.update(updates)

    validated = EmployeeInput(
        name=updated_data["name"],
        department=updated_data["department"],
        salary=updated_data["salary"],
    )

    employees[employee_id] = Employee(
        employee_id=employee_id,
        **validated.model_dump(),
    )

    return OperationResult(
        success=True,
        message=f"Employee {employee_id} updated successfully",
    )


# --------------------------------------------------
# 7. DELETE Employee
# --------------------------------------------------

@mcp.tool()
def delete_employee(employee_id: int) -> OperationResult:
    """Delete an employee."""

    if employee_id not in employees:
        return OperationResult(
            success=False,
            message="Employee not found",
        )

    del employees[employee_id]

    return OperationResult(
        success=True,
        message=f"Employee {employee_id} deleted successfully",
    )


# --------------------------------------------------
# 8. MCP Resource
# --------------------------------------------------

@mcp.resource("employee://departments")
def get_departments() -> str:
    """Return available departments."""

    return """
    Available Departments:
    - Data Science
    - Engineering
    - Human Resources
    - Finance
    """


# --------------------------------------------------
# 9. MCP Prompt
# --------------------------------------------------

@mcp.prompt()
def employee_analysis(department: str) -> str:
    """Generate an employee analysis prompt."""

    return f"""
    Analyze employees partment.

    Provide:
    1. Employee count
    2. Salary distribution
    3. Department overview
    4. Recommendations
    """