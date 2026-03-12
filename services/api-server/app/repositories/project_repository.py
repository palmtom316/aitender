from abc import ABC, abstractmethod

from app.models.project import Project
from app.models.project_member import ProjectMember


class ProjectRepository(ABC):
    @abstractmethod
    def reset(self) -> None:
        raise NotImplementedError

    @abstractmethod
    def list_projects(self) -> list[Project]:
        raise NotImplementedError

    @abstractmethod
    def list_memberships(self) -> list[ProjectMember]:
        raise NotImplementedError
