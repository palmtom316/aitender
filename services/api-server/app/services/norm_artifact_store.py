import json
from pathlib import Path

from app.schemas.norm_artifacts import (
    NormalizedNormArtifacts,
    StoredNormArtifacts,
)


class NormArtifactStore:
    def __init__(self, root_directory: Path) -> None:
        self.root_directory = root_directory

    def save(
        self,
        *,
        document_id: str,
        version_id: str,
        artifacts: NormalizedNormArtifacts,
    ) -> StoredNormArtifacts:
        target_dir = self.root_directory / document_id / version_id
        target_dir.mkdir(parents=True, exist_ok=True)

        markdown_path = target_dir / "full.md"
        layout_json_path = target_dir / "layout.json"
        metadata_json_path = target_dir / "metadata.json"

        markdown_path.write_text(artifacts.markdown_text)
        layout_json_path.write_text(
            json.dumps(artifacts.layout_payload, ensure_ascii=False, indent=2)
        )
        metadata_json_path.write_text(
            json.dumps(artifacts.metadata, ensure_ascii=False, indent=2)
        )

        return StoredNormArtifacts(
            markdown_path=markdown_path,
            layout_json_path=layout_json_path,
            metadata_json_path=metadata_json_path,
        )

    def save_json(
        self,
        *,
        document_id: str,
        version_id: str,
        filename: str,
        payload: dict,
    ) -> Path:
        target_dir = self.root_directory / document_id / version_id
        target_dir.mkdir(parents=True, exist_ok=True)

        target_path = target_dir / filename
        target_path.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2)
        )
        return target_path
