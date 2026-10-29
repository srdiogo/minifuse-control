"""Private application preferences and uncertain-operation references."""

import json
import os
import secrets
from pathlib import Path


class Preferences:
    def __init__(self, path=None):
        root = Path(os.environ.get("XDG_CONFIG_HOME") or Path.home() / ".config")
        self.path = Path(path) if path else root / "minifuse/desktop.json"
        self.data = {"activation_target": "disabled"}
        if self.path.exists():
            with self.path.open("rb") as stream:
                content = stream.read(65537)
            if len(content) > 65536:
                raise ValueError("Preferences exceed their size limit")
            stored = json.loads(content)
            if not isinstance(stored, dict):
                raise ValueError("Preferences must be an object")
            self.data.update(stored)

    def save(self):
        self.path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        temporary = self.path.with_name(f".{self.path.name}.{secrets.token_hex(8)}")
        fd = os.open(temporary, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
        with os.fdopen(fd, "w") as stream:
            json.dump(self.data, stream, allow_nan=False, indent=2)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, self.path)
        directory = os.open(self.path.parent, os.O_RDONLY | os.O_DIRECTORY)
        try:
            os.fsync(directory)
        finally:
            os.close(directory)
