from app.models.norm_clause_entry import NormClauseEntry
from app.models.norm_commentary_entry import NormCommentaryEntry
from app.repositories.norm_structure_repository import NormStructureRepository
from app.repositories.postgres_base import PostgresRepositoryBase


class PostgresNormStructureRepository(PostgresRepositoryBase, NormStructureRepository):
    def supports_persisted_search(self) -> bool:
        return True

    def reset(self) -> None:
        with self._connect() as connection:
            with connection.cursor() as cursor:
                cursor.execute("delete from norm_commentary_entries")
                cursor.execute("delete from norm_clause_entries")

    def replace_clause_entries(
        self,
        document_id: str,
        entries: list[NormClauseEntry],
    ) -> None:
        path_labels_by_label = self._build_path_labels_by_label(entries)
        with self._connect() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    "delete from norm_clause_entries where document_id = %s",
                    [document_id],
                )
                for entry in entries:
                    cursor.execute(
                        """
                        insert into norm_clause_entries (
                            document_id, label, title, node_type, parent_label,
                            path_labels, page_start, page_end, summary_text,
                            commentary_summary, tags
                        ) values (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                        """,
                        [
                            entry.document_id,
                            entry.label,
                            entry.title,
                            entry.node_type,
                            entry.parent_label,
                            path_labels_by_label.get(entry.label, []),
                            entry.page_start,
                            entry.page_end,
                            entry.summary_text,
                            entry.commentary_summary,
                            entry.tags,
                        ],
                    )

    def replace_commentary_entries(
        self,
        document_id: str,
        entries: list[NormCommentaryEntry],
    ) -> None:
        with self._connect() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    "delete from norm_commentary_entries where document_id = %s",
                    [document_id],
                )
                for entry in entries:
                    cursor.execute(
                        """
                        insert into norm_commentary_entries (
                            document_id, label, title, node_type, parent_label,
                            page_start, page_end, commentary_text, summary_text, tags
                        ) values (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                        """,
                        [
                            entry.document_id,
                            entry.label,
                            entry.title,
                            entry.node_type,
                            entry.parent_label,
                            entry.page_start,
                            entry.page_end,
                            entry.commentary_text,
                            entry.summary_text,
                            entry.tags,
                        ],
                    )
                    if entry.node_type == "clause":
                        cursor.execute(
                            """
                            update norm_clause_entries
                            set commentary_summary = %s
                            where document_id = %s and label = %s
                            """,
                            [
                                entry.commentary_text,
                                entry.document_id,
                                entry.label,
                            ],
                        )

    def list_clause_entries(self, document_id: str) -> list[NormClauseEntry]:
        with self._connect() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    select document_id, label, title, node_type, parent_label, path_labels,
                           page_start, page_end, summary_text, commentary_summary, tags
                    from norm_clause_entries
                    where document_id = %s
                    order by label
                    """,
                    [document_id],
                )
                return [
                    NormClauseEntry.model_validate(row)
                    for row in cursor.fetchall()
                ]

    def list_commentary_entries(
        self,
        document_id: str,
    ) -> list[NormCommentaryEntry]:
        with self._connect() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    select document_id, label, title, node_type, parent_label,
                           page_start, page_end, commentary_text, summary_text, tags
                    from norm_commentary_entries
                    where document_id = %s
                    order by label
                    """,
                    [document_id],
                )
                return [
                    NormCommentaryEntry.model_validate(row)
                    for row in cursor.fetchall()
                ]

    def search_clause_results(
        self,
        *,
        document_id: str,
        query: str | None = None,
        clause_id: str | None = None,
        path_prefix: str | None = None,
    ) -> list[dict] | None:
        with self._connect() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    select
                        clause.label,
                        clause.title,
                        clause.page_start,
                        clause.page_end,
                        clause.summary_text,
                        clause.commentary_summary,
                        clause.path_labels,
                        clause.tags
                    from norm_clause_entries as clause
                    where clause.document_id = %s
                      and clause.node_type = 'clause'
                      and (%s::text is null or clause.label = %s::text)
                      and (
                        %s::text is null
                        or clause.path_labels @> array[%s::text]
                      )
                      and (
                        %s::text is null
                        or to_tsvector(
                            'simple',
                            coalesce(clause.title, '') || ' ' ||
                            coalesce(clause.summary_text, '') || ' ' ||
                            coalesce(clause.commentary_summary, '')
                        ) @@ plainto_tsquery('simple', %s::text)
                      )
                    order by clause.label
                    """,
                    [
                        document_id,
                        clause_id,
                        clause_id,
                        path_prefix,
                        path_prefix,
                        query,
                        query,
                    ],
                )
                return [
                    {
                        "label": row["label"],
                        "title": row["title"],
                        "page_start": row["page_start"],
                        "page_end": row["page_end"],
                        "summary_text": row["summary_text"],
                        "commentary_summary": row["commentary_summary"],
                        "path_labels": list(row["path_labels"] or []),
                        "tags": list(row["tags"] or []),
                    }
                    for row in cursor.fetchall()
                ]

    @staticmethod
    def _build_path_labels_by_label(
        entries: list[NormClauseEntry],
    ) -> dict[str, list[str]]:
        entry_by_label = {
            entry.label: entry
            for entry in entries
        }
        path_labels_by_label: dict[str, list[str]] = {}

        for entry in entries:
            path: list[str] = []
            current: NormClauseEntry | None = entry
            while current is not None:
                path.append(current.label)
                current = (
                    entry_by_label.get(current.parent_label)
                    if current.parent_label
                    else None
                )
            path_labels_by_label[entry.label] = list(reversed(path))

        return path_labels_by_label
