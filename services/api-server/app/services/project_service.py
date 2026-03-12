from pathlib import Path

from app.models.project import Project, ProjectListItem, ProjectListResponse
from app.models.user import AuthenticatedUser, UserRole
from app.repositories.factory import get_project_repository
from app.repositories.json_project_repository import JsonProjectRepository
from app.repositories.project_repository import ProjectRepository


class ProjectService:
    def __init__(
        self,
        state_path: Path | None = None,
        repository: ProjectRepository | None = None,
    ) -> None:
        self._repository = (
            repository
            or JsonProjectRepository(state_path=state_path)
            if state_path is not None
            else get_project_repository()
        )

    def reset(self) -> None:
        self._repository.reset()

    def list_projects_for_user(
        self,
        user: AuthenticatedUser,
    ) -> ProjectListResponse:
        projects = {
            project.id: project
            for project in self._repository.list_projects()
        }
        memberships = self._repository.list_memberships()

        if user.role == UserRole.ADMIN:
            items = [
                ProjectListItem(
                    id=project.id,
                    organization_id=project.organization_id,
                    name=project.name,
                    member_role=UserRole.ADMIN,
                )
                for project in projects.values()
                if project.organization_id == user.organization_id
            ]
            return ProjectListResponse(items=items)

        memberships = [
            membership
            for membership in memberships
            if membership.user_id == user.id
        ]
        items = [
            ProjectListItem(
                id=projects[membership.project_id].id,
                organization_id=projects[membership.project_id].organization_id,
                name=projects[membership.project_id].name,
                member_role=membership.role,
            )
            for membership in memberships
        ]
        return ProjectListResponse(items=items)


project_service = ProjectService(repository=get_project_repository())
