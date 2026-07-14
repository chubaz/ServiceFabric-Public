"""FastAPI boundary for the ordinary Research Notes application."""

from __future__ import annotations

import os
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request, status
from pydantic import BaseModel, Field

from research_notes_domain import NoteNotFound, NotesService, SQLiteNoteRepository


class NoteInput(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    body: str = Field(min_length=1, max_length=100_000)


def database_url() -> str:
    """Returns the injected local SQLite binding or a developer-safe default."""
    return os.environ.get(
        "SF_DATABASE_PRIMARY_URL",
        f"sqlite:///{Path(__file__).resolve().parent / 'research-notes.sqlite3'}",
    )


def create_app(database: str | None = None) -> FastAPI:
    """Creates an app with only its public domain-library dependency."""
    service = NotesService(SQLiteNoteRepository(database or database_url()))

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        service.initialize()
        app.state.notes = service
        yield

    api = FastAPI(title="Research Notes", version="0.2.0", lifespan=lifespan)

    def notes(request: Request) -> NotesService:
        return request.app.state.notes

    @api.get("/")
    def home() -> dict[str, str]:
        return {"application": "Research Notes", "status": "ready"}

    @api.get("/health")
    @api.get("/health/ready")
    def health() -> dict[str, str]:
        return {"status": "healthy"}

    @api.post("/notes", status_code=status.HTTP_201_CREATED)
    def create_note(value: NoteInput, request: Request) -> dict[str, object]:
        return notes(request).create(title=value.title, body=value.body).as_dict()

    @api.get("/notes")
    def search_notes(request: Request, query: str = "") -> dict[str, object]:
        return {"notes": [note.as_dict() for note in notes(request).search(query)]}

    @api.get("/notes/{note_id}")
    def get_note(note_id: int, request: Request) -> dict[str, object]:
        try:
            return notes(request).get(note_id).as_dict()
        except NoteNotFound as exc:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="note not found") from exc

    @api.post("/notes/preview")
    def preview_note(value: NoteInput) -> dict[str, int | str]:
        return {
            "title": value.title,
            "character_count": len(value.body),
            "line_count": len(value.body.splitlines()) or 1,
        }

    return api


app = create_app()
