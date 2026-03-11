from enum import StrEnum

from pydantic import BaseModel


class UserRole(StrEnum):
    ADMIN = "admin"
    PROJECT_MANAGER = "project_manager"
    WRITER = "writer"
    VIEWER = "viewer"


class User(BaseModel):
    id: str
    organization_id: str
    email: str
    password: str
    role: UserRole
    display_name: str


class AuthenticatedUser(BaseModel):
    id: str
    organization_id: str
    role: UserRole
    display_name: str


class LoginRequest(BaseModel):
    email: str
    password: str


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: AuthenticatedUser
