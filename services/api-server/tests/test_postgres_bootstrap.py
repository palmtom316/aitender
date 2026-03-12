from pathlib import Path

from app.repositories.bootstrap import initialize_postgres_database
from app.repositories.postgres_base import PostgresRepositoryBase


class FakeCursor:
    def __init__(self, executed: list[str]) -> None:
        self._executed = executed

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def execute(self, sql: str) -> None:
        self._executed.append(sql)


class FakeConnection:
    def __init__(self, executed: list[str]) -> None:
        self._executed = executed

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def cursor(self) -> FakeCursor:
        return FakeCursor(self._executed)


class FakePostgresRepository(PostgresRepositoryBase):
    def __init__(self, sql_directory: Path, executed: list[str]) -> None:
        self._sql_directory = sql_directory
        self._executed = executed
        super().__init__(database_url="postgresql://aitender:test@localhost:5432/aitender")

    def _connect(self):
        return FakeConnection(self._executed)

    def _sql_path(self, filename: str) -> Path:
        return self._sql_directory / filename


def test_postgres_repository_base_executes_schema_and_seed_files(tmp_path: Path):
    executed: list[str] = []
    (tmp_path / "schema.sql").write_text("create table example(id int);")
    (tmp_path / "fts.sql").write_text("create index example_idx on example(id);")
    (tmp_path / "seed.sql").write_text("insert into example values (1);")
    repository = FakePostgresRepository(tmp_path, executed)

    repository.initialize_schema()
    repository.seed_defaults()

    assert executed == [
        "create table example(id int);",
        "create index example_idx on example(id);",
        "insert into example values (1);",
    ]


def test_initialize_postgres_database_runs_seed_by_default(monkeypatch):
    calls: list[tuple[str | None, bool]] = []

    class FakeBootstrapRepository:
        def __init__(self, database_url: str | None = None) -> None:
            calls.append((database_url, False))

        def initialize_schema(self) -> None:
            calls.append((None, True))

        def seed_defaults(self) -> None:
            calls.append((None, False))

    monkeypatch.setattr(
        "app.repositories.bootstrap.PostgresRepositoryBase",
        FakeBootstrapRepository,
    )

    initialize_postgres_database(database_url="postgresql://aitender:test@localhost/db")

    assert calls == [
        ("postgresql://aitender:test@localhost/db", False),
        (None, True),
        (None, False),
    ]


def test_initialize_postgres_database_can_skip_seed(monkeypatch):
    calls: list[str] = []

    class FakeBootstrapRepository:
        def __init__(self, database_url: str | None = None) -> None:
            calls.append(f"init:{database_url}")

        def initialize_schema(self) -> None:
            calls.append("schema")

        def seed_defaults(self) -> None:
            calls.append("seed")

    monkeypatch.setattr(
        "app.repositories.bootstrap.PostgresRepositoryBase",
        FakeBootstrapRepository,
    )

    initialize_postgres_database(seed=False)

    assert calls == ["init:None", "schema"]
