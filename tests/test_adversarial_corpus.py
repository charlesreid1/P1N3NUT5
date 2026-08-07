"""Adversarial trap corpus — the plan's acceptance criterion
"100% of trap questions result in verify_claim returning `false` or
`needs_qualification` with citations to the correct record."

Runs every entry in `tests/corpus/adversarial.json` through
`verify_claim` and asserts the verdict + citation.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from p1n3nut5_mcp import knowledge as kb


CORPUS_PATH = Path(__file__).parent / "corpus" / "adversarial.json"


def _load() -> list[dict]:
    with CORPUS_PATH.open() as f:
        return json.load(f)


CORPUS = _load()


def _corpus_id(entry: dict) -> str:
    return entry["id"]


@pytest.mark.parametrize("entry", CORPUS, ids=[_corpus_id(e) for e in CORPUS])
def test_adversarial_verdict(entry: dict) -> None:
    r = kb.verify_claim(entry["q"])
    assert r.get("ok"), f"[{entry['id']}] verify_claim returned ok=False: {r}"
    verdict = r["payload"]["verdict"]
    assert verdict == entry["want_verdict"], (
        f"[{entry['id']}] verdict={verdict!r}, wanted {entry['want_verdict']!r}; "
        f"claim={entry['q']!r}"
    )
    want_cite = entry.get("cite_must_include")
    if want_cite is None:
        # unverified traps have no envelope
        assert r.get("envelope") is None, (
            f"[{entry['id']}] expected null envelope for unverified, got {r['envelope']!r}"
        )
    else:
        envelope = r.get("envelope") or {}
        cites = envelope.get("citations", [])
        assert want_cite in cites, (
            f"[{entry['id']}] missing citation {want_cite!r}; got {cites!r}"
        )


def test_adversarial_corpus_size() -> None:
    """The plan target is ~40 trap questions."""
    assert len(CORPUS) >= 40, f"adversarial corpus has only {len(CORPUS)} entries"


def test_adversarial_corpus_unique_ids() -> None:
    ids = [e["id"] for e in CORPUS]
    assert len(ids) == len(set(ids)), "duplicate ids in adversarial corpus"


def test_every_non_null_citation_resolves() -> None:
    """Every cite_must_include either is null or resolves to bibliography.json."""
    corpus = kb.get_corpus()
    bib_ids = {r.id for r in corpus.category("bibliography")}
    for e in CORPUS:
        c = e.get("cite_must_include")
        if c is None:
            continue
        assert c in bib_ids, (
            f"[{e['id']}] cite_must_include={c!r} does not resolve to bibliography.json"
        )
