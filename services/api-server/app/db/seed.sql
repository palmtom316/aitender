insert into projects (id, organization_id, name) values
    ('project-alpha', 'org-1', 'Alpha Substation Bid'),
    ('project-beta', 'org-1', 'Beta Transmission Line Bid')
on conflict (id) do nothing;

insert into project_memberships (project_id, user_id, role) values
    ('project-alpha', 'user-pm', 'project_manager'),
    ('project-beta', 'user-pm', 'project_manager'),
    ('project-alpha', 'user-writer', 'writer'),
    ('project-beta', 'user-viewer', 'viewer')
on conflict (project_id, user_id) do nothing;
