from pydantic import BaseModel


class LoginRequest(BaseModel):
    email: str
    first_name: str
    last_name: str
    code: str


class LoginResponse(BaseModel):
    id: int
    email: str
    first_name: str
    last_name: str
    is_reviewer: bool
    access_token: str | None = None
