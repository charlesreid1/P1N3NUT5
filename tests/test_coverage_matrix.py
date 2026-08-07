"""Era × vendor coverage matrix — the plan step 6.

Samples the corpus by (era, vendor) cell and confirms non-empty
coverage across the {WPA2-era, WPA3-era, Wi-Fi 6/6E-era} ×
{Cisco, Ubiquiti, TP-Link, MikroTik, Ruckus, consumer-mesh} matrix.

The coverage signal comes from `vendors.json`: each vendor_profile
record declares `technical_body.era_footprint.{wpa2_era, wpa3_era,
wifi6_6e_era}` as a short prose string. A cell counts as covered
iff that field exists and is non-empty. This is a *coverage* test,
not a *correctness* test — it flags gaps in the plan's target
matrix, not wrong content.

A separate check confirms the vendor records themselves cross-link
into the rest of the corpus so a vendor is not a stub: every
vendor_profile.see_also target must resolve to a real record.
"""

from __future__ import annotations

import pytest

from p1n3nut5_mcp import knowledge as kb


# The plan's target matrix. Rows are eras, columns are vendor
# profile ids. If you rename a vendor id in vendors.json, update
# the column list here.
ERAS = ("wpa2_era", "wpa3_era", "wifi6_6e_era")
VENDORS = (
    "vendor-cisco",
    "vendor-ubiquiti",
    "vendor-tp-link",
    "vendor-mikrotik",
    "vendor-ruckus",
    "vendor-consumer-mesh",
)


def _cell(vendor_id: str, era: str) -> str | None:
    """Return the era footprint prose for (vendor, era), or None."""
    corpus = kb.get_corpus()
    rec = corpus.by_id.get(vendor_id)
    if rec is None:
        return None
    footprint = rec.body.get("technical_body", {}).get("era_footprint", {})
    val = footprint.get(era)
    if isinstance(val, str) and val.strip():
        return val.strip()
    return None


@pytest.mark.parametrize("vendor", VENDORS)
@pytest.mark.parametrize("era", ERAS)
def test_coverage_cell_non_empty(era: str, vendor: str) -> None:
    """Every (era, vendor) cell must have a non-empty footprint entry."""
    prose = _cell(vendor, era)
    assert prose is not None, f"missing coverage for ({era}, {vendor})"
    # The prose should be more than a placeholder — at least 20 chars.
    assert len(prose) >= 20, (
        f"({era}, {vendor}) footprint is too short: {prose!r}"
    )


def test_vendor_records_are_registered() -> None:
    """Every vendor listed in the matrix has a vendor_profile record."""
    corpus = kb.get_corpus()
    ids = {r.id for r in corpus.category("vendor_profile")}
    for v in VENDORS:
        assert v in ids, f"vendor_profile record missing: {v}"


def test_vendor_records_cross_link_into_corpus() -> None:
    """Every vendor's see_also target resolves — no stub vendors."""
    corpus = kb.get_corpus()
    for rec in corpus.category("vendor_profile"):
        assert rec.see_also, f"vendor {rec.id} has empty see_also — stub record"
        for target in rec.see_also:
            assert target in corpus.by_id, (
                f"vendor {rec.id} see_also target {target!r} does not resolve"
            )


def test_matrix_is_dense() -> None:
    """Sanity check on the whole matrix — every cell filled."""
    missing: list[tuple[str, str]] = []
    for era in ERAS:
        for vendor in VENDORS:
            if _cell(vendor, era) is None:
                missing.append((era, vendor))
    assert not missing, f"coverage gaps: {missing}"
