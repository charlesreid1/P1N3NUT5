"""L8 coverage tests — lock in the L1-L7 fixes.

Three CI gates:
  T-L1  every CAPABILITY_RULES key has a handler in server.main()
  T-L2  every tool named in SKILL.md is either registered or Deferred
  T-L3  every markdown link in the top-level docs resolves

Separate module from the L6 depth tests (`test_depth.py`) — those lock
corpus depth; these lock code / doc / config consistency.
"""

from __future__ import annotations

import ast
import inspect
import re
from pathlib import Path

import pytest

from p1n3nut5_mcp import pineapple_transport, server


REPO = Path(__file__).resolve().parent.parent


# --------------------------------------------------------------------------- #
# T-L1 — CAPABILITY_RULES ↔ server.main() coverage
# --------------------------------------------------------------------------- #


def _registered_tool_names() -> set[str]:
    """Names of every tool registered in server.main() (via app.tool())."""
    src = inspect.getsource(server.main)
    tree = ast.parse(src)
    names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Name):
            names.add(node.id)
    return names


# Capability → server tool name for the handful of cases where the
# server exposes the tool under a different name than the capability.
CAPABILITY_ALIASES = {
    "status": "pineapple_status",
}


def test_every_capability_has_a_handler() -> None:
    """Every key in CAPABILITY_RULES has a matching server tool.

    Accepts (in order): a direct name match, a `do_<capability>` server-
    layer wrapper (server.py wraps every transmitting primitive that
    way), or an explicit alias in CAPABILITY_ALIASES.
    """
    caps = set(pineapple_transport.CAPABILITY_RULES)
    tools = _registered_tool_names()
    missing = []
    for cap in caps:
        if cap in tools:
            continue
        if f"do_{cap}" in tools:
            continue
        if CAPABILITY_ALIASES.get(cap) in tools:
            continue
        missing.append(cap)
    assert not missing, (
        f"CAPABILITY_RULES has {missing} without a handler in server.main() — "
        "either register the tool or drop the rule."
    )


# --------------------------------------------------------------------------- #
# T-L2 — SKILL.md tool inventory consistency
# --------------------------------------------------------------------------- #


SKILL = REPO / "skills" / "pineapple" / "SKILL.md"


def _skill_tool_names() -> tuple[set[str], set[str]]:
    """Parse SKILL.md — return (landed_names, deferred_names).

    A "tool name" is the first backtick-quoted identifier in a bulleted
    line under any `### Act — ...`, `### Perceive — ...`, or
    `### Orchestrate` section. The `### Deferred — ...` section carries
    the aspirational names that must not be registered.
    """
    text = SKILL.read_text(encoding="utf-8")
    lines = text.splitlines()

    landed: set[str] = set()
    deferred: set[str] = set()
    section: str | None = None  # 'landed' | 'deferred' | None

    ident_pat = re.compile(r"`([a-zA-Z_][a-zA-Z0-9_]*)`")
    for line in lines:
        h = line.strip()
        # Reset section on ANY heading — a `## Common WCTF patterns`
        # after `### Deferred` should NOT keep us in "deferred", or
        # every backtick ident in the playbook prose gets misfiled.
        if h.startswith("#"):
            section = None
            if h.startswith("### "):
                title = h[4:].strip().lower()
                first_word = re.split(r"[\s—-]+", title, maxsplit=1)[0]
                if first_word == "deferred":
                    section = "deferred"
                elif first_word in {"act", "perceive", "orchestrate"}:
                    section = "landed"
            continue
        if section is None or not h.startswith("- "):
            continue
        m = ident_pat.search(h)
        if not m:
            continue
        (landed if section == "landed" else deferred).add(m.group(1))
    return landed, deferred


def test_skill_landed_tools_are_registered() -> None:
    """Every name in SKILL.md's landed sections resolves to a server tool.

    The tool name may match the registered name directly, or the
    server may expose it under a `do_` prefix (server.py wraps the
    transmitting primitives that way).
    """
    landed, _deferred = _skill_tool_names()
    tools = _registered_tool_names()
    missing: list[str] = []
    for name in sorted(landed):
        if name in tools:
            continue
        if f"do_{name}" in tools:
            continue
        # `pineapple_status` in SKILL is server.pineapple_status
        if hasattr(server, name):
            continue
        missing.append(name)
    assert not missing, (
        f"SKILL.md lists {missing} in a landed section, but the name does "
        "not resolve in server.py — either register or move to Deferred."
    )


def test_skill_deferred_tools_are_not_registered() -> None:
    """Nothing in SKILL.md's Deferred section is actually registered.

    If someone lands a deferred tool, they should move it to a live
    section, not leave it in Deferred where the assistant will refuse
    to invoke it.
    """
    _landed, deferred = _skill_tool_names()
    tools = _registered_tool_names()
    over_promised = [n for n in sorted(deferred) if n in tools or f"do_{n}" in tools]
    assert not over_promised, (
        f"Tools listed as Deferred in SKILL.md but registered in "
        f"server.main(): {over_promised}. Move them to a live section."
    )


# --------------------------------------------------------------------------- #
# T-L3 — docs-link integrity
# --------------------------------------------------------------------------- #


LINK_PAT = re.compile(r"\[[^\]]+\]\(([^)]+)\)")


def _iter_docs() -> list[Path]:
    return [
        REPO / "README.md",
        *sorted((REPO / "docs").glob("*.md")),
        REPO / "knowledge" / "MANIFEST.md",
        REPO / "knowledge" / "records" / "README.md",
        REPO / "tests" / "README.md",
        REPO / "skills" / "pineapple" / "SKILL.md",
    ]


@pytest.mark.parametrize("doc", _iter_docs(), ids=lambda p: p.relative_to(REPO).as_posix())
def test_doc_links_resolve(doc: Path) -> None:
    """Every relative markdown link from the top-level docs must resolve.

    Skips absolute URLs (http/https), mailto, and same-page anchors
    (`#foo`). Anchor fragments on relative links are stripped before
    filesystem lookup.
    """
    assert doc.exists(), doc
    text = doc.read_text(encoding="utf-8")
    broken: list[str] = []
    for match in LINK_PAT.finditer(text):
        target = match.group(1).strip()
        if not target:
            continue
        low = target.lower()
        if low.startswith(("http://", "https://", "mailto:", "ftp://")):
            continue
        if target.startswith("#"):
            continue
        # strip anchor fragment
        path_part = target.split("#", 1)[0]
        if not path_part:
            continue
        resolved = (doc.parent / path_part).resolve()
        if not resolved.exists():
            broken.append(f"{target} → {resolved}")
    assert not broken, (
        f"{doc.relative_to(REPO)} has unresolved links: {broken}"
    )
