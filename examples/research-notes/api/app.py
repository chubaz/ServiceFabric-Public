"""Ordinary FastAPI Research Notes application fixture."""

from __future__ import annotations

from fastapi import FastAPI
from pydantic import BaseModel, Field


app = FastAPI(title="Research Notes", version="0.1.0")


class NoteInput(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    body: str = Field(min_length=1, max_length=100_000)


@app.get("/")
def home() -> dict[str, str]:
    return {"application": "Research Notes", "status": "ready"}


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "healthy"}


@app.post("/notes/preview")
def preview_note(value: NoteInput) -> dict[str, int | str]:
    return {
        "title": value.title,
        "character_count": len(value.body),
        "line_count": len(value.body.splitlines()) or 1,
    }
