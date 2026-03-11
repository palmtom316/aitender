from pydantic import BaseModel

from app.models.user import UserRole


class Project(BaseModel):
    id: str
    organization_id: str
    name: str


class ProjectListItem(BaseModel):
    id: str
    organization_id: str
    name: str
    member_role: UserRole


class ProjectListResponse(BaseModel):
    items: list[ProjectListItem]
