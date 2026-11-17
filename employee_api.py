from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
import logging
import uuid
from fastapi import Request

logger = logging.getLogger("uvicorn.error")
app = FastAPI(title="Employee REST API")


class Employee(BaseModel):
    employee_id: int
    name: str
    department: str
    salary: float = Field(gt=0)


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


@app.get("/employees")
def list_employees():
    return list(employees.values())


@app.get("/employees/{employee_id}")
def get_employee(employee_id: int):
    employee = employees.get(employee_id)

    if employee is None:
        raise HTTPException(
            status_code=404,
            detail="Employee not found",
        )

    return employee


@app.post("/employees", status_code=201)
def create_employee(employee: Employee):
    if employee.employee_id in employees:
        raise HTTPException(
            status_code=409,
            detail="Employee already exists",
        )

    employees[employee.employee_id] = employee
    return employee


@app.put("/employees/{employee_id}")
def update_employee(employee_id: int, employee: Employee):
    if employee_id not in employees:
        raise HTTPException(
            status_code=404,
            detail="Employee not found",
        )

    if employee.employee_id != employee_id:
        raise HTTPException(
            status_code=400,
            detail="Employee ID mismatch",
        )

    employees[employee_id] = employee
    return employee


@app.delete("/employees/{employee_id}")
def delete_employee(employee_id: int):
    if employee_id not in employees:
        raise HTTPException(
            status_code=404,
            detail="Employee not found",
        )

    del employees[employee_id]

    return {
        "success": True,
        "message": "Employee deleted successfully",
    }

@app.middleware("http")
async def correlation_middleware(request: Request, call_next):

    correlation_id = request.headers.get("X-Correlation-ID")
    if not correlation_id:
        correlation_id = str(uuid.uuid4())

    logger.info(
        "FastAPI request | correlation_id=%s | method=%s | path=%s",
        correlation_id,
        request.method,
        request.url.path,
    )

    response = await call_next(request)
    response.headers["X-Correlation-ID"] = correlation_id
    logger.info(
        "FastAPI response | correlation_id=%s | status=%s",
        correlation_id,
        response.status_code,
    )

    return response