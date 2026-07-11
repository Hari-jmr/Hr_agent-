from pydantic import BaseModel, ConfigDict


class LoginRequest(BaseModel):
    username: str
    password: str


class EmployeeProfile(BaseModel):
    model_config = ConfigDict(extra='allow')

    name: str | None = None
    job_title: str | None = None
    department: str | None = None
    emp_code: str | None = None


class AuthResponse(BaseModel):
    authenticated: bool
    employee: EmployeeProfile | None = None
    is_hr: bool | None = None
    login: str | None = None
