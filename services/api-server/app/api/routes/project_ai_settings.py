from fastapi import APIRouter, Depends, HTTPException

from app.api.dependencies import (
    get_current_user,
    get_project_ai_settings_service,
    get_project_service,
)
from app.models.project_ai_settings import ProjectAiSettings
from app.models.user import AuthenticatedUser
from app.services.project_ai_settings_service import ProjectAiSettingsService
from app.services.project_service import ProjectService

router = APIRouter(prefix="/projects/{project_id}/settings/ai", tags=["project-ai-settings"])


def _assert_project_visible(
    *,
    current_user: AuthenticatedUser,
    project_id: str,
    project_service: ProjectService,
) -> None:
    visible_projects = project_service.list_projects_for_user(current_user)
    if project_id not in {project.id for project in visible_projects.items}:
        raise HTTPException(status_code=404, detail="Project not found")


@router.get("")
def get_project_ai_settings(
    project_id: str,
    current_user: AuthenticatedUser = Depends(get_current_user),
    project_service: ProjectService = Depends(get_project_service),
    service: ProjectAiSettingsService = Depends(get_project_ai_settings_service),
) -> ProjectAiSettings:
    _assert_project_visible(
        current_user=current_user,
        project_id=project_id,
        project_service=project_service,
    )
    return service.get_settings(project_id)


@router.put("")
def update_project_ai_settings(
    project_id: str,
    payload: ProjectAiSettings,
    current_user: AuthenticatedUser = Depends(get_current_user),
    project_service: ProjectService = Depends(get_project_service),
    service: ProjectAiSettingsService = Depends(get_project_ai_settings_service),
) -> ProjectAiSettings:
    _assert_project_visible(
        current_user=current_user,
        project_id=project_id,
        project_service=project_service,
    )
    return service.update_settings(project_id, payload)
