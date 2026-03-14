-- Phase 1 draft PostgreSQL FTS index for norm clause retrieval.
-- The current API still supports in-memory preview search for tests and early UI wiring.

create extension if not exists pg_trgm;

create index if not exists idx_norm_clause_entry_fts
on norm_clause_entries
using gin (
    to_tsvector(
        'simple',
        coalesce(title, '') || ' ' ||
        coalesce(content_preview, '') || ' ' ||
        coalesce(summary_text, '') || ' ' ||
        coalesce(commentary_summary, '')
    )
);

-- Example query shape for the persisted implementation:
-- select label, title, page_start, page_end, summary_text, commentary_summary
-- from norm_clause_entries
-- where document_id = $1
--   and ($2::text is null or label = $2)
--   and ($3::text is null or path_labels @> array[$3]::text[])
--   and (
--     $4::text is null
--     or to_tsvector('simple', coalesce(title, '') || ' ' || coalesce(summary_text, '') || ' ' || coalesce(commentary_summary, ''))
--        @@ plainto_tsquery('simple', $4)
--   )
-- order by label;
