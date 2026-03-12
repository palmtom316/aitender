from pathlib import Path

from app.core.config import settings
from app.models.project import Project
from app.models.project_member import ProjectMember
from app.models.user import UserRole
from app.repositories.json_state_store import JsonStateStore
from app.repositories.project_repository import ProjectRepository


class JsonProjectRepository(ProjectRepository):
    def __init__(self, state_path: Path | None = None) -> None:
        self._store = JsonStateStore(
            state_path or settings.state_root / "projects.json",
        )
        self._store.load(default_factory=self._default_state)

    def reset(self) -> None:
        self._store.reset()
        self._store.load(default_factory=self._default_state)

    def list_projects(self) -> list[Project]:
        state = self._store.load(default_factory=self._default_state)
        return [
            Project.model_validate(project)
            for project in state["projects"]
        ]

    def list_memberships(self) -> list[ProjectMember]:
        state = self._store.load(default_factory=self._default_state)
        return [
            ProjectMember.model_validate(membership)
            for membership in state["memberships"]
        ]

    @staticmethod
    def _default_state() -> dict:
        return {
            "projects": [
                Project(
                    id="project-alpha",
                    organization_id="org-1",
                    name="Alpha Substation Bid",
                ).model_dump(),
                Project(
                    id="project-beta",
                    organization_id="org-1",
                    name="Beta Transmission Line Bid",
                ).model_dump(),
            ],
            "memberships": [
                ProjectMember(
                    project_id="project-alpha",
                    user_id="user-pm",
                    role=UserRole.PROJECT_MANAGER,
                ).model_dump(mode="json"),
                ProjectMember(
                    project_id="project-beta",
                    user_id="user-pm",
                    role=UserRole.PROJECT_MANAGER,
                ).model_dump(mode="json"),
                ProjectMember(
                    project_id="project-alpha",
                    user_id="user-writer",
                    role=UserRole.WRITER,
                ).model_dump(mode="json"),
                ProjectMember(
                    project_id="project-beta",
                    user_id="user-viewer",
                    role=UserRole.VIEWER,
                ).model_dump(mode="json"),
            ],
        }
