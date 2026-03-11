from pydantic import BaseModel


class DocumentVersion(BaseModel):
    id: str
    document_id: str
    version_number: int
    source_file_name: str
