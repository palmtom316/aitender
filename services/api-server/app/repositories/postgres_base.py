from importlib import import_module
from pathlib import Path

from app.core.config import settings


class PostgresRepositoryBase:
    def __init__(self, database_url: str | None = None) -> None:
        self._database_url = database_url or settings.database_url
        if not self._database_url:
            raise RuntimeError(
                "AITENDER_DATABASE_URL must be configured for the postgres repository backend"
            )

    def _connect(self):
        try:
            psycopg = import_module("psycopg")
            rows = import_module("psycopg.rows")
        except ModuleNotFoundError as exc:
            raise RuntimeError(
                "psycopg is required for the postgres repository backend"
            ) from exc

        return psycopg.connect(self._database_url, row_factory=rows.dict_row)

    def _sql_path(self, filename: str) -> Path:
        return Path(__file__).resolve().parent.parent / "db" / filename

    def _run_sql_file(self, filename: str) -> None:
        sql_path = self._sql_path(filename)
        with self._connect() as connection:
            with connection.cursor() as cursor:
                cursor.execute(sql_path.read_text())

    def initialize_schema(self) -> None:
        self._run_sql_file("schema.sql")
        self._run_sql_file("fts.sql")

    def seed_defaults(self) -> None:
        self._run_sql_file("seed.sql")
