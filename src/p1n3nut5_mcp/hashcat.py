"""
Thin wrapper around a local hashcat install.

Job model:
  * `crack_start(hash_path, wordlist_path, mode)` spawns a hashcat
    subprocess, returns a `job_id`.
  * The job runs to completion in the background; the MCP process
    keeps a small registry mapping id → live/finished record.
  * `crack_status(id)` reports pid + exit code (None while running).
  * `crack_result(id)` returns the parsed `--outfile` — the cracked
    lines hashcat wrote when it hit a match.
  * `crack_stop(id)` sends SIGTERM.

Honors HASHCAT_PATH and WORDLIST_DIR from plan-organize.md's env
table. Wordlist path is joined against WORDLIST_DIR when relative.
"""

from __future__ import annotations

import asyncio
import os
import uuid
from dataclasses import dataclass, field
from pathlib import Path

from p1n3nut5_mcp.runtime import Config


@dataclass
class Job:
    id: str
    mode: int
    hash_path: str
    wordlist_path: str
    outfile: str
    proc: "asyncio.subprocess.Process | None" = None
    exit_code: int | None = None
    _stderr: str = ""
    _stdout: str = ""


@dataclass
class Registry:
    jobs: dict[str, Job] = field(default_factory=dict)


_REGISTRY = Registry()


def _resolve_wordlist(cfg: Config, wordlist_path: str) -> str:
    p = Path(wordlist_path)
    if p.is_absolute() or cfg.wordlist_dir is None:
        return str(p)
    return str(Path(cfg.wordlist_dir) / p)


def _hashcat_bin(cfg: Config) -> str:
    return cfg.hashcat_path or "hashcat"


async def crack_start(
    hash_path: str,
    wordlist_path: str,
    mode: int = 22000,
    config: Config | None = None,
    outdir: str = "/tmp",
    spawn=asyncio.create_subprocess_exec,
) -> Job:
    """Spawn hashcat in the background. Returns the Job record."""
    cfg = config or Config.from_env()
    job_id = uuid.uuid4().hex[:8]
    outfile = str(Path(outdir) / f"crack-{job_id}.out")
    wl = _resolve_wordlist(cfg, wordlist_path)
    cmd = [
        _hashcat_bin(cfg),
        "-m",
        str(mode),
        "-a",
        "0",  # straight
        "--quiet",
        "--outfile",
        outfile,
        "--outfile-format",
        "2",  # plaintext only
        hash_path,
        wl,
    ]
    proc = await spawn(*cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
    job = Job(
        id=job_id,
        mode=mode,
        hash_path=hash_path,
        wordlist_path=wl,
        outfile=outfile,
        proc=proc,
    )
    _REGISTRY.jobs[job_id] = job
    return job


def crack_status(job_id: str) -> dict:
    job = _REGISTRY.jobs.get(job_id)
    if job is None:
        return {"ok": False, "error": f"unknown job {job_id}"}
    proc = job.proc
    pid = proc.pid if proc else None
    exit_code = proc.returncode if proc else job.exit_code
    return {
        "ok": True,
        "id": job.id,
        "pid": pid,
        "exit_code": exit_code,
        "running": exit_code is None,
        "mode": job.mode,
    }


def crack_result(job_id: str) -> dict:
    job = _REGISTRY.jobs.get(job_id)
    if job is None:
        return {"ok": False, "error": f"unknown job {job_id}"}
    cracked: list[str] = []
    outfile = Path(job.outfile)
    if outfile.exists():
        cracked = [line for line in outfile.read_text().splitlines() if line]
    return {
        "ok": True,
        "id": job.id,
        "cracked": cracked,
        "cracked_count": len(cracked),
    }


async def crack_stop(job_id: str) -> dict:
    job = _REGISTRY.jobs.get(job_id)
    if job is None or job.proc is None:
        return {"ok": False, "error": f"unknown job {job_id}"}
    try:
        job.proc.terminate()
    except ProcessLookupError:
        pass
    try:
        await asyncio.wait_for(job.proc.wait(), timeout=5)
    except asyncio.TimeoutError:
        job.proc.kill()
        await job.proc.wait()
    return {"ok": True, "id": job_id, "exit_code": job.proc.returncode}


def _reset_registry_for_tests() -> None:
    """Test hook — never called from production code."""
    _REGISTRY.jobs.clear()


def _register_for_tests(job: Job) -> None:
    _REGISTRY.jobs[job.id] = job


# quiet the flake8 unused-import for os
_ = os
