"""Ordinary FastAPI Text Utility application with an additive capability adapter."""

from __future__ import annotations

import re

from fastapi import FastAPI
from pydantic import BaseModel, Field


app = FastAPI(title="Text Utility", version="1.0.0")


class TextInput(BaseModel):
    text: str = Field(min_length=1, max_length=100_000)


def words(text: str) -> list[str]:
    return re.findall(r"[\w']+", text, flags=re.UNICODE)


@app.get("/")
def home() -> dict[str, str]:
    return {"application": "Text Utility", "status": "ready"}


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "healthy"}


@app.post("/actions/count-words")
def count_words(value: TextInput) -> dict[str, int]:
    return {"word_count": len(words(value.text))}


@app.post("/actions/inspect")
def inspect_text(value: TextInput) -> dict[str, int]:
    return {
        "word_count": len(words(value.text)),
        "character_count": len(value.text),
        "line_count": len(value.text.splitlines()) or 1,
    }
