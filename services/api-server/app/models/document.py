from pydantic import BaseModel


class Document(BaseModel):
    id: str
    organization_id: str
    project_id: str
    file_name: str
    library_type: str
    uploaded_by: str
    status: str
