"""Depth-pass acceptance tests (Phase D6 T1–T5).

Lock in the per-record depth authored in `plan-improve-docs.md` phases
D1–D5 so a future edit that regresses the corpus fails loudly.

Categories:
  T1 — every attacks.json record has flag_signature, mitigation,
       preconditions (>=2), tools (>=2).
  T2 — every frame_types.json + ies.json record has a non-empty
       fields[]/layout[] (placeholder or authored).
  T3 — every eap_methods.json record has a non-empty attacks[] and
       every id resolves to attacks.json.
  T4 — every hashcat_modes.json record has technical_body.example_command.
  T5 — the acceptance-criteria manifest (below) is met.

The manifest is expressed inline as a small dict so the criteria are
readable and version-controlled alongside the tests.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest


RECORDS = Path(__file__).resolve().parent.parent / "knowledge" / "records"


def _load(name: str) -> list[dict]:
    return json.loads((RECORDS / name).read_text(encoding="utf-8"))


# ---------------------------------------------------------------------------
# T1 — attacks.json depth
# ---------------------------------------------------------------------------


ATTACKS = _load("attacks.json")


@pytest.mark.parametrize("rec", ATTACKS, ids=lambda r: r["id"])
def test_attack_has_flag_signature(rec: dict) -> None:
    """Either a string describing the WCTF-flag shape or explicit null."""
    assert "flag_signature" in rec, (
        f"{rec['id']}: no flag_signature (must be string or null)"
    )
    fs = rec["flag_signature"]
    assert fs is None or isinstance(fs, str), (
        f"{rec['id']}: flag_signature must be string or null, got {type(fs).__name__}"
    )


@pytest.mark.parametrize("rec", ATTACKS, ids=lambda r: r["id"])
def test_attack_has_mitigation(rec: dict) -> None:
    """List of bullets or explicit null. Never absent."""
    assert "mitigation" in rec, f"{rec['id']}: no mitigation field"
    m = rec["mitigation"]
    assert m is None or (
        isinstance(m, list) and all(isinstance(x, str) and x for x in m)
    ), f"{rec['id']}: mitigation must be list[str] or null, got {m!r}"


@pytest.mark.parametrize("rec", ATTACKS, ids=lambda r: r["id"])
def test_attack_preconditions_depth(rec: dict) -> None:
    precs = rec.get("preconditions") or []
    assert len(precs) >= 2, (
        f"{rec['id']}: preconditions must have >= 2 bullets, got {len(precs)}: {precs}"
    )


@pytest.mark.parametrize("rec", ATTACKS, ids=lambda r: r["id"])
def test_attack_tools_depth(rec: dict) -> None:
    tools = rec.get("tools") or []
    assert len(tools) >= 2, (
        f"{rec['id']}: tools must have >= 2 bullets, got {len(tools)}: {tools}"
    )


# ---------------------------------------------------------------------------
# T2 — frame_types + ies layouts
# ---------------------------------------------------------------------------


FRAMES = _load("frame_types.json")
IES = _load("ies.json")


@pytest.mark.parametrize("rec", FRAMES, ids=lambda r: r["id"])
def test_frame_has_fields_layout(rec: dict) -> None:
    tb = rec.get("technical_body") or {}
    fields = tb.get("fields") or []
    assert fields, f"{rec['id']}: technical_body.fields[] must be non-empty"
    for f in fields:
        assert "name" in f, f"{rec['id']}: field entry missing 'name': {f!r}"


@pytest.mark.parametrize("rec", IES, ids=lambda r: r["id"])
def test_ie_has_layout(rec: dict) -> None:
    tb = rec.get("technical_body") or {}
    layout = tb.get("layout") or []
    assert layout, f"{rec['id']}: technical_body.layout[] must be non-empty"
    for f in layout:
        assert "name" in f, f"{rec['id']}: layout entry missing 'name': {f!r}"


# ---------------------------------------------------------------------------
# T3 — eap_methods back-references resolve to attacks.json
# ---------------------------------------------------------------------------


EAP_METHODS = _load("eap_methods.json")
_ATTACK_IDS = {r["id"] for r in ATTACKS}


@pytest.mark.parametrize("rec", EAP_METHODS, ids=lambda r: r["id"])
def test_eap_has_attacks_backref(rec: dict) -> None:
    tb = rec.get("technical_body") or {}
    attacks = tb.get("attacks")
    assert attacks is not None, f"{rec['id']}: technical_body.attacks missing"
    assert isinstance(attacks, list), f"{rec['id']}: technical_body.attacks must be a list"
    assert attacks, f"{rec['id']}: technical_body.attacks must be non-empty"
    for aid in attacks:
        assert aid in _ATTACK_IDS, (
            f"{rec['id']}: attacks[] id {aid!r} does not resolve to attacks.json"
        )


# ---------------------------------------------------------------------------
# T4 — hashcat_modes example commands
# ---------------------------------------------------------------------------


HASHCAT_MODES = _load("hashcat_modes.json")


@pytest.mark.parametrize("rec", HASHCAT_MODES, ids=lambda r: r["id"])
def test_hashcat_mode_has_example_command(rec: dict) -> None:
    tb = rec.get("technical_body") or {}
    cmd = tb.get("example_command")
    assert cmd, f"{rec['id']}: technical_body.example_command must be non-empty"
    assert isinstance(cmd, str) and cmd.strip(), (
        f"{rec['id']}: example_command must be a non-empty string"
    )


# ---------------------------------------------------------------------------
# T5 — acceptance-criteria roll-up
# ---------------------------------------------------------------------------


ENDPOINTS = _load("pineapple_endpoints.json")
LOCAL_OPS = _load("local_operations.json")


ACCEPTANCE = {
    "attacks_min": 90,          # Appendix B floor; corpus is now 98
    "frames_min": 30,           # ontology floor; corpus is 40
    "ies_min": 80,              # ontology floor; corpus is 86 (80 + 6 ANQP)
    "eap_methods_min": 30,      # ontology floor; corpus is 30
    "hashcat_modes_min": 30,    # ontology floor; corpus is 30
    "endpoints_firmware_min_coverage": 1.0,  # 100% of pineapple_endpoints
    "endpoints_iface_coverage": 1.0,         # 100% have api or ssh populated
    "local_ops_min": 11,        # everything carved out
}


def test_acceptance_attacks_count() -> None:
    assert len(ATTACKS) >= ACCEPTANCE["attacks_min"], (
        f"attacks.json has {len(ATTACKS)}, floor is {ACCEPTANCE['attacks_min']}"
    )


def test_acceptance_frames_count() -> None:
    assert len(FRAMES) >= ACCEPTANCE["frames_min"]


def test_acceptance_ies_count() -> None:
    assert len(IES) >= ACCEPTANCE["ies_min"]


def test_acceptance_eap_methods_count() -> None:
    assert len(EAP_METHODS) >= ACCEPTANCE["eap_methods_min"]


def test_acceptance_hashcat_modes_count() -> None:
    assert len(HASHCAT_MODES) >= ACCEPTANCE["hashcat_modes_min"]


def test_acceptance_endpoints_firmware_min_coverage() -> None:
    have_fw = sum(1 for r in ENDPOINTS if r.get("firmware_min"))
    coverage = have_fw / len(ENDPOINTS) if ENDPOINTS else 0.0
    assert coverage >= ACCEPTANCE["endpoints_firmware_min_coverage"], (
        f"{have_fw}/{len(ENDPOINTS)} endpoints have firmware_min; "
        f"coverage {coverage:.2%} < {ACCEPTANCE['endpoints_firmware_min_coverage']:.2%}"
    )


def test_acceptance_endpoints_iface_coverage() -> None:
    have_iface = sum(1 for r in ENDPOINTS if r.get("api") or r.get("ssh"))
    coverage = have_iface / len(ENDPOINTS) if ENDPOINTS else 0.0
    assert coverage >= ACCEPTANCE["endpoints_iface_coverage"], (
        f"{have_iface}/{len(ENDPOINTS)} endpoints have api/ssh; "
        f"coverage {coverage:.2%}"
    )


def test_acceptance_local_ops_count() -> None:
    assert len(LOCAL_OPS) >= ACCEPTANCE["local_ops_min"], (
        f"local_operations.json has {len(LOCAL_OPS)}, floor is "
        f"{ACCEPTANCE['local_ops_min']}"
    )
