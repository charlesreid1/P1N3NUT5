"""Loader + citation-integrity contract for `knowledge/records/*.json`.

The loader is the whole authoring safety net — a wrong-order edit
should surface as a load error at test time, not a subtly-wrong tool
response at 2am.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from p1n3nut5_mcp.records import Corpus, RecordLoadError


def test_shipped_corpus_loads_clean() -> None:
    """Every record in the shipped corpus resolves its citations + see_alsos."""
    c = Corpus.load()
    assert len(c.by_id) > 200, "expected the seeded Phase-2 corpus"
    assert "bibliography" in c.by_category
    assert "attack" in c.by_category
    assert "cve" in c.by_category


def test_every_non_bib_record_has_citation(tmp_path: Path) -> None:
    """Non-bibliography records with an empty citations[] must fail to load."""
    (tmp_path / "records").mkdir(exist_ok=True)
    (tmp_path / "records" / "bibliography.json").write_text(
        json.dumps([{"id": "src", "name": "S", "category": "bibliography"}])
    )
    (tmp_path / "records" / "attacks.json").write_text(
        json.dumps([{"id": "bad", "name": "N", "category": "attack", "citations": []}])
    )
    with pytest.raises(RecordLoadError, match="citations\\[\\] must be non-empty"):
        Corpus.load(tmp_path)


def test_citation_must_resolve_to_bibliography(tmp_path: Path) -> None:
    (tmp_path / "records").mkdir(exist_ok=True)
    (tmp_path / "records" / "bibliography.json").write_text(
        json.dumps([{"id": "src", "name": "S", "category": "bibliography"}])
    )
    (tmp_path / "records" / "attacks.json").write_text(
        json.dumps(
            [
                {
                    "id": "a",
                    "name": "A",
                    "category": "attack",
                    "citations": ["nope"],
                }
            ]
        )
    )
    with pytest.raises(RecordLoadError, match="does not resolve to a bibliography.json id"):
        Corpus.load(tmp_path)


def test_see_also_must_resolve(tmp_path: Path) -> None:
    (tmp_path / "records").mkdir(exist_ok=True)
    (tmp_path / "records" / "bibliography.json").write_text(
        json.dumps([{"id": "src", "name": "S", "category": "bibliography"}])
    )
    (tmp_path / "records" / "attacks.json").write_text(
        json.dumps(
            [
                {
                    "id": "a",
                    "name": "A",
                    "category": "attack",
                    "citations": ["src"],
                    "see_also": ["dangling"],
                }
            ]
        )
    )
    with pytest.raises(RecordLoadError, match="see_also"):
        Corpus.load(tmp_path)


def test_era_bounds_must_be_ordered(tmp_path: Path) -> None:
    (tmp_path / "records").mkdir(exist_ok=True)
    (tmp_path / "records" / "bibliography.json").write_text(
        json.dumps([{"id": "src", "name": "S", "category": "bibliography"}])
    )
    (tmp_path / "records" / "attacks.json").write_text(
        json.dumps(
            [
                {
                    "id": "a",
                    "name": "A",
                    "category": "attack",
                    "citations": ["src"],
                    "era_bounds": ["2020", "2010"],
                }
            ]
        )
    )
    with pytest.raises(RecordLoadError, match="era_bounds first"):
        Corpus.load(tmp_path)


def test_bad_confidence_rejected(tmp_path: Path) -> None:
    (tmp_path / "records").mkdir(exist_ok=True)
    (tmp_path / "records" / "bibliography.json").write_text(
        json.dumps([{"id": "src", "name": "S", "category": "bibliography"}])
    )
    (tmp_path / "records" / "attacks.json").write_text(
        json.dumps(
            [
                {
                    "id": "a",
                    "name": "A",
                    "category": "attack",
                    "confidence": "vibes",
                    "citations": ["src"],
                }
            ]
        )
    )
    with pytest.raises(RecordLoadError, match="confidence must be one of"):
        Corpus.load(tmp_path)


def test_duplicate_id_rejected(tmp_path: Path) -> None:
    (tmp_path / "records").mkdir(exist_ok=True)
    (tmp_path / "records" / "bibliography.json").write_text(
        json.dumps([{"id": "src", "name": "S", "category": "bibliography"}])
    )
    (tmp_path / "records" / "attacks.json").write_text(
        json.dumps(
            [
                {"id": "a", "name": "A", "category": "attack", "citations": ["src"]},
                {"id": "a", "name": "A2", "category": "attack", "citations": ["src"]},
            ]
        )
    )
    with pytest.raises(RecordLoadError, match="duplicate record id"):
        Corpus.load(tmp_path)
