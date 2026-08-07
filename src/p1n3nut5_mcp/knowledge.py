"""
Knowledge-retrieval MCP tools.

Backs `lookup_standard`, `lookup_channel`, `lookup_frame`, `lookup_ie`,
`lookup_cipher`, `lookup_eap`, `lookup_attack`, `lookup_cve`,
`lookup_hashcat_mode`, `bibliography`, `cross_reference`,
`search_records`, `verify_claim`, and `explain_attack` against the
loaded `knowledge/records/*.json` corpus.

Every tool returns

    {ok, payload, envelope}

where envelope = {citations[], era_bounds, region, confidence}, per
plan-knowledge.md's "Every KR tool response carries" rule. `payload`
is the record body (id + technical fields + notes); no adjectives, no
prose reflow.

Prose corpus tools (`list_topics`, `read_lore`, `search_lore`,
`random_lore`) live below the KR block. They walk
`knowledge/<topic>/*.md` on disk — startup-time discovery, no manifest
maintenance.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from p1n3nut5_mcp.records import (
    Corpus,
    Record,
    RecordLoadError,
    _resolve_root,
)


# ---------------------------------------------------------------------------
# Corpus singleton — loaded lazily so import-time failures don't happen when
# the KR isn't in use.
# ---------------------------------------------------------------------------


_CORPUS: Corpus | None = None


def get_corpus(root: Path | str | None = None, reload: bool = False) -> Corpus:
    """Return the shared Corpus. Reload with reload=True (tests use this)."""
    global _CORPUS
    if reload or _CORPUS is None:
        _CORPUS = Corpus.load(root)
    return _CORPUS


def _wrap(rec: Record | None) -> dict:
    if rec is None:
        return {"ok": False, "payload": None, "envelope": None}
    return {
        "ok": True,
        "payload": {
            "id": rec.id,
            "name": rec.name,
            "category": rec.category,
            "aliases": list(rec.aliases),
            "see_also": list(rec.see_also),
            "disputed": rec.disputed,
            "still_effective_2026": rec.still_effective_2026,
            **rec.body,
        },
        "envelope": rec.envelope(),
    }


def _wrap_many(records: list[Record]) -> dict:
    return {
        "ok": True,
        "payload": [_wrap(r)["payload"] for r in records],
        "count": len(records),
    }


# ---------------------------------------------------------------------------
# lookup_* tools
# ---------------------------------------------------------------------------


def lookup_standard(name: str) -> dict:
    """802.11 amendment or related IETF/IEEE spec."""
    rec = _find_in_category(name, ("standard",))
    return _wrap(rec)


def lookup_channel(number: int, band: float | None = None) -> dict:
    """Channel by number + optional band (2.4/5/6). Ambiguous → 2.4 in the
    1–14 range, 5 for 36–165, 6 for 6 GHz-only numbers.

    Returns the first channel record matching (channel, band). See
    channels.json for the (illustrative) anchor set — full 5 GHz UNII-1..4
    and 6 GHz 1..233 come in Phase 2 completion.
    """
    c = get_corpus()
    for rec in c.category("band_and_channel"):
        tb = rec.body.get("technical_body", {})
        if tb.get("channel") == number:
            if band is None or float(tb.get("band_ghz", 0)) == float(band):
                return _wrap(rec)
    return _wrap(None)


def lookup_frame(type_or_name: str | int, subtype: int | None = None) -> dict:
    """Frame by (type, subtype) or by kebab-case name/alias."""
    c = get_corpus()
    if isinstance(type_or_name, int) and subtype is not None:
        for rec in c.category("frame_type"):
            tb = rec.body.get("technical_body", {})
            if tb.get("frame_type") == type_or_name and tb.get("subtype") == subtype:
                return _wrap(rec)
        return _wrap(None)
    return _wrap(_find_in_category(str(type_or_name), ("frame_type",)))


def lookup_ie(id_or_name: str | int) -> dict:
    """Information Element by numeric ID or by name/alias."""
    c = get_corpus()
    if isinstance(id_or_name, int):
        for rec in c.category("information_element"):
            tb = rec.body.get("technical_body", {})
            if tb.get("element_id") == id_or_name:
                return _wrap(rec)
        return _wrap(None)
    return _wrap(_find_in_category(str(id_or_name), ("information_element",)))


def lookup_cipher(name: str) -> dict:
    return _wrap(_find_in_category(name, ("cipher",)))


def lookup_eap(method: str) -> dict:
    return _wrap(_find_in_category(method, ("eap_method",)))


def lookup_attack(name: str) -> dict:
    return _wrap(_find_in_category(name, ("attack",)))


def lookup_cve(cve_id: str) -> dict:
    """Canonical form CVE-YYYY-NNNN; the record id is the lowercase variant."""
    normalized = cve_id.strip().lower().replace("cve-", "cve-")
    if not normalized.startswith("cve-"):
        normalized = f"cve-{normalized}"
    c = get_corpus()
    rec = c.by_id.get(normalized)
    if rec is None:
        # fall back to alias search
        rec = _find_in_category(cve_id, ("cve",))
    return _wrap(rec)


def lookup_hashcat_mode(name_or_number: str | int) -> dict:
    c = get_corpus()
    if isinstance(name_or_number, int) or (
        isinstance(name_or_number, str) and name_or_number.isdigit()
    ):
        n = int(name_or_number)
        for rec in c.category("hashcat_mode"):
            if rec.body.get("technical_body", {}).get("mode") == n:
                return _wrap(rec)
        return _wrap(None)
    return _wrap(_find_in_category(str(name_or_number), ("hashcat_mode",)))


def bibliography(cite_id: str | None = None) -> dict:
    c = get_corpus()
    if cite_id is None:
        return _wrap_many(c.category("bibliography"))
    rec = c.by_id.get(cite_id)
    return _wrap(rec)


def cross_reference(record_id: str) -> dict:
    """Walk see_also outward one hop. Every referenced record is returned."""
    c = get_corpus()
    root = c.by_id.get(record_id)
    if root is None:
        return {"ok": False, "payload": None}
    linked = [c.by_id[i] for i in root.see_also if i in c.by_id]
    return {
        "ok": True,
        "payload": {
            "record": _wrap(root)["payload"],
            "envelope": root.envelope(),
            "see_also": [_wrap(r)["payload"] for r in linked],
        },
    }


def search_records(
    query: str | None = None,
    category: str | None = None,
    era: str | None = None,
    transport: str | None = None,
) -> dict:
    c = get_corpus()
    hits = c.search(query=query, category=category, era=era, transport=transport)
    return _wrap_many(hits)


# ---------------------------------------------------------------------------
# verify_claim + explain_attack
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class ClaimTrap:
    """Trap catalog entry — plan-knowledge.md § 'Explicitly disputed / ambiguous'."""

    pattern: re.Pattern[str]
    verdict: str
    reason: str
    citations: tuple[str, ...]
    see_also: tuple[str, ...] = ()


_TRAPS: list[ClaimTrap] = [
    ClaimTrap(
        pattern=re.compile(r"pmf.*(prevent|stop|block).*deauth", re.I),
        verdict="needs_qualification",
        reason=(
            "PMF makes broadcast deauth/disassoc ineffective and authenticates the "
            "unicast versions between PMF-capable peers. It does NOT protect unicast "
            "deauth against PMF-disabled clients on a transition-mode AP; "
            "some drivers additionally drop malformed deauths regardless."
        ),
        citations=("ieee-802-11-2020",),
        see_also=("std-802-11w", "deauth-broadcast", "deauth-targeted"),
    ),
    ClaimTrap(
        pattern=re.compile(
            r"wpa3.*(fix|defeat|kill|prevent).*offline.*(dict|crack)", re.I
        ),
        verdict="needs_qualification",
        reason=(
            "WPA3-SAE resists offline dictionary attack in principle. Dragonblood "
            "(Vanhoef+Ronen 2019, CVE-2019-9494/9495) demonstrates side-channel and "
            "timing attacks that partially defeat that resistance on implementations "
            "with weak MODP groups. WPA3 transition mode is also downgradeable to "
            "WPA2 whenever a WPA2-capable client will negotiate it."
        ),
        citations=("vanhoef-dragonblood-2019", "wfa-wpa3-spec"),
        see_also=("km-wpa3-sae", "dragonblood-sidechannel", "wpa3-transition-downgrade"),
    ),
    ClaimTrap(
        pattern=re.compile(r"hid.*(ssid|network).*(secret|secure|hide|protect)", re.I),
        verdict="false",
        reason=(
            "Hidden SSIDs offer no security. Clients that have ever associated to "
            "the network volunteer the SSID in probe requests when they next attempt "
            "to reconnect. The SSID leaks by design."
        ),
        citations=("ieee-802-11-2020",),
        see_also=("def-hidden-ssid-not-secret", "ie-ssid"),
    ),
    ClaimTrap(
        pattern=re.compile(r"pmkid.*(always|every).*(leak|expose)", re.I),
        verdict="false",
        reason=(
            "PMKID leakage is vendor-dependent. Many recent firmwares omit the "
            "PMKID from M1 by default. Records are per-vendor and dated."
        ),
        citations=("steube-pmkid-2018",),
        see_also=("pmkid-capture",),
    ),
    ClaimTrap(
        pattern=re.compile(r"mac.*random.*(prevent|stop).*track", re.I),
        verdict="needs_qualification",
        reason=(
            "MAC randomization defeats naive SSID+MAC correlation but does not "
            "defeat probe-request IE fingerprinting, sequence-number continuity, "
            "or preferred-network-list disclosure. Per-OS behavior varies: iOS 14+ "
            "randomizes per-SSID; Android is vendor-dependent."
        ),
        citations=("ieee-802-11-2020",),
    ),
    ClaimTrap(
        pattern=re.compile(r"wps.*(pixie|pixiedust).*(work|effective).*(every|all)", re.I),
        verdict="false",
        reason=(
            "Pixie Dust is vendor+chipset dependent. Broadcom and Ralink chipsets "
            "were historically vulnerable; MediaTek is variable; recent registrar "
            "entropy patches close it on many current models."
        ),
        citations=("bongard-pixie-2014",),
        see_also=("wps-pixie-dust",),
    ),
    ClaimTrap(
        pattern=re.compile(r"6\s*ghz.*safe.*wpa3", re.I),
        verdict="needs_qualification",
        reason=(
            "6 GHz's WPA3-only mandate closes the WPA2 downgrade door, but "
            "Dragonblood-family side channels still apply where the SAE "
            "implementation is weak. RNR IEs in 2.4/5 GHz beacons also advertise "
            "6 GHz BSSIDs to attackers whose radios can't tune 6 GHz."
        ),
        citations=("wfa-wpa3-6ghz-mandate", "vanhoef-dragonblood-2019"),
        see_also=("rnr-6ghz-enumeration",),
    ),
    ClaimTrap(
        pattern=re.compile(r"kr00k.*only.*old", re.I),
        verdict="needs_qualification",
        reason=(
            "The core Broadcom/Cypress Kr00k (CVE-2019-15126) is largely patched on "
            "flagship phones by 2026 but persists on many IoT endpoints (older Echo, "
            "Kindle, WiFi cameras). The QCA variant (CVE-2020-3702) has a longer tail."
        ),
        citations=("eset-kr00k-2020",),
        see_also=("kr00k-broadcom-cve-2019-15126", "kr00k-qca-cve-2020-3702"),
    ),
    ClaimTrap(
        pattern=re.compile(r"ssid\s*confusion.*need.*(psk|password|key)", re.I),
        verdict="false",
        reason=(
            "SSID Confusion (CVE-2023-52424) works because the SSID is not "
            "authenticated in the 4-way handshake at all. The client is fooled "
            "about which network it is on; the attacker does not need the target "
            "PSK — each side uses whatever key its own network actually has."
        ),
        citations=("vanhoef-yseboodt-ssid-2024",),
        see_also=("ssid-confusion-cve-2023-52424",),
    ),
    ClaimTrap(
        pattern=re.compile(r"reaver.*(always|every).*work", re.I),
        verdict="false",
        reason=(
            "Reaver's success is gated by vendor lockout, WPS-Locked timing, and "
            "Wi-Fi Alliance's WPS deprecation guidance. Still viable on ISP-supplied "
            "routers and some enterprise-branded consumer gear."
        ),
        citations=("viehboeck-wps-2011",),
        see_also=("wps-reaver-online",),
    ),
    ClaimTrap(
        pattern=re.compile(r"deauth.*reason.*7", re.I),
        verdict="true",
        reason=(
            "Deauth reason code 7 is 'class 3 frame received from nonassociated "
            "STA' per IEEE 802.11-2020 §9.4.1.7."
        ),
        citations=("ieee-802-11-2020",),
        see_also=("frame-mgmt-deauth",),
    ),
]


def verify_claim(text: str) -> dict:
    """Grade a natural-language claim against the trap catalog.

    Returns one of `true / false / needs_qualification / unverified`,
    plus reason + citations + see_also. `unverified` means no trap
    matched — this is a coverage gap, not a claim about the truth.
    """
    for trap in _TRAPS:
        if trap.pattern.search(text):
            c = get_corpus()
            return {
                "ok": True,
                "payload": {
                    "verdict": trap.verdict,
                    "reason": trap.reason,
                    "see_also": [
                        _wrap(c.by_id[sid])["payload"]
                        for sid in trap.see_also
                        if sid in c.by_id
                    ],
                },
                "envelope": {
                    "citations": list(trap.citations),
                    "era_bounds": [None, None],
                    "region": "universal",
                    "confidence": "primary",
                },
            }
    return {
        "ok": True,
        "payload": {
            "verdict": "unverified",
            "reason": "No trap catalog match. Add a record and a ClaimTrap for this claim.",
        },
        "envelope": None,
    }


def explain_attack(
    name: str, target_security: str | None = None, era: str | None = None
) -> dict:
    """Return the steps to run an attack.

    Per plan-knowledge.md acceptance criteria: **never refuses on the basis
    of era or target_security**. Both become non-blocking context lines on
    the response envelope. A refusal only happens if the underlying claim
    grades `false` via `verify_claim` — and even then the refusal cites the
    correct alternative.
    """
    rec = _find_in_category(name, ("attack",))
    if rec is None:
        return {
            "ok": False,
            "payload": {"error": f"unknown attack: {name!r}"},
            "envelope": None,
        }

    tb = rec.body.get("technical_body", {})
    context_lines: list[str] = []
    if target_security and target_security not in (rec.body.get("target_security") or []):
        context_lines.append(
            f"target_security={target_security} is outside the record's "
            f"target list {rec.body.get('target_security')}; steps still returned."
        )
    if era and not _era_within(rec.era_bounds, era):
        context_lines.append(
            f"era={era} is outside era_bounds {list(rec.era_bounds)}; "
            "steps still returned per WCTF-ethos policy."
        )

    return {
        "ok": True,
        "payload": {
            "id": rec.id,
            "name": rec.name,
            "preconditions": rec.body.get("preconditions", []),
            "tools": rec.body.get("tools", []),
            "hashcat_mode": rec.body.get("hashcat_mode"),
            "transport": rec.body.get("transport"),
            "mitigation": rec.body.get("mitigation", []),
            "flag_signature": rec.body.get("flag_signature"),
            "caveat": rec.body.get("caveat"),
            "technical_body": tb,
            "context": context_lines,
        },
        "envelope": rec.envelope(),
    }


# ---------------------------------------------------------------------------
# prose corpus tools
# ---------------------------------------------------------------------------


URI_SCHEME = "p1n3nut5"


def _knowledge_root() -> Path:
    """Locate the top-level `knowledge/` directory (parent of `records/`)."""
    r = _resolve_root(None)
    # _resolve_root returns .../knowledge/records; step up.
    return r.parent


def list_topics() -> dict:
    """Enumerate every topic dir + .md file under knowledge/."""
    root = _knowledge_root()
    topics: dict[str, list[str]] = {}
    if not root.exists():
        return {"ok": True, "payload": topics}
    for md in sorted(root.glob("*/*.md")):
        topic = md.parent.name
        topics.setdefault(topic, []).append(md.stem)
    return {"ok": True, "payload": topics}


def read_lore(topic: str, name: str) -> dict:
    """One markdown file's contents. `name` is the file stem (no `.md`)."""
    root = _knowledge_root()
    path = root / topic / f"{name}.md"
    if not path.exists():
        return {"ok": False, "payload": {"error": f"not found: {topic}/{name}"}}
    return {
        "ok": True,
        "payload": {
            "topic": topic,
            "name": name,
            "uri": f"{URI_SCHEME}://{topic}/{name}",
            "text": path.read_text(encoding="utf-8"),
        },
    }


