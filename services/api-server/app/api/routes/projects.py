from fastapi import APIRouter, Depends

from app.api.dependencies import get_current_user, get_project_service
from app.models.project import ProjectListResponse
from app.models.user import AuthenticatedUser
from app.services.project_service import ProjectService

router = APIRouter(tags=["projects"])


@router.get("/projects", response_model=ProjectListResponse)
def list_projects(
    current_user: AuthenticatedUser = Depends(get_current_user),
    service: ProjectService = Depends(get_project_service),
) -> ProjectListResponse:
    return service.list_projects_for_user(current_user)
