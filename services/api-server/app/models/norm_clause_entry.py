from pydantic import BaseModel, Field


class NormClauseEntry(BaseModel):
    document_id: str
    label: str
    title: str
    node_type: str
    parent_label: str | None
    path_labels: list[str] = Field(default_factory=list)
    page_start: int | None
    page_end: int | None
    summary_text: str
    commentary_summary: str = ""
