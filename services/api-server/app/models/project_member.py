from pydantic import BaseModel

from app.models.user import UserRole


class ProjectMember(BaseModel):
    project_id: str
    user_id: str
    role: UserRole
