from abc import ABC, abstractmethod


class ObjectStorage(ABC):
    @abstractmethod
    def save_bytes(
        self,
        *,
        project_id: str,
        document_id: str,
        version_id: str,
        filename: str,
        content: bytes,
    ) -> str:
        raise NotImplementedError

    @abstractmethod
    def reset(self) -> None:
        raise NotImplementedError