def search_lore(query: str, max_results: int = 20) -> dict:
    """Case-insensitive substring search across every knowledge/*/*.md file."""
    root = _knowledge_root()
    hits: list[dict] = []
    if not root.exists():
        return {"ok": True, "payload": hits}
    needle = query.lower()
    for md in sorted(root.glob("*/*.md")):
        try:
            text = md.read_text(encoding="utf-8")
        except OSError:
            continue
        low = text.lower()
        if needle in low:
            idx = low.index(needle)
            start = max(0, idx - 80)
            end = min(len(text), idx + 80 + len(needle))
            hits.append(
                {
                    "topic": md.parent.name,
                    "name": md.stem,
                    "uri": f"{URI_SCHEME}://{md.parent.name}/{md.stem}",
                    "snippet": text[start:end],
                }
            )
            if len(hits) >= max_results:
                break
    return {"ok": True, "payload": hits}


def random_lore() -> dict:
    """One arbitrary markdown file — for inspiration.

    Deterministic within a process: picks the first sorted file. Callers
    who want cryptographic randomness should draw their own selector.
    """
    root = _knowledge_root()
    if not root.exists():
        return {"ok": False, "payload": {"error": "no knowledge/ directory"}}
    files = sorted(root.glob("*/*.md"))
    if not files:
        return {"ok": False, "payload": {"error": "no markdown files"}}
    md = files[0]
    return read_lore(md.parent.name, md.stem)


