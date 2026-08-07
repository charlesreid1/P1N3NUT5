"""KR MCP tools + verify_claim trap catalog + explain_attack contract."""

from __future__ import annotations

from p1n3nut5_mcp import knowledge as k


def test_lookup_standard_by_alias():
    r = k.lookup_standard("wi-fi 6")
    assert r["ok"]
    assert r["payload"]["id"] == "std-802-11ax"
    assert r["envelope"]["confidence"] == "primary"


def test_lookup_attack_returns_hashcat_mode_for_pmkid():
    r = k.lookup_attack("pmkid-capture")
    assert r["ok"]
    assert r["payload"]["hashcat_mode"] == 22000
    assert "hcxdumptool" in r["payload"]["tools"]


def test_lookup_cve_normalizes_id():
    for variant in ("CVE-2023-52424", "cve-2023-52424", "2023-52424"):
        r = k.lookup_cve(variant)
        assert r["ok"], variant
        assert "SSID Confusion" in r["payload"]["name"], variant


def test_lookup_hashcat_mode_by_number():
    r = k.lookup_hashcat_mode(22000)
    assert r["ok"]
    assert "22000" in r["payload"]["name"] or r["payload"].get("technical_body", {}).get("mode") == 22000


def test_lookup_ie_by_element_id():
    r = k.lookup_ie(48)
    assert r["ok"]
    assert r["payload"]["id"] == "ie-rsn"


def test_lookup_frame_by_type_subtype():
    r = k.lookup_frame(0, 12)  # deauth
    assert r["ok"]
    assert r["payload"]["id"] == "frame-mgmt-deauth"


def test_explain_attack_never_refuses_on_era():
    """WCTF ethos — always return the steps."""
    r = k.explain_attack("wep-fms", era="2026")
    assert r["ok"]
    # WEP-FMS era_bounds start in 2001; 2026 is inside → no context line.
    r2 = k.explain_attack("wpa2-4way-capture", era="1990")
    assert r2["ok"]
    assert any("era=1990" in c for c in r2["payload"]["context"])
    assert r2["payload"]["tools"]  # still returned


def test_explain_attack_unknown_returns_ok_false():
    r = k.explain_attack("nope-not-a-thing")
    assert r["ok"] is False


def test_cross_reference_walks_see_also():
    r = k.cross_reference("pmkid-capture")
    assert r["ok"]
    linked_ids = {rec["id"] for rec in r["payload"]["see_also"]}
    assert "hashcat-mode-22000" in linked_ids
    assert "km-wpa2-psk" in linked_ids


def test_bibliography_all_returns_the_shipped_corpus():
    r = k.bibliography()
    assert r["ok"]
    assert r["count"] > 30


def test_search_records_by_category_and_transport():
    r = k.search_records(category="attack", transport="ssh")
    assert r["ok"]
    assert r["count"] > 10
    for rec in r["payload"]:
        assert rec.get("transport") == "ssh"


# ---- verify_claim traps (plan-knowledge.md § "Explicitly disputed") --------


def test_verify_claim_pmf_deauth_needs_qualification():
    r = k.verify_claim("PMF prevents all deauth attacks")
    assert r["payload"]["verdict"] == "needs_qualification"


def test_verify_claim_wpa3_offline_dictionary_needs_qualification():
    r = k.verify_claim("WPA3 fixes offline dictionary attack on the PSK")
    assert r["payload"]["verdict"] == "needs_qualification"


def test_verify_claim_hidden_ssid_is_false():
    r = k.verify_claim("Hiding your SSID makes the network secret")
    assert r["payload"]["verdict"] == "false"


def test_verify_claim_ssid_confusion_needs_psk_false():
    r = k.verify_claim("SSID Confusion attack needs the target's PSK")
    assert r["payload"]["verdict"] == "false"


def test_verify_claim_deauth_reason_7_is_true():
    r = k.verify_claim("Deauth reason 7 is class 3 frame received from nonassociated STA")
    assert r["payload"]["verdict"] == "true"


def test_verify_claim_unrelated_returns_unverified():
    r = k.verify_claim("The moon is made of green cheese")
    assert r["payload"]["verdict"] == "unverified"


# ---- prose corpus -----------------------------------------------------------


def test_list_topics_finds_wpa2():
    r = k.list_topics()
    assert r["ok"]
    assert "reference" in r["payload"].get("wpa2", [])


def test_read_lore_returns_uri():
    r = k.read_lore("wpa2", "reference")
    assert r["ok"]
    assert r["payload"]["uri"] == "p1n3nut5://wpa2/reference"
    assert "RSN IE" in r["payload"]["text"]


def test_search_lore_matches_across_topics():
    # Ask for enough results that the pmkid/ hit isn't clipped by the cap
    # once the corpus grows past 20 topic files.
    r = k.search_lore("PMKID", max_results=50)
    assert r["ok"]
    topics = {h["topic"] for h in r["payload"]}
    assert "pmkid" in topics
