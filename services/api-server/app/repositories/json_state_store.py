import json
from pathlib import Path
from typing import Callable


class JsonStateStore:
    def __init__(self, path: Path) -> None:
        self.path = path

    def load(self, *, default_factory: Callable[[], dict]) -> dict:
        if not self.path.exists():
            state = default_factory()
            self.save(state)
            return state

        return json.loads(self.path.read_text())

    def save(self, state: dict) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(
            json.dumps(state, indent=2, sort_keys=True),
        )

    def reset(self) -> None:
        if self.path.exists():
            self.path.unlink()
