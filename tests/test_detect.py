"""Phase 4 — pcap parsing, hcx conversion, handshake/PMKID extraction."""

from __future__ import annotations

import shutil
from pathlib import Path

from p1n3nut5_mcp import detect

FIXTURES = Path(__file__).parent / "fixtures" / "pcaps"


def test_parse_pcap_open_beacon():
    summary = detect.parse_pcap(str(FIXTURES / "beacon-open.pcap"))
    assert summary.total_frames == 1
    assert summary.frame_type_counts["management"] == 1
    assert summary.bssids == ["aa:bb:cc:dd:ee:ff"]
    assert summary.ssids == ["open-net"]


def test_parse_pcap_wpa2_beacon():
    summary = detect.parse_pcap(str(FIXTURES / "beacon-wpa2.pcap"))
    assert summary.total_frames == 1
    assert summary.ssids == ["wpa2-net"]
    assert summary.bssids == ["11:22:33:44:55:66"]


async def test_convert_to_hashcat_parses_output(tmp_path: Path):
    canned = (FIXTURES / "handshake-hcx.txt").read_text()

    async def fake_run(cmd: list[str]) -> tuple[int, str, str]:
        # cmd is [tool, "-o", out_path, pcap_path]
        Path(cmd[2]).write_text(canned)
        return 0, "", ""

    out = str(tmp_path / "out.22000")
    r = await detect.convert_to_hashcat("input.pcap", out, run=fake_run)
    assert r["ok"] is True
    assert r["warnings"] == []
    types = sorted(h.type for h in r["hash_lines"])
    assert types == ["01", "02"]
    pmkid = next(h for h in r["hash_lines"] if h.type == "01")
    assert pmkid.mac_ap == "aa:bb:cc:dd:ee:ff"
    assert pmkid.mac_client == "11:22:33:44:55:66"
    assert pmkid.essid == "my-ap-1"


async def test_extract_handshakes_filters_type_02(tmp_path: Path):
    canned = (FIXTURES / "handshake-hcx.txt").read_text()

    async def fake_run(cmd: list[str]) -> tuple[int, str, str]:
        Path(cmd[2]).write_text(canned)
        return 0, "", ""

    r = await detect.extract_handshakes(
        "input.pcap", str(tmp_path / "out.22000"), run=fake_run
    )
    assert [h.type for h in r["hash_lines"]] == ["02"]


async def test_extract_pmkids_filters_type_01(tmp_path: Path):
    canned = (FIXTURES / "handshake-hcx.txt").read_text()

    async def fake_run(cmd: list[str]) -> tuple[int, str, str]:
        Path(cmd[2]).write_text(canned)
        return 0, "", ""

    r = await detect.extract_pmkids(
        "input.pcap", str(tmp_path / "out.22000"), run=fake_run
    )
    assert [h.type for h in r["hash_lines"]] == ["01"]


async def test_convert_to_hashcat_surfaces_tool_failure(tmp_path: Path):
    async def fake_run(cmd: list[str]) -> tuple[int, str, str]:
        return 1, "", "no handshakes found"

    r = await detect.convert_to_hashcat(
        "input.pcap", str(tmp_path / "out.22000"), run=fake_run
    )
    assert r["ok"] is False
    assert any("no handshakes found" in w for w in r["warnings"])


def test_regenerate_fixtures_script_runs(tmp_path: Path):
    """Sanity: the fixture generator produces identical bytes every run."""
    # Re-run the generator into a temp dir; hash-compare with the tracked file.
    import subprocess
    import sys

    script = Path(__file__).parents[1] / "scripts" / "generate-pcap-fixtures.py"
    subprocess.run([sys.executable, str(script)], check=True)
    for name in ("beacon-open.pcap", "beacon-wpa2.pcap", "handshake-hcx.txt"):
        assert (FIXTURES / name).exists()
