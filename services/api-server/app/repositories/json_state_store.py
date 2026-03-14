import json
from pathlib import Path
from threading import RLock
from typing import Callable


class JsonStateStore:
    _locks: dict[str, RLock] = {}

    def __init__(self, path: Path) -> None:
        self.path = path
        self._lock = self._locks.setdefault(str(path), RLock())

    def load(self, *, default_factory: Callable[[], dict]) -> dict:
        with self._lock:
            if not self.path.exists():
                state = default_factory()
                self.save(state)
                return state

            return json.loads(self.path.read_text())

    def save(self, state: dict) -> None:
        with self._lock:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            temp_path = self.path.with_suffix(f"{self.path.suffix}.tmp")
            temp_path.write_text(
                json.dumps(state, indent=2, sort_keys=True),
            )
            temp_path.replace(self.path)

    def reset(self) -> None:
        with self._lock:
            if self.path.exists():
                self.path.unlink()
