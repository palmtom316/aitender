from pathlib import Path

from pydantic import BaseModel


class PageText(BaseModel):
    page: int
    text: str


class NormalizedNormArtifacts(BaseModel):
    provider: str
    markdown_text: str
    layout_payload: dict
    page_texts: list[PageText]
    metadata: dict


class StoredNormArtifacts(BaseModel):
    markdown_path: Path
    layout_json_path: Path
    metadata_json_path: Path
