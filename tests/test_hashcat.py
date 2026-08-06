"""crack_start / crack_status / crack_result / crack_stop."""

from __future__ import annotations

from pathlib import Path

import pytest

from p1n3nut5_mcp import hashcat as hashcat_mod
from p1n3nut5_mcp.hashcat import (
    Job,
    _register_for_tests,
    _reset_registry_for_tests,
    crack_result,
    crack_start,
    crack_status,
)
from p1n3nut5_mcp.runtime import Config


@pytest.fixture(autouse=True)
def _reset_registry():
    _reset_registry_for_tests()
    yield
    _reset_registry_for_tests()


class FakeProc:
    def __init__(self, pid=4242, returncode=None):
        self.pid = pid
        self.returncode = returncode

    def terminate(self) -> None:
        self.returncode = -15

    def kill(self) -> None:
        self.returncode = -9

    async def wait(self) -> int:
        if self.returncode is None:
            self.returncode = 0
        return self.returncode


async def test_crack_start_uses_hashcat_bin_and_records_job(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
):
    captured_cmd: list[str] = []

    async def fake_spawn(*cmd, **kw):
        captured_cmd.extend(cmd)
        return FakeProc()

    cfg = Config.from_env(
        {
            "PINEAPPLE_HOST": "x",
            "HASHCAT_PATH": "/opt/hashcat/hashcat",
            "WORDLIST_DIR": "/opt/wordlists",
        }
    )
    hash_path = str(tmp_path / "target.22000")
    Path(hash_path).write_text("WPA*02*...\n")

    job = await crack_start(
        hash_path, wordlist_path="rockyou.txt", mode=22000, config=cfg, spawn=fake_spawn
    )
    assert job.mode == 22000
    assert captured_cmd[0] == "/opt/hashcat/hashcat"
    assert "-m" in captured_cmd and "22000" in captured_cmd
    # Relative wordlist gets prefixed with WORDLIST_DIR
    assert "/opt/wordlists/rockyou.txt" in captured_cmd
    status = crack_status(job.id)
    assert status["ok"] is True
    assert status["running"] is True


def test_crack_status_unknown_job():
    r = crack_status("nope")
    assert r["ok"] is False
    assert "unknown job" in r["error"]


def test_crack_result_reads_outfile(tmp_path: Path):
    outfile = tmp_path / "out.txt"
    outfile.write_text("password123\nhunter2\n\n")  # blank line filtered
    job = Job(
        id="abcd1234",
        mode=22000,
        hash_path="ignored",
        wordlist_path="ignored",
        outfile=str(outfile),
        exit_code=0,
    )
    _register_for_tests(job)
    r = crack_result("abcd1234")
    assert r["cracked"] == ["password123", "hunter2"]
    assert r["cracked_count"] == 2


async def test_crack_stop_terminates(monkeypatch: pytest.MonkeyPatch, tmp_path: Path):
    async def fake_spawn(*cmd, **kw):
        return FakeProc()

    cfg = Config.from_env({"PINEAPPLE_HOST": "x"})
    job = await crack_start(
        str(tmp_path / "h"), wordlist_path="/abs/wordlist", config=cfg, spawn=fake_spawn
    )
    r = await hashcat_mod.crack_stop(job.id)
    assert r["ok"] is True
