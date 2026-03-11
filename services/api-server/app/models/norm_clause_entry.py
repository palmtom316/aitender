from pydantic import BaseModel


class NormClauseEntry(BaseModel):
    document_id: str
    label: str
    title: str
    node_type: str
    parent_label: str | None
    page_start: int | None
    page_end: int | None
    summary_text: str
