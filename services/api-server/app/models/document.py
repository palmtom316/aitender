from pydantic import BaseModel


class Document(BaseModel):
    id: str
    organization_id: str
    project_id: str
    file_name: str
    library_type: str
    uploaded_by: str
    status: str
    current_version_id: str | None = None
    latest_job_id: str | None = None