# ---------------------------------------------------------------------------
# internals
# ---------------------------------------------------------------------------


def _find_in_category(needle: str, categories: tuple[str, ...]) -> Record | None:
    c = get_corpus()
    want = needle.strip().lower()
    for cat in categories:
        for rec in c.category(cat):
            if rec.id.lower() == want or rec.name.lower() == want:
                return rec
            if any(a.lower() == want for a in rec.aliases):
                return rec
    # Loose fallback — substring on id, useful for CLI-style callers.
    for cat in categories:
        for rec in c.category(cat):
            if want in rec.id.lower() or want in rec.name.lower():
                return rec
    return None


def _era_within(bounds: tuple[str | None, str | None], era: str) -> bool:
    from p1n3nut5_mcp.records import _in_era  # noqa: PLC0415

    return _in_era(bounds, era)


__all__ = [
    "get_corpus",
    "lookup_standard",
    "lookup_channel",
    "lookup_frame",
    "lookup_ie",
    "lookup_cipher",
    "lookup_eap",
    "lookup_attack",
    "lookup_cve",
    "lookup_hashcat_mode",
    "bibliography",
    "cross_reference",
    "search_records",
    "verify_claim",
    "explain_attack",
    "list_topics",
    "read_lore",
    "search_lore",
    "random_lore",
    "RecordLoadError",
]
