from pathlib import Path
import shutil

from app.integrations.storage.base import ObjectStorage


class LocalObjectStorage(ObjectStorage):
    def __init__(self, root_directory: Path) -> None:
        self.root_directory = root_directory

    def save_bytes(
        self,
        *,
        project_id: str,
        document_id: str,
        version_id: str,
        filename: str,
        content: bytes,
    ) -> str:
        target_dir = (
            self.root_directory / project_id / document_id / version_id
        )
        target_dir.mkdir(parents=True, exist_ok=True)
        target_path = target_dir / filename
        target_path.write_bytes(content)
        return str(target_path)

    def reset(self) -> None:
        if self.root_directory.exists():
            shutil.rmtree(self.root_directory)
