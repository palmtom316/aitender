from app.models.project import Project
from app.models.project_member import ProjectMember
from app.repositories.postgres_base import PostgresRepositoryBase
from app.repositories.project_repository import ProjectRepository


class PostgresProjectRepository(PostgresRepositoryBase, ProjectRepository):
    def reset(self) -> None:
        with self._connect() as connection:
            with connection.cursor() as cursor:
                cursor.execute("delete from project_memberships")
                cursor.execute("delete from projects")

    def list_projects(self) -> list[Project]:
        with self._connect() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    select id, organization_id, name
                    from projects
                    order by id
                    """
                )
                return [
                    Project.model_validate(row)
                    for row in cursor.fetchall()
                ]

    def list_memberships(self) -> list[ProjectMember]:
        with self._connect() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    select project_id, user_id, role
                    from project_memberships
                    order by project_id, user_id
                    """
                )
                return [
                    ProjectMember.model_validate(row)
                    for row in cursor.fetchall()
                ]
