"""Portable note business rules and SQLite persistence implementation."""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path


class ValidationError(ValueError):
    """Raised when a note violates the public domain constraints."""


class NoteNotFound(LookupError):
    """Raised when a requested note does not exist."""


@dataclass(frozen=True)
class Note:
    id: int
    title: str
    body: str
    created_at: str

    def as_dict(self) -> dict[str, object]:
        return {"id": self.id, "title": self.title, "body": self.body, "created_at": self.created_at}


class SQLiteNoteRepository:
    """A small application-local SQLite repository with no runtime ownership."""

    def __init__(self, url: str) -> None:
        self.path = self._path_from_url(url)

    @staticmethod
    def _path_from_url(url: str) -> str:
        prefix = "sqlite:///"
        if not url.startswith(prefix):
            raise ValueError("Research Notes requires a sqlite:/// database binding")
        path = url.removeprefix(prefix)
        if not path or path == ":memory:":
            return ":memory:"
        return str(Path(path).expanduser())

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.path)
        connection.row_factory = sqlite3.Row
        return connection

    def initialize(self) -> None:
        if self.path != ":memory:":
            Path(self.path).parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as connection:
            connection.execute(
                """CREATE TABLE IF NOT EXISTS notes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    body TEXT NOT NULL,
                    created_at TEXT NOT NULL
                )"""
            )

    def create(self, title: str, body: str) -> Note:
        created_at = datetime.now(UTC).isoformat()
        with self._connect() as connection:
            cursor = connection.execute(
                "INSERT INTO notes (title, body, created_at) VALUES (?, ?, ?)",
                (title, body, created_at),
            )
            note_id = int(cursor.lastrowid)
        return Note(id=note_id, title=title, body=body, created_at=created_at)

    def get(self, note_id: int) -> Note:
        with self._connect() as connection:
            row = connection.execute(
                "SELECT id, title, body, created_at FROM notes WHERE id = ?", (note_id,)
            ).fetchone()
        if row is None:
            raise NoteNotFound(note_id)
        return Note(**dict(row))

    def search(self, query: str) -> list[Note]:
        pattern = query.strip().lower()
        with self._connect() as connection:
            rows = connection.execute(
                """SELECT id, title, body, created_at FROM notes
                   WHERE ? = '' OR instr(lower(title), ?) > 0 OR instr(lower(body), ?) > 0
                   ORDER BY id DESC""",
                (pattern, pattern, pattern),
            ).fetchall()
        return [Note(**dict(row)) for row in rows]


class NotesService:
    """Public business interface shared by the HTTP and future capability adapters."""

    def __init__(self, repository: SQLiteNoteRepository) -> None:
        self._repository = repository

    def initialize(self) -> None:
        self._repository.initialize()

    def create(self, *, title: str, body: str) -> Note:
        title, body = title.strip(), body.strip()
        if not title:
            raise ValidationError("title must not be blank")
        if not body:
            raise ValidationError("body must not be blank")
        return self._repository.create(title, body)

    def get(self, note_id: int) -> Note:
        return self._repository.get(note_id)

    def search(self, query: str = "") -> list[Note]:
        return self._repository.search(query)
