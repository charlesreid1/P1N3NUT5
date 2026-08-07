"""Gold Q/A corpus — the plan's acceptance criterion "100% of ~100
test-corpus questions answered with exact agreement."

Each JSON entry declares a tool call and an expected shape of the
response. The runner dispatches to the tool, then walks the `expect`
keys as dotted paths (`payload.hashcat_mode`, `envelope.era_bounds`,
`payload.see_also[].id`) and asserts equality. Two relaxed variants:

  * `expect_contains` — for list fields (assert value is IN the list) or
    string fields (assert substring). Also handles a dotted-path with
    `[]` for iterating a list of dicts and matching against `.id` or
    similar.
  * `expect_min_count` — for tools that return arrays.

Each entry has a `src` field pointing at the bibliography id it was
mined from. Traceability, not a runtime assertion.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from p1n3nut5_mcp import knowledge as kb


CORPUS_PATH = Path(__file__).parent / "corpus" / "gold.json"


def _load_corpus() -> list[dict]:
    with CORPUS_PATH.open() as f:
        return json.load(f)


def _dispatch(tool: str, args: dict) -> dict:
    fn = getattr(kb, tool, None)
    if fn is None:
        raise AssertionError(f"unknown tool {tool!r}")
    return fn(**args)


def _resolve(obj: Any, path: str) -> Any:
    """Walk a dotted path with optional `[]` for iterating a list of dicts.

    `payload.see_also[].id` → for each dict in payload.see_also,
    yield the value at `.id`. Returned as a list.

    Otherwise, plain dotted access. A missing key raises KeyError so
    the failure is diagnosable.
    """
    if "[]" in path:
        head, _, tail = path.partition("[].")
        seq = _resolve(obj, head)
        if not isinstance(seq, list):
            raise AssertionError(f"expected list at {head!r}, got {type(seq).__name__}")
        return [_resolve(item, tail) if tail else item for item in seq]
    cur = obj
    for part in path.split("."):
        if isinstance(cur, dict):
            if part not in cur:
                raise KeyError(f"missing key {part!r} at {path!r}; keys: {list(cur)}")
            cur = cur[part]
        else:
            raise AssertionError(
                f"cannot descend into {type(cur).__name__} at {part!r} (path={path!r})"
            )
    return cur


def _check_expect(response: dict, entry: dict) -> None:
    """Apply expect / expect_contains / expect_min_count assertions."""
    if "expect" in entry:
        for path, want in entry["expect"].items():
            got = _resolve(response, path)
            assert got == want, (
                f"[{entry['id']}] path {path!r}: expected {want!r}, got {got!r}"
            )
    if "expect_contains" in entry:
        for path, want in entry["expect_contains"].items():
            got = _resolve(response, path)
            if isinstance(got, list):
                assert want in got, (
                    f"[{entry['id']}] {path!r}: {want!r} not in {got!r}"
                )
            elif isinstance(got, str):
                assert want in got, (
                    f"[{entry['id']}] {path!r}: substring {want!r} not in {got!r}"
                )
            else:
                raise AssertionError(
                    f"[{entry['id']}] expect_contains against non-list/str at {path!r}: "
                    f"got type {type(got).__name__}"
                )
    if "expect_min_count" in entry:
        count = response.get("count")
        if count is None:
            payload = response.get("payload")
            count = len(payload) if isinstance(payload, list) else None
        assert count is not None, f"[{entry['id']}] no 'count' or list payload"
        assert count >= entry["expect_min_count"], (
            f"[{entry['id']}] expected >= {entry['expect_min_count']}, got {count}"
        )


CORPUS = _load_corpus()


def _corpus_id(entry: dict) -> str:
    return entry["id"]


@pytest.mark.parametrize("entry", CORPUS, ids=[_corpus_id(e) for e in CORPUS])
def test_gold_question(entry: dict) -> None:
    response = _dispatch(entry["tool"], entry["args"])
    assert response.get("ok"), f"[{entry['id']}] tool returned ok=False: {response}"
    _check_expect(response, entry)


def test_gold_corpus_size() -> None:
    """The plan's target is ~100 gold Q/A pairs."""
    assert len(CORPUS) >= 100, f"gold corpus has only {len(CORPUS)} entries"


def test_gold_corpus_unique_ids() -> None:
    ids = [e["id"] for e in CORPUS]
    assert len(ids) == len(set(ids)), "duplicate ids in gold corpus"


def test_gold_corpus_src_resolves() -> None:
    """Every `src` field either is null or resolves to a bibliography id.

    Traceability check — mirrors the discipline in the loader.
    """
    corpus = kb.get_corpus()
    bib_ids = {r.id for r in corpus.category("bibliography")}
    for e in CORPUS:
        src = e.get("src")
        if src is None:
            continue
        assert src in bib_ids, (
            f"[{e['id']}] src={src!r} does not resolve to bibliography.json"
        )
