from app.models.project import Project, ProjectListItem, ProjectListResponse
from app.models.project_member import ProjectMember
from app.models.user import AuthenticatedUser, UserRole


class ProjectService:
    def __init__(self) -> None:
        self._projects = {
            "project-alpha": Project(
                id="project-alpha",
                organization_id="org-1",
                name="Alpha Substation Bid",
            ),
            "project-beta": Project(
                id="project-beta",
                organization_id="org-1",
                name="Beta Transmission Line Bid",
            ),
        }
        self._memberships = [
            ProjectMember(
                project_id="project-alpha",
                user_id="user-pm",
                role=UserRole.PROJECT_MANAGER,
            ),
            ProjectMember(
                project_id="project-beta",
                user_id="user-pm",
                role=UserRole.PROJECT_MANAGER,
            ),
            ProjectMember(
                project_id="project-alpha",
                user_id="user-writer",
                role=UserRole.WRITER,
            ),
            ProjectMember(
                project_id="project-beta",
                user_id="user-viewer",
                role=UserRole.VIEWER,
            ),
        ]

    def list_projects_for_user(
        self,
        user: AuthenticatedUser,
    ) -> ProjectListResponse:
        if user.role == UserRole.ADMIN:
            items = [
                ProjectListItem(
                    id=project.id,
                    organization_id=project.organization_id,
                    name=project.name,
                    member_role=UserRole.ADMIN,
                )
                for project in self._projects.values()
                if project.organization_id == user.organization_id
            ]
            return ProjectListResponse(items=items)

        memberships = [
            membership
            for membership in self._memberships
            if membership.user_id == user.id
        ]
        items = [
            ProjectListItem(
                id=self._projects[membership.project_id].id,
                organization_id=self._projects[membership.project_id].organization_id,
                name=self._projects[membership.project_id].name,
                member_role=membership.role,
            )
            for membership in memberships
        ]
        return ProjectListResponse(items=items)


project_service = ProjectService()
