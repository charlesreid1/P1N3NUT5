"""
Typed record loader for `knowledge/records/*.json`.

The KR half of the corpus — dated, cited, region-bound, disputed-aware.
Every record type declared in `plan-knowledge.md § "Records ontology"`
loads through here, and the citation-integrity contract from
`knowledge/records/README.md` is enforced at load time:

  * `citations[]` non-empty; every entry resolves to a
    `bibliography.json` id — loader raises otherwise
  * `era_bounds = [first_effective, last_effective]`; either may be
    null; if both present, first ≤ last
  * `see_also[]` entries resolve to a known record id across the
    entire loaded corpus
  * `id` is unique across the file and unique-per-category across the
    corpus

The lookup helpers below back the `lookup_*` MCP tools; each returns
the corpus envelope

    {citations[], era_bounds, region, confidence}

`plan-knowledge.md § "Explicitly disputed / ambiguous entries"`
declares the traps `verify_claim` must grade; those come from the
records themselves via each record's `disputed:` field.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path
from typing import Any, Iterable


CONFIDENCE_LEVELS = ("primary", "secondary", "community", "folklore")

# File name → category tag used in the record envelope + validation.
# Every file below is optional; the loader tolerates absence so early
# authoring phases (Layer 0 → Layer 4) leave the corpus in a
# validator-clean state per plan-knowledge.md § "Authoring order".
RECORD_FILES: dict[str, str] = {
    "bibliography.json": "bibliography",
    "standards.json": "standard",
    "channels.json": "band_and_channel",
    "hashcat_modes.json": "hashcat_mode",
    "frame_types.json": "frame_type",
    "ies.json": "information_element",
    "security_suites.json": "key_management",  # or "cipher"
    "eap_methods.json": "eap_method",
    "cves.json": "cve",
    "attacks.json": "attack",
    "pineapple_endpoints.json": "pineapple_endpoint",
    "openwrt_uci.json": "openwrt_uci",
    "defense_and_detection.json": "defense_and_detection",
    "karma_family.json": "karma_family",
    "roaming.json": "roaming",
    "dos.json": "dos",
    "chipset_vulns.json": "chipset_vuln",
    "client_fingerprints.json": "client_fingerprint",
    "default_psks.json": "default_psk",
}


class RecordLoadError(RuntimeError):
    """Raised on schema violations, missing citations, dangling see_also."""


@dataclass(frozen=True)
class Record:
    """A single typed record. All KR tools return one of these + envelope."""

    id: str
    name: str
    category: str
    aliases: tuple[str, ...] = ()
    region: str = "universal"
    era_bounds: tuple[str | None, str | None] = (None, None)
    still_effective_2026: bool | None = None
    confidence: str = "community"
    citations: tuple[str, ...] = ()
    see_also: tuple[str, ...] = ()
    disputed: dict[str, str] = field(default_factory=dict)
    body: dict[str, Any] = field(default_factory=dict)
    """Everything else — technical_body, preconditions, tools, ..."""

    def envelope(self) -> dict:
        """The {citations, era_bounds, region, confidence} response envelope
        the plan mandates for every KR tool response."""
        return {
            "citations": list(self.citations),
            "era_bounds": list(self.era_bounds),
            "region": self.region,
            "confidence": self.confidence,
        }


# Fields the record dataclass promotes to first-class attributes. Every
# other key goes into `body`.
_TOP_FIELDS = {
    "id",
    "name",
    "category",
    "aliases",
    "region",
    "era_bounds",
    "still_effective_2026",
    "confidence",
    "citations",
    "see_also",
    "disputed",
}


@dataclass
class Corpus:
    """The whole loaded KR. Held by lookup helpers + MCP tools."""

    by_id: dict[str, Record]
    by_category: dict[str, list[Record]]
    root: Path

    @classmethod
    def load(cls, root: Path | str | None = None) -> "Corpus":
        r = _resolve_root(root)
        by_id: dict[str, Record] = {}
        by_category: dict[str, list[Record]] = {}

        # Pass 1 — load + shape-validate every file. Cross-file link
        # checks (citation targets, see_also targets) run in pass 2.
        for fname, default_category in RECORD_FILES.items():
            path = r / fname
            if not path.exists():
                continue
            raw = _read_json(path)
            if not isinstance(raw, list):
                raise RecordLoadError(f"{fname}: expected top-level JSON array")
            for i, obj in enumerate(raw):
                rec = _to_record(obj, default_category, source=f"{fname}[{i}]")
                if rec.id in by_id:
                    raise RecordLoadError(
                        f"duplicate record id {rec.id!r} in {fname}[{i}] "
                        f"(also in earlier record)"
                    )
                by_id[rec.id] = rec
                by_category.setdefault(rec.category, []).append(rec)

        # Pass 2 — link integrity. Every citation resolves to a
        # bibliography id; every see_also resolves to any record id.
        _link_check(by_id, by_category)

        return cls(by_id=by_id, by_category=by_category, root=r)

    # --- lookup helpers ----------------------------------------------------

    def get(self, record_id: str) -> Record | None:
        return self.by_id.get(record_id)

    def get_required(self, record_id: str) -> Record:
        rec = self.by_id.get(record_id)
        if rec is None:
            raise KeyError(record_id)
        return rec

    def by_alias(self, needle: str) -> Record | None:
        """Case-insensitive match against id, name, or aliases."""
        want = needle.strip().lower()
        for rec in self.by_id.values():
            if rec.id.lower() == want or rec.name.lower() == want:
                return rec
            if any(a.lower() == want for a in rec.aliases):
                return rec
        return None

    def category(self, cat: str) -> list[Record]:
        return list(self.by_category.get(cat, ()))

    def search(
        self,
        query: str | None = None,
        category: str | None = None,
        era: str | None = None,
        transport: str | None = None,
    ) -> list[Record]:
        results: Iterable[Record] = self.by_id.values()
        if category:
            results = (r for r in results if r.category == category)
        if transport:
            results = (r for r in results if r.body.get("transport") == transport)
        if era:
            results = (r for r in results if _in_era(r.era_bounds, era))
        if query:
            needle = query.lower()

            def _hit(r: Record) -> bool:
                blob = " ".join(
                    (
                        r.id,
                        r.name,
                        " ".join(r.aliases),
                        json.dumps(r.body, sort_keys=True, default=str),
                    )
                ).lower()
                return needle in blob

            results = (r for r in results if _hit(r))
        return list(results)


# ---------------------------------------------------------------------------
# internal helpers
# ---------------------------------------------------------------------------


def _resolve_root(root: Path | str | None) -> Path:
    """Locate `knowledge/records`.

    Search order:
      1. explicit `root=`
      2. `$P1N3NUT5_KNOWLEDGE` if set (points at `knowledge/`)
      3. `<package>/../../knowledge/records` for a dev checkout
      4. `<package>/_knowledge/records` for the packaged wheel layout
         (see `pyproject.toml [tool.hatch.build.targets.wheel.force-
         include]` — the whole `knowledge/` tree gets bundled as
         `_knowledge/`).
    """
    if root is not None:
        p = Path(root)
        return p / "records" if p.name != "records" else p
    import os as _os  # noqa: PLC0415

    env = _os.environ.get("P1N3NUT5_KNOWLEDGE")
    if env:
        p = Path(env)
        return p / "records" if p.name != "records" else p
    here = Path(__file__).resolve().parent
    for candidate in (
        here.parent.parent / "knowledge" / "records",
        here / "_knowledge" / "records",
    ):
        if candidate.exists():
            return candidate
    # Fall back to the dev layout even if empty — Corpus.load will just
    # produce an empty corpus, not crash.
    return here.parent.parent / "knowledge" / "records"


def _read_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        raise RecordLoadError(f"{path}: JSON decode error: {e}") from e


def _to_record(obj: Any, default_category: str, source: str) -> Record:
    if not isinstance(obj, dict):
        raise RecordLoadError(f"{source}: record must be a JSON object")
    rid = obj.get("id")
    name = obj.get("name")
    if not isinstance(rid, str) or not rid:
        raise RecordLoadError(f"{source}: missing 'id' string")
    if not isinstance(name, str) or not name:
        raise RecordLoadError(f"{source}: {rid}: missing 'name' string")
    category = obj.get("category", default_category)
    if not isinstance(category, str) or not category:
        raise RecordLoadError(f"{source}: {rid}: 'category' must be a non-empty string")

    aliases = _string_tuple(obj.get("aliases", ()), f"{source}: {rid}: aliases")
    citations = _string_tuple(obj.get("citations", ()), f"{source}: {rid}: citations")
    see_also = _string_tuple(obj.get("see_also", ()), f"{source}: {rid}: see_also")
    region = obj.get("region", "universal")
    if not isinstance(region, str):
        raise RecordLoadError(f"{source}: {rid}: region must be a string")
    era = _validate_era_bounds(obj.get("era_bounds"), f"{source}: {rid}")
    conf = obj.get("confidence", "community")
    if conf not in CONFIDENCE_LEVELS:
        raise RecordLoadError(
            f"{source}: {rid}: confidence must be one of {CONFIDENCE_LEVELS}, "
            f"got {conf!r}"
        )
    still_2026 = obj.get("still_effective_2026")
    if still_2026 is not None and not isinstance(still_2026, bool):
        raise RecordLoadError(
            f"{source}: {rid}: still_effective_2026 must be bool or omitted"
        )
    disputed = obj.get("disputed", {})
    if not isinstance(disputed, dict):
        raise RecordLoadError(f"{source}: {rid}: disputed must be an object")

    # bibliography records are the only ones exempt from the citations-
    # required rule; everything else needs at least one entry.
    if category != "bibliography" and not citations:
        raise RecordLoadError(
            f"{source}: {rid}: citations[] must be non-empty (no primary cite, "
            f"no record loads — see knowledge/records/README.md)"
        )

    body = {k: v for k, v in obj.items() if k not in _TOP_FIELDS}

    return Record(
        id=rid,
        name=name,
        category=category,
        aliases=aliases,
        region=region,
        era_bounds=era,
        still_effective_2026=still_2026,
        confidence=conf,
        citations=citations,
        see_also=see_also,
        disputed=disputed,
        body=body,
    )


def _string_tuple(v: Any, ctx: str) -> tuple[str, ...]:
    if v is None:
        return ()
    if isinstance(v, tuple):
        # Callers pass () as the default; only lists actually appear in JSON.
        v = list(v)
    if not isinstance(v, list):
        raise RecordLoadError(f"{ctx}: expected list, got {type(v).__name__}")
    out: list[str] = []
    for i, item in enumerate(v):
        if not isinstance(item, str) or not item:
            raise RecordLoadError(f"{ctx}[{i}]: must be non-empty string")
        out.append(item)
    return tuple(out)


_ISO_DATE = re.compile(r"^\d{4}(-\d{2}(-\d{2})?)?$")


def _validate_era_bounds(
    v: Any, ctx: str
) -> tuple[str | None, str | None]:
    if v is None:
        return (None, None)
    if not isinstance(v, list) or len(v) != 2:
        raise RecordLoadError(
            f"{ctx}: era_bounds must be [first_effective, last_effective]"
        )
    first, last = v
    for end, label in ((first, "era_bounds[0]"), (last, "era_bounds[1]")):
        if end is None:
            continue
        if not isinstance(end, str) or not _ISO_DATE.match(end):
            raise RecordLoadError(
                f"{ctx}: {label} must be an ISO date (YYYY, YYYY-MM, "
                f"YYYY-MM-DD) or null, got {end!r}"
            )
    if first and last:
        f = _parse_partial_iso(first)
        l = _parse_partial_iso(last)
        if f and l and f > l:
            raise RecordLoadError(
                f"{ctx}: era_bounds first ({first}) must be <= last ({last})"
            )
    return (first, last)


def _parse_partial_iso(s: str) -> date | None:
    parts = s.split("-")
    try:
        y = int(parts[0])
        m = int(parts[1]) if len(parts) > 1 else 1
        d = int(parts[2]) if len(parts) > 2 else 1
        return date(y, m, d)
    except (ValueError, IndexError):
        return None


def _in_era(bounds: tuple[str | None, str | None], era: str) -> bool:
    """`era` is a year or full ISO date; return True if it lies within bounds
    (unbounded ends match any date on that side)."""
    e = _parse_partial_iso(era)
    if e is None:
        return False
    first = _parse_partial_iso(bounds[0]) if bounds[0] else None
    last = _parse_partial_iso(bounds[1]) if bounds[1] else None
    if first and e < first:
        return False
    if last and e > last:
        return False
    return True


def _link_check(
    by_id: dict[str, Record], by_category: dict[str, list[Record]]
) -> None:
    bib_ids = {r.id for r in by_category.get("bibliography", ())}
    # If a corpus loads *without* a bibliography file yet (early Phase-2
    # slice), skip citation resolution. The intent is that Layer-0
    # bibliography lands first; once it exists, everything downstream is
    # checked strictly.
    check_citations = bool(bib_ids)
    for rec in by_id.values():
        if check_citations:
            for cite in rec.citations:
                if cite not in bib_ids:
                    raise RecordLoadError(
                        f"{rec.id}: citation {cite!r} does not resolve to a "
                        f"bibliography.json id"
                    )
        for other in rec.see_also:
            if other not in by_id:
                raise RecordLoadError(
                    f"{rec.id}: see_also {other!r} does not resolve to a "
                    f"known record id"
                )
