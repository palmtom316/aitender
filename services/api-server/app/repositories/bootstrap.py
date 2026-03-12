from app.repositories.postgres_base import PostgresRepositoryBase


def initialize_postgres_database(
    *,
    database_url: str | None = None,
    seed: bool = True,
) -> None:
    repository = PostgresRepositoryBase(database_url=database_url)
    repository.initialize_schema()
    if seed:
        repository.seed_defaults()
