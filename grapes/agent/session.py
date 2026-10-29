import json
import os
import time
import uuid
from pathlib import Path
from typing import TypedDict


class SessionHeader(TypedDict):
    type: str
    version: int
    id: str
    created_at: int


def default_sessions_dir() -> Path:
    base = os.environ.get("XDG_DATA_HOME")
    data_home = Path(base) if base else Path.home() / ".local/share"
    return data_home / "grapes" / "sessions"


class Session:
    def __init__(self, path: Path, header: SessionHeader, entries: list[dict] | None = None) -> None:
        self.path = path
        self.header = header
        self.entries: list[dict] = entries if entries is not None else []

    @property
    def id(self) -> str:
        return self.header["id"]

    def append(self, entry_type: str, data: dict) -> dict:
        seq = len(self.entries) + 1
        entry = {
            "type": entry_type,
            "id": f"e{seq}",
            "parent_id": self.entries[-1]["id"] if self.entries else None,
            "seq": seq,
            "created_at": int(time.time() * 1000),
            "data": data,
        }
        with self.path.open("a") as file:
            file.write(json.dumps(entry) + "\n")
        self.entries.append(entry)
        return entry

    def messages(self) -> list[dict]:
        by_id = {entry["id"]: entry for entry in self.entries}
        current = self.entries[-1] if self.entries else None
        messages: list[dict] = []

        while current is not None:
            if current["type"] == "message":
                messages.append(current["data"])
            parent_id = current["parent_id"]
            current = by_id.get(parent_id) if parent_id else None

        messages.reverse()
        return messages


class SessionStore:
    def __init__(self, root: Path) -> None:
        self.root = root
        self.root.mkdir(parents=True, exist_ok=True)

    def create(self) -> Session:
        session_id = f"ses_{uuid.uuid4().hex[:12]}"
        path = self.root / f"{session_id}.jsonl"
        header: SessionHeader = {
            "type": "session",
            "version": 1,
            "id": session_id,
            "created_at": int(time.time() * 1000),
        }
        path.write_text(json.dumps(header) + "\n")
        return Session(path, header)

    def open(self, session_id: str) -> Session:
        path = self.root / f"{session_id}.jsonl"
        with path.open() as file:
            header: SessionHeader = json.loads(file.readline())
            entries = [json.loads(line) for line in file if line.strip()]
        return Session(path, header, entries)

    def list(self) -> list[SessionHeader]:
        sessions: list[SessionHeader] = []

        for path in self.root.glob("*.jsonl"):
            with path.open() as file:
                header = json.loads(file.readline())
            sessions.append(header)

        sessions.sort(key=lambda header: header["created_at"], reverse=True)
        return sessions
