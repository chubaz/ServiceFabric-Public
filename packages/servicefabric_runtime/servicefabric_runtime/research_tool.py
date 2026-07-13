"""Deterministic local fixture for the reviewed research provider boundary."""

from __future__ import annotations


PAPERS = (
    {
        "id": "paper.retrieval-augmentation",
        "title": "Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks",
        "year": 2020,
    },
    {
        "id": "paper.transformer",
        "title": "Attention Is All You Need",
        "year": 2017,
    },
)


def search_papers(arguments: dict[str, object]) -> dict[str, object]:
    query = arguments.get("query")
    maximum_results = arguments.get("maximum_results", 5)
    if not isinstance(query, str) or not query.strip() or len(query) > 500:
        raise ValueError("query must be a non-empty bounded string")
    if not isinstance(maximum_results, int) or isinstance(maximum_results, bool):
        raise ValueError("maximum_results must be an integer")
    if not 1 <= maximum_results <= 20:
        raise ValueError("maximum_results must be between 1 and 20")
    return {"query": query.strip(), "papers": list(PAPERS[:maximum_results])}
