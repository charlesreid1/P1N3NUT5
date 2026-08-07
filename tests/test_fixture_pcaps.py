"""Perception tools + fixture pcaps.

The plan step 8: "For every frame_types.json record and every
attacks.json Tier-1 record, ship a small .pcapng fixture under
tests/fixtures/ so the perception tools have a deterministic parse
target."

This test parameterizes over each generated fixture, invokes
parse_pcap, and asserts an expected shape. The `record_id` column
links every fixture back to a real record in the corpus so a
fixture rot / rename shows up here as a fail before it shows up
as a silent gap.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pytest

from p1n3nut5_mcp import detect, knowledge as kb


FIXTURES = Path(__file__).parent / "fixtures" / "pcaps"


@dataclass(frozen=True)
class FixtureSpec:
    filename: str
    record_id: str                          # id in the loaded corpus
    expect_frame_type: str                  # 'management', 'control', 'data'
    expect_subtype: int
    expect_bssid: str
    expect_ssid: str | None
    expect_client: str | None
    label: str                              # pytest-id / short hint


SPECS = (
    FixtureSpec(
        filename="beacon-open.pcap",
        record_id="frame-mgmt-beacon",
        expect_frame_type="management",
        expect_subtype=8,
        expect_bssid="aa:bb:cc:dd:ee:ff",
        expect_ssid="open-net",
        expect_client=None,
        label="beacon-open",
    ),
    FixtureSpec(
        filename="beacon-wpa2.pcap",
        record_id="wpa2-4way-capture",
        expect_frame_type="management",
        expect_subtype=8,
        expect_bssid="11:22:33:44:55:66",
        expect_ssid="wpa2-net",
        expect_client=None,
        label="beacon-wpa2",
    ),
    FixtureSpec(
        filename="beacon-wpa3-sae.pcap",
        record_id="km-wpa3-sae",
        expect_frame_type="management",
        expect_subtype=8,
        expect_bssid="22:33:44:55:66:77",
        expect_ssid="sae-net",
        expect_client=None,
        label="beacon-wpa3-sae",
    ),
    FixtureSpec(
        filename="beacon-wpa3-transition.pcap",
        record_id="wpa3-transition-downgrade",
        expect_frame_type="management",
        expect_subtype=8,
        expect_bssid="33:44:55:66:77:88",
        expect_ssid="transit-net",
        expect_client=None,
        label="beacon-wpa3-transition",
    ),
    FixtureSpec(
        filename="deauth-reason-7.pcap",
        record_id="deauth-targeted",
        expect_frame_type="management",
        expect_subtype=12,
        expect_bssid="aa:bb:cc:dd:ee:ff",
        expect_ssid=None,
        expect_client="11:22:33:44:55:66",
        label="deauth-reason-7",
    ),
    FixtureSpec(
        filename="probe-request-hidden.pcap",
        record_id="frame-mgmt-probe-request",
        expect_frame_type="management",
        expect_subtype=4,
        expect_bssid="ff:ff:ff:ff:ff:ff",
        expect_ssid=None,
        expect_client="11:22:33:44:55:66",
        label="probe-request-hidden",
    ),
    FixtureSpec(
        filename="probe-response-karma.pcap",
        record_id="mana-karma",
        expect_frame_type="management",
        expect_subtype=5,
        expect_bssid="aa:bb:cc:dd:ee:ff",
        expect_ssid="AttendeeHomeNet",
        expect_client="11:22:33:44:55:66",
        label="probe-response-karma",
    ),
)


@pytest.mark.parametrize("spec", SPECS, ids=[s.label for s in SPECS])
def test_fixture_parses(spec: FixtureSpec) -> None:
    path = FIXTURES / spec.filename
    assert path.exists(), (
        f"fixture missing: {path} — run `python scripts/generate-pcap-fixtures.py`"
    )
    summary = detect.parse_pcap(str(path))
    assert summary.total_frames == 1, (
        f"[{spec.label}] expected 1 frame, got {summary.total_frames}"
    )
    assert summary.frame_type_counts[spec.expect_frame_type] == 1, (
        f"[{spec.label}] expected 1 {spec.expect_frame_type} frame, "
        f"got {summary.frame_type_counts!r}"
    )
    assert spec.expect_bssid in summary.bssids, (
        f"[{spec.label}] BSSID {spec.expect_bssid!r} not in {summary.bssids!r}"
    )
    if spec.expect_ssid is not None:
        assert spec.expect_ssid in summary.ssids, (
            f"[{spec.label}] SSID {spec.expect_ssid!r} not in {summary.ssids!r}"
        )
    if spec.expect_client is not None:
        assert spec.expect_client in summary.clients, (
            f"[{spec.label}] client {spec.expect_client!r} not in {summary.clients!r}"
        )


@pytest.mark.parametrize("spec", SPECS, ids=[s.label for s in SPECS])
def test_fixture_record_id_resolves(spec: FixtureSpec) -> None:
    """Every fixture is anchored to a real corpus record — no orphan pcaps."""
    corpus = kb.get_corpus()
    assert spec.record_id in corpus.by_id, (
        f"[{spec.label}] record_id {spec.record_id!r} does not resolve in corpus"
    )


def test_fixture_dir_has_no_orphans() -> None:
    """Every .pcap in the fixtures dir is claimed by a spec."""
    known = {s.filename for s in SPECS}
    on_disk = {p.name for p in FIXTURES.glob("*.pcap")}
    orphans = on_disk - known
    assert not orphans, (
        f"unclaimed fixture pcaps: {orphans}. Add a FixtureSpec or delete."
    )


def test_pcapng_round_trip() -> None:
    """parse_pcap must produce a non-empty summary from a pcapng file.

    T-L5 — regression gate on the L6 scapy-required change. Without
    scapy the old code raised NotImplementedError on pcapng magic;
    with L6 this just works.
    """
    path = FIXTURES / "beacon-open.pcapng"
    assert path.exists(), (
        f"fixture missing: {path} — run `python scripts/generate-pcap-fixtures.py`"
    )
    summary = detect.parse_pcap(str(path))
    assert summary.total_frames >= 1
    assert "aa:bb:cc:dd:ee:ff" in summary.bssids
    assert "open-net" in summary.ssids


def test_generator_is_deterministic(tmp_path: Path) -> None:
    """Running the generator twice produces byte-identical fixtures.

    Guards against future edits that would introduce non-determinism
    (timestamps, random MACs) — the plan's discipline is that fixtures
    are hand-crafted with known contents.
    """
    import subprocess
    import sys

    checked = (
        "beacon-open.pcap",
        "beacon-wpa2.pcap",
        "deauth-reason-7.pcap",
        "beacon-open.pcapng",
    )
    before = {name: (FIXTURES / name).read_bytes() for name in checked}
    subprocess.run(
        [sys.executable, "scripts/generate-pcap-fixtures.py"],
        check=True,
        cwd=Path(__file__).parent.parent,
    )
    after = {name: (FIXTURES / name).read_bytes() for name in checked}
    for name in checked:
        assert before[name] == after[name], (
            f"regenerating {name} produced different bytes — non-deterministic"
        )
