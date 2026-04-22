from pydantic import BaseModel


class LoginRequest(BaseModel):
    email: str
    full_name: str
    code: str


class LoginResponse(BaseModel):
    id: int
    email: str
    full_name: str
    is_reviewer: bool
    access_token: str | None = None
