create table if not exists projects (
    id text primary key,
    organization_id text not null,
    name text not null
);

create table if not exists project_memberships (
    project_id text not null,
    user_id text not null,
    role text not null,
    primary key (project_id, user_id)
);

create table if not exists documents (
    id text primary key,
    organization_id text not null,
    project_id text not null,
    file_name text not null,
    library_type text not null,
    uploaded_by text not null,
    status text not null,
    current_version_id text,
    latest_job_id text
);

create index if not exists idx_documents_project_library
on documents (project_id, library_type);

create table if not exists document_versions (
    id text primary key,
    document_id text not null,
    version_number integer not null,
    source_file_name text not null
);

create index if not exists idx_document_versions_document
on document_versions (document_id);

create table if not exists document_artifacts (
    id text primary key,
    document_version_id text not null,
    artifact_type text not null,
    storage_path text not null
);

create unique index if not exists idx_document_artifacts_version_type
on document_artifacts (document_version_id, artifact_type);

create table if not exists norm_clause_entries (
    document_id text not null,
    label text not null,
    title text not null,
    node_type text not null,
    parent_label text,
    path_labels text[] not null default '{}',
    page_start integer,
    page_end integer,
    summary_text text not null,
    commentary_summary text not null default '',
    tags text[] not null default '{}',
    primary key (document_id, label)
);

alter table norm_clause_entries
    add column if not exists path_labels text[] not null default '{}';

alter table norm_clause_entries
    add column if not exists commentary_summary text not null default '';

alter table norm_clause_entries
    add column if not exists tags text[] not null default '{}';

create index if not exists idx_norm_clause_entries_document_parent
on norm_clause_entries (document_id, parent_label);

create index if not exists idx_norm_clause_entries_path_labels
on norm_clause_entries using gin (path_labels);

create table if not exists norm_commentary_entries (
    document_id text not null,
    label text not null,
    title text not null,
    node_type text not null,
    parent_label text,
    page_start integer,
    page_end integer,
    commentary_text text not null,
    summary_text text not null default '',
    tags text[] not null default '{}',
    primary key (document_id, label)
);

alter table norm_commentary_entries
    add column if not exists summary_text text not null default '';

alter table norm_commentary_entries
    add column if not exists tags text[] not null default '{}';

create index if not exists idx_norm_commentary_entries_document
on norm_commentary_entries (document_id);

create table if not exists processing_jobs (
    id text primary key,
    document_id text not null,
    provider_name text not null,
    status text not null,
    error_message text
);

create index if not exists idx_processing_jobs_document
on processing_jobs (document_id);

create table if not exists audit_logs (
    id text primary key,
    job_id text not null,
    step text not null,
    message text not null,
    level text not null,
    created_at timestamptz not null default now()
);

alter table audit_logs
    add column if not exists created_at timestamptz not null default now();

create index if not exists idx_audit_logs_job_created
on audit_logs (job_id, created_at);
