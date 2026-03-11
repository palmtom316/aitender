from pydantic import BaseModel


class DocumentArtifact(BaseModel):
    id: str
    document_version_id: str
    artifact_type: str
    storage_path: str
