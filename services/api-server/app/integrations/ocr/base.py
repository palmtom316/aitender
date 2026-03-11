from abc import ABC, abstractmethod
from pathlib import Path


class OCRAdapter(ABC):
    @abstractmethod
    def extract(self, document_path: Path) -> dict:
        raise NotImplementedError
