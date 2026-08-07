#!/usr/bin/env python3
"""
Depth-pass enrichment for knowledge/records/attacks.json.

Implements Phase D1 (A1–A5) from plan-improve-docs.md:
  A1. flag_signature present on every record (string or explicit null).
  A2. mitigation present on every record (list or explicit null-with-note).
  A3. preconditions ≥ 2 bullets on every record.
  A4. Tier-1.5 frontier records carry a paper-anchored `notes` field.
  A5. Missing Appendix-B slugs authored (8 new records, 3 aliasable renames).

Idempotent — reruns produce byte-identical output. All strings are
authored inline. Cites reuse existing bibliography.json ids only.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

RECORDS = Path(__file__).resolve().parent.parent / "knowledge" / "records"
ATTACKS = RECORDS / "attacks.json"


# ---------------------------------------------------------------------------
# A1 + A2 — flag_signature and mitigation per attack id.
# `null` means "no WCTF-flag shape for this primitive" (DoS / fuzz / etc.);
# encoded as JSON null in the output.
# ---------------------------------------------------------------------------

FLAG_SIGNATURES: dict[str, str | None] = {
    # WEP family — the recovered key IS the flag or it decrypts a target frame.
    "wep-korek": "recovered WEP key decrypts the target frame or is the flag itself",
    "wep-arp-request-replay": (
        "not itself a flag — feeds FMS/KoreK/PTW, whose recovered WEP key is the flag"
    ),
    "tkip-beck-tews-mic-recovery": (
        "recovered Michael MIC key lets you inject one QoS ARP-length frame per rekey window; "
        "flag lands if the puzzle rewards a plaintext-injection primitive"
    ),
    # WPS family.
    "wps-pixie-dust": "recovered WPS PIN → PSK → flag",
    "wps-null-pin": "recovered PSK returned by the registrar's empty-PIN acceptance",
    "wps-vendor-pin-derivation": "first-try PSK recovered from vendor-derived PIN",
    "krack-linux-all-zero-ptk": (
        "post-M3-replay client traffic decrypts with the all-zero PTK — plaintext bytes are the flag"
    ),
    "krack-ft-reassoc": (
        "post-replay client traffic decrypts with the reinstalled PTK; flag lives in captured frames"
    ),
    "dragonblood-sidechannel": (
        "recovered SAE password element via side-channel timing → PSK, PSK is the flag"
    ),
    "dragonblood-timing": (
        "recovered SAE password element via MODP timing oracle → PSK, PSK is the flag"
    ),
    "kr00k-qca-cve-2020-3702": (
        "post-disassoc tail frames from a Qualcomm-Atheros client decrypt with all-zero PTK"
    ),
    "fragattacks-plaintext-inject": (
        "attacker-crafted plaintext delivered as an A-MSDU subframe to the victim client"
    ),
    "fragattacks-mixed-key": (
        "victim's decrypted frame reassembled from fragments encrypted under different keys — flag "
        "is the leaked plaintext"
    ),
    "macstealer-mac-hijack": (
        "return-traffic destined for the victim MAC delivered to the attacker instead — flag lives "
        "in the captured payload"
    ),
    "wifi7-mlo-link-desync": (
        "one MLO link left in a stale state accepts frames the other link has rekeyed past; flag is "
        "either injected content or hijacked return traffic on the desynced link"
    ),
    "btm-forced-roam": (
        "victim's client associates to the attacker BSSID under its own cooperation — flag lives in "
        "post-association traffic captured on the rogue"
    ),
    "neighbor-report-spoof": (
        "same as btm-forced-roam — client roams onto attacker BSSID and its traffic is captured"
    ),
    "passpoint-roaming-consortium-spoof": (
        "Passpoint client auto-associates to attacker AP; captured EAP inner exchange or portal "
        "traffic is the flag"
    ),
    "mc-mitm-dual-radio": (
        "primitive — flag depends on the follow-on attack (KRACK reinstall, deauth-driven "
        "reassociation, band-forced roam)"
    ),
    "deauth-targeted": (
        "target client reassociates after being kicked; the resulting 4-way capture yields the "
        "flag via crack"
    ),
    "disassoc-targeted": (
        "on Kr00k-vulnerable chipsets the post-disassoc tail decrypts with zero-PTK; otherwise a "
        "reassociation-trigger primitive"
    ),
    "probe-flood-mdk4": None,
    "authentication-flood": None,
    "association-flood": None,
    "eapol-start-flood": None,
    "rts-cts-nav-dos": None,
    "cts-to-self-silencing": None,
    "mana-loud": (
        "any client with a matching preferred-network probe associates; flag is captured "
        "association traffic or portal input"
    ),
    "mana-known-beacons": (
        "any client whose preferred network is in the dictionary auto-associates without probing"
    ),
    "rogue-radius-eaphammer": (
        "inner MSCHAPv2 or GTC captured under the rogue tunnel — hashcat 5500 recovers the "
        "password (flag), or the OTP is directly usable"
    ),
    "cert-phish-eaphammer-weak-validation": (
        "victim client without server-cert pinning completes EAP against the attacker — inner "
        "credentials or OTP is the flag"
    ),
    "eap-inner-downgrade-peap-mschapv2": (
        "MSCHAPv2 challenge/response captured under downgrade — hashcat 5500 recovers the flag"
    ),
    "asleap-mschapv2-crack": "recovered MSCHAPv2 password (the flag)",
    "hashcat-5500-mschapv2-crack": "recovered MSCHAPv2 password (the flag)",
    "leap-legacy-crack": "recovered LEAP password (the flag) via asleap or hashcat 5500",
    "default-psk-thomson-speedtouch": (
        "PSK derived from the SSID suffix — validate against a captured PMKID or handshake"
    ),
    "pineap-active-karma": (
        "victim client associates believing it's on a preferred network — flag lives in captured "
        "post-association traffic (DNS lookups, HTTP, mail credentials)"
    ),
    "pineap-ssid-pool-broadcast": (
        "victim in range whose preferred-network list intersects the pool auto-associates"
    ),
    "twt-forced-sleep-abuse": (
        "primitive — target client is starved of receive time. Not itself a flag; enables other "
        "attacks (deauth-driven roam without the client responding, delayed-response race conditions)"
    ),
    "ru-based-ofdma-dos": None,
    "packet-inject-arbitrary": None,
    "wps-negative-pin": "recovered PSK on the affected firmware generation",
    "wps-locked-bypass-timing": "recovered PSK after waiting through lockout cycles",
    "krack-groupkey-reinstall": (
        "GTK reinstalled to a zero-or-known value; broadcast traffic can be decrypted or replayed"
    ),
    "krack-wnm-reinstall": (
        "PTK reinstalled during WNM sleep-mode key rotation; captured post-sleep frames decrypt"
    ),
    "fragattacks-cache-poisoning": (
        "victim reassembles attacker plaintext with legitimate ciphertext across (re)connect — flag "
        "is the injected payload delivered up-stack"
    ),
    "sae-h2e-followup-side-channel": (
        "recovered SAE password element via residual timing leak → PSK is the flag"
    ),
    "dragonblood-modp-downgrade": (
        "victim completes SAE under attacker-chosen weak MODP group; timing oracle then applies "
        "and yields the PSK"
    ),
    "eap-gtc-plaintext-token-capture": (
        "plaintext OTP captured inside the rogue PEAP tunnel; usable within its validity window"
    ),
    "mdm-profile-theft-captive-portal": (
        "victim installs a rogue MDM profile that pins the attacker's RADIUS cert; all subsequent "
        "EAP flows deliver credentials to the attacker"
    ),
    "mschapv2-challenge-response-capture": (
        "captured challenge/response pair; hashcat 5500 / asleap recovers the password (the flag)"
    ),
    "default-psk-bt-home-hub": (
        "PSK derived from the BTHub SSID suffix; validate against a captured PMKID or handshake"
    ),
    "default-psk-sky-broadband": "PSK derived from the SKY-prefix SSID",
    "default-psk-livebox-sagemcom": "PSK derived from the Livebox-XXXX SSID",
    "default-psk-netgear-genie": "PSK is one of the adjective-noun-3digits pattern",
    "default-psk-technicolor": "PSK derived from the Technicolor SSID + serial",
    "csa-rogue-channel": (
        "victim client tunes to attacker channel; flag lives in what happens next (rogue-AP capture "
        "or MC-MitM setup)"
    ),
    "wnm-sleep-mode-abuse": None,
    "tdls-teardown-injection": (
        "STA-to-STA traffic that had been direct now traverses the AP; observable frames may carry "
        "the flag"
    ),
    "ap-fuzzed-ies-crash": None,
    "eapol-4way-nonce-reuse": (
        "diagnostic — the fact of nonce reuse is the flag for detection puzzles"
    ),
    "band-steering-abuse": (
        "victim client drops to 2.4 GHz where attacker AP is waiting; flag is captured "
        "post-association traffic"
    ),
    "krack-groupkey-broadcast-replay": (
        "replayed broadcast frame accepted by unpatched client — flag is the plaintext contents"
    ),
    "wps-hcxlabtool-aggressive": (
        "recovered PSK from PMKID capture; WPS side yields PIN on vulnerable chipsets"
    ),
}


MITIGATIONS: dict[str, list[str] | None] = {
    "wep-korek": ["retire WEP", "any WPA generation defeats it"],
    "wep-arp-request-replay": ["retire WEP", "disable ARP responses on the AP where possible (rare on APs)"],
    "tkip-beck-tews-mic-recovery": [
        "retire TKIP",
        "use CCMP/GCMP only",
        "reduce Michael MIC failure countermeasure window to zero seconds is not enough — the leak still occurs",
    ],
    "wps-pixie-dust": [
        "disable WPS",
        "patched WPS registrar entropy on newer chipset firmware",
    ],
    "wps-null-pin": ["disable WPS"],
    "wps-vendor-pin-derivation": ["disable WPS", "customer-visible PIN rotation on affected vendors"],
    "krack-linux-all-zero-ptk": [
        "patched wpa_supplicant (≥ 2.7)",
        "OCI in the 4-way handshake blocks the MC-MitM prerequisite",
    ],
    "krack-ft-reassoc": [
        "patched hostapd on the target-side AP",
        "802.11r amendment (post-2018) with OCI in the FT reassoc",
    ],
    "dragonblood-sidechannel": [
        "SAE-PT / H2E (km-wpa3-sae-ext-key)",
        "cache-partitioned hostapd builds",
    ],
    "dragonblood-timing": [
        "disable MODP groups (ECC-only)",
        "hostapd `sae_groups` set to 19 / 20 / 21 only",
    ],
    "kr00k-qca-cve-2020-3702": ["patched Qualcomm-Atheros firmware"],
    "fragattacks-plaintext-inject": [
        "patched client + AP for CVE-2020-24588",
        "reject non-SPP A-MSDU frames at the client",
    ],
    "fragattacks-mixed-key": [
        "patched client + AP for CVE-2020-24587",
        "clear the fragmentation cache on rekey",
    ],
    "macstealer-mac-hijack": [
        "AP-side client isolation that binds the isolation state to the 4-way session, not the MAC",
        "patched client that clears its cached AP-side association on reauth",
    ],
    "wifi7-mlo-link-desync": [
        "OCI-equivalent link binding in the 4-way (in the 802.11be errata as of 2025)",
        "reject frames on a link whose sequence-number space is behind the rekey point",
    ],
    "btm-forced-roam": [
        "PMF-required blocks unsolicited BTM Requests from a rogue on older client stacks",
        "client-side ignore-BTM policy for enterprise-managed devices",
    ],
    "neighbor-report-spoof": [
        "PMF-required blocks unsolicited Neighbor Report Response frames",
        "client-side neighbor-report validation against the associated ESS's known BSSID set",
    ],
    "passpoint-roaming-consortium-spoof": [
        "server-cert pinning under the Passpoint profile (WPA2/3-Enterprise inner)",
        "OSU-provider-list allowlisting",
    ],
    "mc-mitm-dual-radio": [
        "OCI in the 4-way handshake (blocks the channel-mismatch primitive)",
        "PMF-required limits deauth-driven MC-MitM setup",
    ],
    "deauth-targeted": [
        "802.11w PMF-required matched by the client",
        "client-side rate limit on association retries",
    ],
    "disassoc-targeted": [
        "PMF-required blocks unicast disassoc against PMF-capable clients",
        "patched chipset firmware for the Kr00k trigger",
    ],
    "probe-flood-mdk4": ["WIDS probe-flood alert; AP-side rate limit on probe processing"],
    "authentication-flood": ["AP-side auth-frame rate limit; PMF-required (auth is not covered but "
                             "post-auth is)"],
    "association-flood": ["AP-side assoc-frame rate limit"],
    "eapol-start-flood": [
        "authenticator-side EAPOL-Start rate limit",
        "RADIUS Accounting-Start rate limit",
    ],
    "rts-cts-nav-dos": ["ignore excessive NAV on Duration/ID field at driver level; airtime fairness"],
    "cts-to-self-silencing": ["same as RTS/CTS NAV DoS mitigation"],
    "mana-loud": [
        "clients that MAC-randomize per probe defeat correlation but not the association",
        "client-side 'only associate on explicit user selection' policy defeats it entirely",
    ],
    "mana-known-beacons": [
        "client-side 'require probe response for preferred network' (default off on most stacks)",
        "'ignore SSIDs seen only via broadcast beacon' policy",
    ],
    "rogue-radius-eaphammer": [
        "RADIUS server certificate pinning on every client profile (MDM-enforced)",
        "disable PEAP inner-method downgrade to GTC",
    ],
    "cert-phish-eaphammer-weak-validation": [
        "server-cert pinning is the load-bearing defense",
        "EAP-TLS with mutual auth eliminates the primitive",
    ],
    "eap-inner-downgrade-peap-mschapv2": [
        "disable PEAP inner-method downgrade",
        "server-cert pinning stops the tunnel establishment",
    ],
    "asleap-mschapv2-crack": ["retire MSCHAPv2 (EAP-TLS with mutual auth)"],
    "hashcat-5500-mschapv2-crack": ["retire MSCHAPv2 (EAP-TLS)"],
    "leap-legacy-crack": ["retire LEAP (PEAP or EAP-TLS)"],
    "default-psk-thomson-speedtouch": [
        "change PSK from vendor default",
        "vendor pushes non-derivable factory PSKs on newer firmware generations",
    ],
    "pineap-active-karma": [
        "client-side probe-request MAC randomization + 'associate only on explicit selection'",
        "WIDS KARMA-response detection at the venue",
    ],
    "pineap-ssid-pool-broadcast": ["client-side 'require probe response for preferred network'"],
    "twt-forced-sleep-abuse": [
        "client-side ignore-TWT policy for managed devices",
        "AP-side TWT authentication (MFP-protected Action frames)",
    ],
    "ru-based-ofdma-dos": [
        "AP-side detection of malformed Trigger frames",
        "WIDS OFDMA-anomaly alert",
    ],
    "packet-inject-arbitrary": [
        "MFP-required for management",
        "encrypted control frames not yet standardized (802.11-2024 draft)",
    ],
    "wps-negative-pin": ["disable WPS"],
    "wps-locked-bypass-timing": ["disable WPS", "permanent lockout after N failures instead of timed reset"],
    "krack-groupkey-reinstall": ["patched client + AP for CVE-2017-13080/13081"],
    "krack-wnm-reinstall": ["patched client for CVE-2017-13087/13088"],
    "fragattacks-cache-poisoning": [
        "patched client for CVE-2020-24586",
        "clear the fragmentation cache on (re)connect",
    ],
    "sae-h2e-followup-side-channel": [
        "SAE-PT with cache-partitioned math paths",
        "constant-time SAE implementation audits",
    ],
    "dragonblood-modp-downgrade": [
        "hostapd `sae_groups` restricted to ECC-only (19/20/21)",
        "client rejects MODP groups in SAE Group Negotiation",
    ],
    "eap-gtc-plaintext-token-capture": [
        "server-cert pinning stops the outer tunnel",
        "disable PEAP → GTC inner-method downgrade",
    ],
    "mdm-profile-theft-captive-portal": [
        "MDM-enforced profile pinning; block user-installed profiles on managed devices",
        "certificate pinning on the MDM enrollment endpoint",
    ],
    "mschapv2-challenge-response-capture": ["retire MSCHAPv2 (EAP-TLS)"],
    "default-psk-bt-home-hub": ["change PSK from vendor default; newer BT firmware ships non-derivable PSKs"],
    "default-psk-sky-broadband": ["change PSK from vendor default"],
    "default-psk-livebox-sagemcom": ["change PSK from vendor default"],
    "default-psk-netgear-genie": ["change PSK from vendor default"],
    "default-psk-technicolor": ["change PSK from vendor default"],
    "csa-rogue-channel": [
        "client-side ignore unauthenticated CSA (modern default)",
        "PMF-protected CSA Action frames",
    ],
    "wnm-sleep-mode-abuse": ["patched client for the WNM CVEs"],
    "tdls-teardown-injection": [
        "PMF-protected TDLS teardown (802.11-2020 §11.20)",
        "AP-side monitoring of unexpected TDLS teardowns",
    ],
    "ap-fuzzed-ies-crash": ["driver / firmware update; IE-size sanity checks in the parser"],
    "eapol-4way-nonce-reuse": None,
    "band-steering-abuse": [
        "detect on-channel jamming at the WIDS",
        "disable band-steering where a rogue-AP threat model requires it",
    ],
    "krack-groupkey-broadcast-replay": ["patched client for CVE-2017-13080"],
    "wps-hcxlabtool-aggressive": ["disable WPS; strong PSK; PMF-required"],
    # Already-mitigated records — expand the existing bullets to depth.
    "wep-fms": ["retire WEP", "use WPA2-PSK or WPA3-SAE"],
    "wpa2-4way-capture": [
        "strong PSK (12+ chars high-entropy)",
        "802.11w PMF-required blocks broadcast deauth so a client can't be forced to reassociate",
        "WPA3-SAE removes the offline crack path entirely",
    ],
    "pmkid-capture": [
        "AP firmware that omits PMKID from M1 (uneven vendor uptake in 2026)",
        "WPA3-SAE only (no transition-mode WPA2 side)",
        "strong PSK if WPA2 must remain",
    ],
    "wps-reaver-online": [
        "disable WPS on the AP",
        "WPS-Locked after N failures with permanent (not timed) lockout",
        "vendor-issued PIN rotation for affected models",
    ],
    "krack-client-key-reinstall": [
        "patched client (wpa_supplicant ≥ 2.7, iOS 11, Android 6.0.1+, Windows Oct 2017)",
        "OCI in the 4-way handshake mitigates the MC-MitM prerequisite",
    ],
    "wpa3-transition-downgrade": [
        "WPA3-only (no transition mode)",
        "6 GHz operation (WPA3-mandated)",
        "Transition Disable KDE — but only clients that honor it benefit",
    ],
    "kr00k-broadcom-cve-2019-15126": [
        "patched Broadcom / Cypress firmware",
        "PMF-required blocks the disassoc trigger against PMF-capable clients",
    ],
    "ssid-confusion-cve-2023-52424": [
        "SSID-in-4-way binding (draft standards fix)",
        "client-side check that beacon-declared BSSID matches the 4-way BSSID (some 2025+ Linux iwd builds)",
        "per-SSID unique credentials — the primitive requires shared PSK/EAP",
    ],
    "framing-frames-power-save-poison": [
        "AP-side patched hostapd (2023-Q4+)",
        "802.11-2024 draft binding of PM-bit state to the 4-way session",
    ],
    "ft-handshake-capture": [
        "strong PSK on FT-PSK deployments",
        "FT-802.1X (Enterprise) rather than FT-PSK where fleet-wide compromise risk matters",
    ],
    "anqp-realm-enum": [
        "AP-side ANQP-scope restriction (Passpoint venue setup that hides realm list from GAS)",
        "generally accepted as recon-only, but leaks fleet realm info regardless",
    ],
    "deauth-broadcast": [
        "802.11w PMF-required blocks broadcast deauth",
        "PMF-optional networks remain vulnerable against PMF-off clients",
    ],
    "beacon-flood-mdk4": [
        "WIDS beacon-flood detection with automated alert",
        "not a data-plane attack — mitigation is detection, not blocking",
    ],
    "tkip-michael-mic-dos": [
        "retire TKIP",
        "if TKIP must remain, drop Michael countermeasure window from 60s to zero (still leaks but faster recovery)",
    ],
    "evil-twin-clone": [
        "client-side AP authentication (WPA2/3-Enterprise cert pinning; WPA3-SAE per-network unique password)",
        "WIDS beacon-diff and BSSID-collision alerts",
    ],
    "mana-karma": [
        "client-side probe-request MAC randomization and 'associate only on explicit selection'",
        "clear preferred-network list of open networks",
    ],
    "captive-portal-cred-capture": [
        "clients that refuse to submit credentials to unauthenticated portals",
        "user hygiene — don't type primary credentials into a WiFi portal",
    ],
    "rogue-radius-hostapd-wpe": [
        "RADIUS server certificate pinning on every client profile (MDM-enforced)",
        "disable PEAP inner-method downgrade to GTC",
    ],
    "default-psk-upc-ubee": [
        "change PSK from vendor default",
        "operator (UPC/UBEE) pushes non-derivable factory PSKs on newer firmware generations",
    ],
    "pineap-passive-probe-log": None,
    "beacon-stego-vendor-ie": None,
}


# ---------------------------------------------------------------------------
# A3 — preconditions depth. Each entry replaces the record's preconditions[]
# if it currently has < 2 bullets, or if the existing single bullet is a
# fragment. We include the target property AND the operational property.
# ---------------------------------------------------------------------------

PRECONDITIONS: dict[str, list[str]] = {
    "wep-fms": [
        "target AP still speaks WEP-40 or WEP-104",
        "monitor+injection-capable interface within RF range",
        "enough weak-IV frames captured (~250k for 40-bit, ~500k+ for 104-bit) — usually via ARP-replay",
    ],
    "wep-korek": [
        "target AP still speaks WEP-40 or WEP-104",
        "sufficient unique IVs (fewer than FMS requires — KoreK's 17 biases cut the count)",
        "monitor-mode interface in range",
    ],
    "wep-ptw": [
        "target AP still speaks WEP-104",
        "~40k–85k unique IVs captured",
        "monitor+injection-capable interface within RF range",
    ],
    "wep-arp-request-replay": [
        "target AP speaks WEP",
        "at least one seen ARP request from a legitimate client",
        "monitor+injection-capable interface",
    ],
    "tkip-beck-tews-mic-recovery": [
        "target AP still speaks TKIP",
        "short QoS traffic (ARP-length) observable on the air",
        "monitor+injection-capable interface",
    ],
    "wps-reaver-online": [
        "WPS enabled on the target AP",
        "no aggressive WPS-Locked timing (or lockout-reset behavior)",
        "monitor+injection-capable interface in RF range",
    ],
    "wps-pixie-dust": [
        "WPS-vulnerable chipset (historically Broadcom or Ralink)",
        "single WPS exchange captured (Reaver's --pixie flag)",
        "monitor+injection-capable interface",
    ],
    "wps-null-pin": [
        "WPS registrar accepts an empty PIN (vendor-specific bug on the target firmware)",
        "monitor+injection-capable interface",
    ],
    "wps-vendor-pin-derivation": [
        "target vendor derives the WPS PIN from MAC/OUI (Belkin, D-Link, some TP-Link)",
        "vendor confirmed via WPS Manufacturer/Model IE in beacon",
    ],
    "krack-client-key-reinstall": [
        "unpatched client (wpa_supplicant < 2.7, iOS < 11, Android < 6.0.1)",
        "multi-channel MitM between client and legitimate AP",
        "attacker in range to replay M3 into the client",
    ],
    "krack-linux-all-zero-ptk": [
        "unpatched wpa_supplicant ≤ 2.6 on the target client",
        "MitM position that lets attacker replay M3",
        "attacker in RF range for both channels",
    ],
    "krack-ft-reassoc": [
        "FT-enabled AP fleet (MDE in beacons)",
        "attacker replays FT Reassoc Request against the AP",
        "target client mid-roam or forced to roam",
    ],
    "dragonblood-sidechannel": [
        "target AP uses WPA3-SAE (AKM 8) without H2E (RSNXE H2E bit clear)",
        "co-located attack surface — adjacent process on same host or precise timing over LAN",
        "vulnerable SAE implementation (hunt-and-peck without cache partitioning)",
    ],
    "dragonblood-timing": [
        "target hostapd allows MODP-group fallback in SAE Group Negotiation",
        "attacker can measure per-exchange timing from an on-path or nearby vantage",
    ],
    "wpa3-transition-downgrade": [
        "target AP advertises both AKM 2 (PSK) and AKM 8 (SAE) in the RSN IE",
        "WPA2-capable client that hasn't received the Transition Disable KDE",
        "monitor+injection-capable interface",
    ],
    "kr00k-broadcom-cve-2019-15126": [
        "target client uses a vulnerable Broadcom/Cypress chipset (unpatched firmware)",
        "attacker can inject or spoof disassoc frames",
        "monitor+injection-capable interface",
    ],
    "kr00k-qca-cve-2020-3702": [
        "target client uses a vulnerable Qualcomm-Atheros chipset (unpatched firmware)",
        "attacker can inject or spoof disassoc frames",
        "monitor-capable interface for post-disassoc capture",
    ],
    "fragattacks-plaintext-inject": [
        "target client accepts non-SPP A-MSDU frames (unpatched)",
        "monitor+injection-capable interface within RF range",
        "known BSSID/MAC pair of the target association",
    ],
    "fragattacks-mixed-key": [
        "target client stores fragments across a rekey boundary (unpatched)",
        "attacker can inject fragments during a rekey window",
    ],
    "ssid-confusion-cve-2023-52424": [
        "client trusts SSID for policy decisions (VPN auto-connect, MDM per-SSID rules)",
        "two networks share PSK / EAP credentials",
        "client has both SSIDs in its preferred-network list",
    ],
    "framing-frames-power-save-poison": [
        "target client honors PM bit and the AP queues frames on sleep",
        "monitor+injection-capable interface",
        "unpatched AP-side hostapd (pre-2023-Q4)",
    ],
    "macstealer-mac-hijack": [
        "attacker is on the same network as the victim (has PSK, or network is Open/OWE)",
        "victim MAC is known (trivial — passive observation)",
        "AP-side client isolation is either off or implemented naively (MAC-keyed, not session-keyed)",
    ],
    "wifi7-mlo-link-desync": [
        "MLO-capable client + AP negotiated multi-link operation",
        "attacker can suppress or desync one of the links (channel-selective jamming or spoofed link management)",
        "target AP firmware without the 802.11be-2024 errata link-binding fix",
    ],
    "ft-handshake-capture": [
        "target AP fleet is FT-capable (MDE in beacon)",
        "target client roams (or is forced to roam)",
        "monitor+injection-capable interface in range of both APs",
    ],
    "btm-forced-roam": [
        "target client is 11v-capable and honors BTM Requests",
        "attacker in RF range on the target's channel",
        "PMF not required or Action-frame protection incomplete on the client's stack",
    ],
    "neighbor-report-spoof": [
        "target client is 11k-capable and solicits Neighbor Reports",
        "PMF not required on the target client for Action frames",
        "monitor+injection-capable interface",
    ],
    "anqp-realm-enum": [
        "target AP is Interworking / Passpoint capable (Interworking IE present)",
        "attacker within RF range with a GAS-capable client stack (hostapd_cli or scapy)",
    ],
    "passpoint-roaming-consortium-spoof": [
        "target client has a Passpoint profile with matching Roaming Consortium OI",
        "monitor+injection-capable interface + hostapd rogue AP",
    ],
    "mc-mitm-dual-radio": [
        "target client on channel A; attacker can bring up a rogue on channel B",
        "attacker has two radios (one to attract the client, one to reach the legitimate AP)",
    ],
    "deauth-broadcast": [
        "target AP or client with PMF-disabled",
        "PMF-optional networks with PMF-incapable clients are also vulnerable",
        "monitor+injection-capable interface in RF range",
    ],
    "deauth-targeted": [
        "target client MAC known",
        "PMF-disabled OR transition-mode PMF-optional with PMF-incapable client",
        "monitor+injection-capable interface",
    ],
    "disassoc-targeted": [
        "target client uses a Kr00k-vulnerable chipset",
        "attacker can spoof or inject disassoc frames",
    ],
    "beacon-flood-mdk4": [
        "monitor+injection-capable interface",
        "target airspace with clients that surface all beaconed SSIDs (some scoring bots)",
    ],
    "probe-flood-mdk4": [
        "monitor+injection-capable interface",
        "target authenticator with a probe-request state table (some low-end APs are affected)",
    ],
    "authentication-flood": [
        "target AP with limited state-table headroom",
        "monitor+injection-capable interface",
    ],
    "association-flood": [
        "target AP without per-STA assoc rate limiting",
        "monitor+injection-capable interface",
    ],
    "eapol-start-flood": [
        "target 802.1X authenticator or RADIUS backend without EAPOL-Start rate limiting",
        "monitor+injection-capable interface associated to the AP or a wired vantage",
    ],
    "rts-cts-nav-dos": [
        "target airspace not covered by an airtime-fairness scheduler",
        "monitor+injection-capable interface",
    ],
    "cts-to-self-silencing": [
        "target driver honors CTS Duration/ID as advertised (legacy client)",
        "monitor+injection-capable interface",
    ],
    "tkip-michael-mic-dos": [
        "target AP still speaks TKIP",
        "monitor+injection-capable interface",
    ],
    "evil-twin-clone": [
        "target SSID, BSSID, and channel captured",
        "supported interface for rogue AP (channel + PHY match)",
        "captive services (DHCP/DNS/HTTP) ready to serve",
    ],
    "mana-karma": [
        "monitor+injection-capable interface",
        "target client that sends directed probe requests (i.e. has a preferred-network history and is not fully randomizing)",
    ],
    "mana-loud": [
        "monitor+injection-capable interface",
        "airspace with multiple clients whose probe-request SSIDs overlap",
    ],
    "mana-known-beacons": [
        "monitor+injection-capable interface",
        "a dictionary of common preferred-network SSIDs (venue-specific or generic)",
    ],
    "captive-portal-cred-capture": [
        "victim on the rogue AP with an IP lease",
        "DHCP/DNS/HTTP redirect chain online on the rogue",
        "portal template that credibly matches the target brand",
    ],
    "rogue-radius-hostapd-wpe": [
        "victim client with weak or absent RADIUS server-cert validation",
        "matching SSID (or KARMA-style probe response)",
        "hostapd-wpe running on a rogue AP",
    ],
    "rogue-radius-eaphammer": [
        "victim client with weak or absent RADIUS server-cert validation",
        "matching SSID or KARMA-style probe response",
    ],
    "cert-phish-eaphammer-weak-validation": [
        "victim's WPA-Enterprise profile does not pin the RADIUS server certificate",
        "rogue-RADIUS in RF range under a matching SSID",
    ],
    "eap-inner-downgrade-peap-mschapv2": [
        "victim client that accepts PEAP inner-method downgrade to MSCHAPv2",
        "rogue-RADIUS with the downgrade negotiation configured",
    ],
    "eap-inner-downgrade-peap-gtc": [
        "victim client that accepts PEAP inner-method downgrade to GTC",
        "rogue-RADIUS with the GTC inner offered",
    ],
    "asleap-mschapv2-crack": [
        "captured MSCHAPv2 challenge/response pair",
        "wordlist or mask that plausibly contains the password",
    ],
    "hashcat-5500-mschapv2-crack": [
        "captured MSCHAPv2 challenge/response as a hashcat-5500 line",
        "GPU + wordlist / rules for the crack run",
    ],
    "leap-legacy-crack": [
        "captured LEAP challenge/response",
        "wordlist covering common corporate password patterns",
    ],
    "default-psk-upc-ubee": [
        "target SSID matches /^UPC\\d{7}$/",
        "no radio time required — pure passive derivation",
    ],
    "default-psk-thomson-speedtouch": [
        "target SSID matches SpeedTouch<hex-suffix> pattern",
        "no radio time required — pure passive derivation",
    ],
    "pineap-passive-probe-log": [
        "Mark VII with PineAP enabled (logging on)",
        "target client in RF range that emits probe requests (i.e. hasn't fully randomized to broadcast probes)",
    ],
    "pineap-active-karma": [
        "Mark VII with PineAP karma toggle on",
        "target client emitting directed probe requests",
        "airspace authorization to transmit",
    ],
    "pineap-ssid-pool-broadcast": [
        "Mark VII with SSID pool populated (venue-specific or Known Beacons dictionary)",
        "airspace authorization to transmit",
    ],
    "twt-forced-sleep-abuse": [
        "Wi-Fi 6/6E client with TWT negotiated to the AP",
        "attacker can craft TWT Setup Action frames from a rogue vantage",
    ],
    "rnr-6ghz-enumeration": [
        "target AP fleet advertises RNR in 2.4/5 GHz beacons",
        "capture card with 2.4/5 GHz coverage (does NOT need to tune 6 GHz)",
    ],
    "ru-based-ofdma-dos": [
        "target Wi-Fi 6/6E AP with OFDMA scheduling enabled",
        "monitor+injection-capable Wi-Fi 6/6E interface",
    ],
    "packet-inject-arbitrary": [
        "monitor+injection-capable interface",
        "target frame shape defined (management/control/data with appropriate 802.11 header fields)",
    ],
    "beacon-stego-vendor-ie": [
        "target beacon advertises a custom OUI Vendor-Specific IE with attacker-encoded content",
        "passive capture in range for enough beacon intervals to reassemble the payload",
    ],
    "wps-negative-pin": [
        "chipset-specific state machine bug where malformed PIN values are accepted",
        "monitor+injection-capable interface + reaver-family tool that accepts custom PIN inputs",
    ],
    "wps-locked-bypass-timing": [
        "target enters WPS-Locked after N failures",
        "lockout duration is finite and predictable (typically 60-300 s)",
    ],
    "wps-pbc-window-abuse": [
        "target user just pressed the WPS push-button",
        "attacker in RF range during the 2-minute PBC window",
    ],
    "krack-groupkey-reinstall": [
        "unpatched client",
        "attacker can replay the group-key handshake message from a MitM position",
    ],
    "krack-wnm-reinstall": [
        "client supports 802.11v WNM Sleep Mode",
        "unpatched WNM implementation on the client",
    ],
    "fragattacks-cache-poisoning": [
        "target client retains fragmentation cache across (re)connect",
        "attacker injects during the reconnect window",
    ],
    "sae-h2e-followup-side-channel": [
        "H2E-capable SAE stack with residual timing leakage under specific conditions",
        "on-path or co-located measurement vantage",
    ],
    "dragonblood-modp-downgrade": [
        "attacker brings up rogue AP advertising only weak MODP groups",
        "target client accepts MODP fallback in SAE Group Negotiation",
    ],
    "ft-r0-shared-fleet-crack": [
        "misconfigured 11r deployment sharing PMK-R0 across all BSSIDs in the mobility domain",
        "captured FT reassoc from any one BSSID in the mobility domain",
    ],
    "eap-gtc-plaintext-token-capture": [
        "client tolerates PEAP → GTC inner-method downgrade",
        "target uses OTP-style GTC token (RSA / Duo / Yubico)",
    ],
    "mdm-profile-theft-captive-portal": [
        "victim's enterprise WiFi profile can be reinstalled from a captive portal",
        "captive portal serves a fake MDM enrollment page under a plausible cert",
    ],
    "mschapv2-challenge-response-capture": [
        "captured MSCHAPv2 exchange from rogue-RADIUS or inner-EAP downgrade",
        "GPU or asleap for the offline crack",
    ],
    "default-psk-bt-home-hub": [
        "target SSID matches BTHub<N>-.+ pattern",
        "no radio time required — pure passive derivation",
    ],
    "default-psk-sky-broadband": [
        "target SSID matches ^SKY[0-9A-Z]{5}$",
        "no radio time required — pure passive derivation",
    ],
    "default-psk-livebox-sagemcom": [
        "target SSID matches ^Livebox-.{4}$",
        "no radio time required — pure passive derivation",
    ],
    "default-psk-netgear-genie": [
        "target SSID matches ^NETGEAR\\d{2}$",
        "target AP is from Netgear's 2011–2020 Genie firmware generation",
    ],
    "default-psk-technicolor": [
        "target SSID matches ^Technicolor.+$",
        "no radio time required — pure passive derivation",
    ],
    "csa-rogue-channel": [
        "target client honors unauthenticated CSA (legacy driver / firmware)",
        "monitor+injection-capable interface",
    ],
    "wnm-sleep-mode-abuse": [
        "target client with unpatched 802.11v WNM implementation",
        "monitor+injection-capable interface",
    ],
    "tdls-teardown-injection": [
        "two clients set up a TDLS direct link",
        "monitor+injection-capable interface in RF range of both",
    ],
    "ap-fuzzed-ies-crash": [
        "victim client with vulnerable driver / firmware",
        "monitor+injection-capable interface + fuzzer or crafted-IE beacon source",
    ],
    "eapol-4way-nonce-reuse": [
        "prior passive capture of a KRACK-triggered nonce-reuse event",
        "wireshark or equivalent decode of the 4-way messages",
    ],
    "band-steering-abuse": [
        "target fleet uses band-steering (5 GHz preference on capable clients)",
        "attacker can jam or spoof congestion on the target's preferred band",
    ],
    "krack-groupkey-broadcast-replay": [
        "unpatched client",
        "attacker replays a broadcast frame from a MitM vantage",
    ],
    "wps-hcxlabtool-aggressive": [
        "monitor-mode interface with injection support",
        "target airspace with WPS-enabled APs and PMKID leakage across the sweep",
    ],
    "wpa2-4way-capture": [
        "target uses WPA2-PSK (AKM 2 in RSN IE)",
        "a client is present and (re)associating (targeted deauth is the standard trigger)",
        "monitor+injection-capable interface",
    ],
    "framing-frames-power-save-poison-precond-example": [],
}


# ---------------------------------------------------------------------------
# A3 — tools depth. Chain: capture → convert → crack, not just the last step.
# ---------------------------------------------------------------------------

TOOLS: dict[str, list[str]] = {
    "wep-ptw": [
        "airodump-ng (capture IVs)",
        "aireplay-ng -3 (ARP-replay for IV acceleration)",
        "aircrack-ng -z (PTW attack mode — default)",
    ],
    "wep-korek": ["airodump-ng (capture IVs)", "aircrack-ng -K (KoreK attack mode)"],
    "wep-arp-request-replay": [
        "airodump-ng (capture)",
        "aireplay-ng -3 (ARP-replay)",
        "aircrack-ng (feed replayed IVs into FMS/KoreK/PTW)",
    ],
    "tkip-beck-tews-mic-recovery": [
        "airodump-ng (capture QoS traffic)",
        "aireplay-ng (Beck-Tews custom script or tkiptun-ng)",
        "wireshark (verify Michael MIC recovery)",
    ],
    "wps-reaver-online": [
        "airodump-ng (identify WPS-capable target)",
        "reaver -i <iface> -b <bssid> -c <channel>",
        "bully (alternate implementation)",
    ],
    "wps-pixie-dust": [
        "reaver --pixie-dust (single-exchange capture)",
        "pixiewps (offline solve on E-S1/E-S2)",
    ],
    "wps-null-pin": [
        "reaver --pin='' (empty-PIN attempt)",
        "airodump-ng (verify PSK against captured handshake)",
    ],
    "wps-vendor-pin-derivation": [
        "airodump-ng (WPS Manufacturer/Model IE from beacon)",
        "WPSpin or OneShotPin (generate candidate PINs from vendor derivation)",
        "reaver -p <candidate>",
    ],
    "krack-client-key-reinstall": [
        "krackattacks-scripts (Vanhoef PoC — sets up MC-MitM and replays M3)",
        "airodump-ng (verify nonce reuse)",
        "wireshark (decrypt with recovered PTK)",
    ],
    "krack-linux-all-zero-ptk": [
        "krackattacks-scripts",
        "wireshark (decrypt post-replay frames with all-zero PTK)",
    ],
    "krack-ft-reassoc": [
        "krackattacks-scripts (FT reassoc replay mode)",
        "airodump-ng (capture the reassoc + subsequent traffic)",
    ],
    "dragonblood-sidechannel": [
        "dragondrain (drive SAE exchanges)",
        "dragontime or custom cache-timing harness",
    ],
    "dragonblood-timing": [
        "dragontime (Vanhoef PoC — measures MODP handshake time)",
        "custom analysis scripts to solve the password from timing samples",
    ],
    "wpa3-transition-downgrade": [
        "hostapd (rogue advertising WPA2-only RSN IE)",
        "airodump-ng + aireplay-ng (force reassoc)",
        "hcxpcapngtool + hashcat -m 22000 (crack the recovered WPA2 handshake)",
    ],
    "kr00k-broadcom-cve-2019-15126": [
        "aireplay-ng --disassoc (trigger)",
        "airodump-ng (capture the post-disassoc tail)",
        "wireshark (decrypt with all-zero PTK)",
    ],
    "kr00k-qca-cve-2020-3702": [
        "aireplay-ng --disassoc",
        "airodump-ng",
        "wireshark (all-zero PTK decrypt)",
    ],
    "fragattacks-plaintext-inject": [
        "fragattack.py (Vanhoef PoC)",
        "monitor+injection interface with a supported driver (see the paper's testbed)",
    ],
    "fragattacks-mixed-key": [
        "fragattack.py",
        "wireshark to observe the reassembled cross-key plaintext",
    ],
    "ssid-confusion-cve-2023-52424": [
        "custom hostapd fork advertising the target SSID over a different network (same PSK)",
        "aireplay-ng (optional — force roam)",
        "wireshark (observe the client's higher-layer policy response)",
    ],
    "framing-frames-power-save-poison": [
        "Vanhoef PoC scripts (framing-frames repo)",
        "airodump-ng (verify PM-bit manipulation on the wire)",
    ],
    "macstealer-mac-hijack": [
        "Vanhoef PoC (macstealer-scripts)",
        "wireshark (verify traffic hijack path)",
    ],
    "wifi7-mlo-link-desync": [
        "research PoCs — evolving",
        "MLO-capable AP + client testbed (as of 2026, no public tool ships with automated exploitation)",
    ],
    "ft-handshake-capture": [
        "hcxdumptool (capture the FT reassoc)",
        "hcxpcapngtool (convert to 22000)",
        "hashcat -m 22000 (crack)",
    ],
    "btm-forced-roam": [
        "scapy (craft Dot11 Action / WNM BTM Request)",
        "custom hostapd patch that emits BTM Requests on demand",
    ],
    "neighbor-report-spoof": [
        "scapy (craft Dot11 Action Neighbor Report Response)",
        "custom hostapd patch that emits solicited Neighbor Reports",
    ],
    "anqp-realm-enum": [
        "hostapd_cli anqp-get (query as an associated STA)",
        "scapy GAS Initial Request (pre-association)",
    ],
    "passpoint-roaming-consortium-spoof": [
        "hostapd (custom Roaming Consortium OI in the beacon)",
        "airodump-ng (verify the Passpoint client auto-associates)",
    ],
    "mc-mitm-dual-radio": [
        "hostapd (rogue AP on channel B)",
        "channel-hop scripts on the second radio",
        "aireplay-ng -0 (kick client off the legit AP so it lands on the rogue)",
    ],
    "deauth-targeted": [
        "airodump-ng (identify target AP + client MAC)",
        "aireplay-ng -0 <count> -a <bssid> -c <client> <iface>",
        "mdk4 d (alternate)",
    ],
    "disassoc-targeted": [
        "aireplay-ng --disassoc",
        "airodump-ng (capture the resulting tail on Kr00k targets)",
    ],
    "beacon-flood-mdk4": [
        "mdk4 <iface> b -f <ssidlist> (SSID list)",
        "airodump-ng (verify the flood on the air)",
    ],
    "probe-flood-mdk4": [
        "mdk4 <iface> p -f <ssidlist>",
        "airodump-ng (verify)",
    ],
    "authentication-flood": [
        "mdk4 a",
        "airodump-ng (verify AP state-table pressure)",
    ],
    "association-flood": [
        "mdk4 a --auth",
        "airodump-ng",
    ],
    "eapol-start-flood": [
        "custom scapy 802.1X EAPOL-Start emitter",
        "wired vantage or associated STA for injection",
    ],
    "rts-cts-nav-dos": [
        "mdk4 v",
        "airodump-ng (verify airtime collapse)",
    ],
    "cts-to-self-silencing": [
        "scapy Dot11 CTS (Duration field high)",
        "aireplay-ng (alternate)",
    ],
    "tkip-michael-mic-dos": [
        "mdk4 m",
        "airodump-ng (verify Michael countermeasure engagement)",
    ],
    "captive-portal-cred-capture": [
        "hostapd (rogue AP)",
        "dnsmasq (DHCP + DNS redirect)",
        "nginx / evil-portal template (HTTP + login form)",
    ],
    "rogue-radius-hostapd-wpe": [
        "hostapd-wpe (rogue AP + rogue RADIUS in one)",
        "freeradius-wpe (alternate)",
        "hashcat -m 5500 or asleap (crack the captured MSCHAPv2 pair)",
    ],
    "rogue-radius-eaphammer": [
        "eaphammer --interface <iface> --essid <target-ssid> --cred",
        "airodump-ng (verify client association to the rogue)",
    ],
    "cert-phish-eaphammer-weak-validation": [
        "eaphammer --cert-phish",
        "airodump-ng (target-client selection)",
    ],
    "eap-inner-downgrade-peap-mschapv2": [
        "eaphammer --negotiate downgrade",
        "hostapd-wpe (alternate)",
    ],
    "eap-inner-downgrade-peap-gtc": [
        "eaphammer --negotiate gtc",
    ],
    "asleap-mschapv2-crack": [
        "asleap -C <challenge> -R <response> -W <wordlist>",
    ],
    "hashcat-5500-mschapv2-crack": [
        "hashcat -m 5500 <mschapv2.txt> <wordlist> [-r rules]",
    ],
    "leap-legacy-crack": [
        "asleap or hashcat -m 5500 / -m 4800",
    ],
    "default-psk-upc-ubee": [
        "airodump-ng (SSID identification)",
        "upc_keys (candidate PSK generator)",
        "hashcat -m 22000 (validate against a captured PMKID/handshake)",
    ],
    "default-psk-thomson-speedtouch": [
        "airodump-ng",
        "stkeys (candidate generator)",
        "hashcat -m 22000 (validate)",
    ],
    "pineap-passive-probe-log": [
        "PineAP module — Logging tab (WebUI)",
        "/api/pineap/probes (API)",
    ],
    "pineap-active-karma": [
        "PineAP module — Karma toggle (WebUI)",
        "/api/pineap/settings (API)",
    ],
    "pineap-ssid-pool-broadcast": [
        "PineAP module — SSID Pool → Broadcast (WebUI)",
        "/api/pineap/pool/add + settings.broadcast_ssid_pool (API)",
    ],
    "rnr-6ghz-enumeration": [
        "wireshark filter wlan.rnr",
        "tshark -Y 'wlan.tag.number==201'",
    ],
    "ru-based-ofdma-dos": [
        "research PoCs — no shipping tool as of 2026",
        "custom scapy patch for HE Trigger frames",
    ],
    "packet-inject-arbitrary": [
        "aireplay-ng -9 (test mode)",
        "scapy sendp with RadioTap+Dot11",
        "airbase-ng (alternate)",
    ],
    "beacon-stego-vendor-ie": [
        "airodump-ng (capture)",
        "tshark -Y 'wlan.tag.number==221 && wlan.tag.oui==<custom>'",
        "scapy (decode custom OUI payload)",
    ],
    "wps-negative-pin": [
        "reaver with a custom PIN value (--pin=<n>)",
        "oneshotpin fork with negative-PIN payloads",
    ],
    "wps-locked-bypass-timing": [
        "reaver -d 60 (delay between PIN attempts)",
        "wait/resume scripts around WPS-Locked cycles",
    ],
    "wps-pbc-window-abuse": [
        "reaver --pbc",
    ],
    "krack-groupkey-reinstall": [
        "krackattacks-scripts (group-key mode)",
    ],
    "krack-wnm-reinstall": [
        "krackattacks-scripts (WNM subset)",
    ],
    "fragattacks-cache-poisoning": [
        "fragattack.py",
        "wireshark (verify cross-connect fragment reassembly)",
    ],
    "sae-h2e-followup-side-channel": [
        "research PoCs — no shipping tool as of 2026",
    ],
    "dragonblood-modp-downgrade": [
        "custom hostapd with sae_groups=MODP-only",
        "airodump-ng (verify client accepts the group)",
    ],
    "ft-r0-shared-fleet-crack": [
        "airodump-ng (capture FT reassoc on any BSSID in the mobility domain)",
        "hcxpcapngtool (convert to 22000)",
        "hashcat -m 22000 (crack — one PSK works for the whole fleet)",
    ],
    "eap-gtc-plaintext-token-capture": [
        "eaphammer --negotiate gtc",
        "airodump-ng (capture EAP inner exchange)",
    ],
    "mdm-profile-theft-captive-portal": [
        "custom captive portal + apple/msi profile MIME types",
        "hostapd (rogue AP hosting the portal)",
    ],
    "mschapv2-challenge-response-capture": [
        "hostapd-wpe / eaphammer (capture inner or outer MSCHAPv2)",
        "hashcat -m 5500 / asleap (crack offline)",
    ],
    "default-psk-bt-home-hub": [
        "airodump-ng (SSID identification)",
        "candidate PSK generators (BTHub-specific)",
        "hashcat -m 22000 (validate)",
    ],
    "default-psk-sky-broadband": [
        "airodump-ng",
        "candidate PSK generators (Sky-specific)",
        "hashcat -m 22000 (validate)",
    ],
    "default-psk-livebox-sagemcom": [
        "airodump-ng",
        "candidate PSK generators (Livebox-specific)",
        "hashcat -m 22000 (validate)",
    ],
    "default-psk-netgear-genie": [
        "airodump-ng",
        "adjective-noun-3digits generator (Netgear Genie pattern)",
        "hashcat -m 22000 (validate)",
    ],
    "default-psk-technicolor": [
        "airodump-ng",
        "candidate PSK generators (Technicolor-specific)",
        "hashcat -m 22000 (validate)",
    ],
    "csa-rogue-channel": [
        "scapy Dot11 CSA IE injection",
        "airodump-ng (verify client tuning to rogue channel)",
    ],
    "wnm-sleep-mode-abuse": [
        "krackattacks-scripts (WNM subset)",
    ],
    "tdls-teardown-injection": [
        "scapy Dot11 TDLS Teardown Action frame",
        "airodump-ng (verify STA-to-STA traffic returns to AP path)",
    ],
    "ap-fuzzed-ies-crash": [
        "mdk4 f (fuzzer)",
        "scapy (crafted oversized Vendor-Specific IE beacon)",
    ],
    "eapol-4way-nonce-reuse": [
        "airodump-ng (capture)",
        "wireshark (packet-number analysis on the AP-to-STA data stream)",
    ],
    "band-steering-abuse": [
        "mdk4 v (5 GHz NAV)",
        "hostapd (rogue on 2.4 GHz)",
    ],
    "krack-groupkey-broadcast-replay": [
        "krackattacks-scripts",
    ],
    "wps-hcxlabtool-aggressive": [
        "hcxlabtool (aggressive sweep)",
        "hashcat -m 22000 (crack recovered PMKIDs)",
    ],
    # Second-round tools depth — records whose existing tools[] was 1 bullet.
    "mana-karma": [
        "hostapd-mana (per-STA SSID pool)",
        "airodump-ng (verify targeted probe responses on the air)",
    ],
    "mana-loud": [
        "hostapd-mana --loud",
        "airodump-ng (observe the union-broadcast beacons)",
    ],
    "eap-inner-downgrade-peap-gtc": [
        "eaphammer --negotiate gtc",
        "hostapd-wpe (alternate rogue-RADIUS with GTC inner)",
    ],
    "asleap-mschapv2-crack": [
        "asleap -C <challenge> -R <response> -W <wordlist>",
        "hashcat -m 5500 (GPU alternative to asleap for the same input)",
    ],
    "hashcat-5500-mschapv2-crack": [
        "hashcat -m 5500 <mschapv2.txt> <wordlist> [-r rules]",
        "asleap (CPU alternative)",
    ],
    "twt-forced-sleep-abuse": [
        "research PoCs — no shipping tool ships as of 2026",
        "scapy (craft HE TWT Setup Action frames)",
    ],
    "wps-pbc-window-abuse": [
        "reaver --pbc",
        "airodump-ng (spot the WPS activity that indicates a button press)",
    ],
    "krack-groupkey-reinstall": [
        "krackattacks-scripts (group-key mode)",
        "wireshark (decrypt broadcast frames with the reinstalled GTK)",
    ],
    "krack-wnm-reinstall": [
        "krackattacks-scripts (WNM subset)",
        "wireshark (verify PTK reinstall during WNM sleep exchange)",
    ],
    "sae-h2e-followup-side-channel": [
        "research PoCs (community-tracked, no shipping tool as of 2026)",
        "custom cache-timing harness or symbolic-execution analysis",
    ],
    "wnm-sleep-mode-abuse": [
        "krackattacks-scripts (subset)",
        "custom scapy WNM-Sleep-Mode Action frames",
    ],
    "krack-groupkey-broadcast-replay": [
        "krackattacks-scripts",
        "airodump-ng (capture the broadcast to replay)",
    ],
}


# ---------------------------------------------------------------------------
# A4 — frontier notes. Tier-1.5 records get a paper title + year + why.
# ---------------------------------------------------------------------------

FRONTIER_NOTES: dict[str, str] = {
    "kr00k-broadcom-cve-2019-15126": (
        "Paper: 'KrØØk — CVE-2019-15126: Serious vulnerability deep inside your Wi-Fi encryption' "
        "(ESET, RSA 2020). Chipset side: Broadcom / Cypress. Still lands in 2026 because Echo, "
        "Kindle, and cheap IP cameras from the 2016–2019 generation shipped with vulnerable "
        "firmware and never received the fix."
    ),
    "kr00k-qca-cve-2020-3702": (
        "Paper: ESET 2020 follow-up disclosing the Qualcomm-Atheros variant. Same all-zero-PTK "
        "primitive on QCA-based clients. Still relevant in 2026 for embedded / IoT gear that "
        "predates the 2020 firmware update wave."
    ),
    "ssid-confusion-cve-2023-52424": (
        "Paper: Vanhoef & Yseboodt, 'SSID Confusion: Making Wi-Fi clients connect to the wrong "
        "network' (2024, top10vpn co-disclosure). CVE-2023-52424. Still lands in 2026 because the "
        "802.11 fix (SSID-in-4-way binding) is not universally deployed and many client stacks "
        "still trust the beacon-declared SSID at the higher-layer policy tier."
    ),
    "framing-frames-power-save-poison": (
        "Paper: Vanhoef et al., 'Framing Frames: Bypassing Wi-Fi Encryption by Manipulating "
        "Transmit Queues' (USENIX Security 2023). Still lands in 2026 because AP-side fixes rolled "
        "in gradually across hostapd forks — many production APs, especially consumer models, are "
        "unpatched or partially patched."
    ),
    "macstealer-mac-hijack": (
        "Paper: Vanhoef, 'MacStealer' (BlackHat Asia 2023). Client-side flaw — even fully patched "
        "APs cannot fully defend when the client stack accepts stale MAC-keyed state. Still lands "
        "in 2026 across the same client generations that inherit the SSID-confusion attack surface."
    ),
    "wifi7-mlo-link-desync": (
        "Frontier — no single canonical paper yet as of mid-2026. Research vectors: IEEE 802.11be-"
        "2024 §35 (MLO framing), disclosed at DEF CON 32 / WISEC 2024 in preliminary form. "
        "802.11be errata under IEEE Task Group be track for the link-binding fix. Expect a "
        "published PoC at DEF CON 33 / 34."
    ),
    "twt-forced-sleep-abuse": (
        "Primary source: IEEE 802.11ax-2021 §26.8 (TWT). Attack surface first surveyed in "
        "'Wi-Fi 6 security — TWT abuse' academic papers 2021–2023. Still lands in 2026 because AP-"
        "side MFP protection for TWT Setup Action frames is not consistently deployed."
    ),
    "rnr-6ghz-enumeration": (
        "Primary source: IEEE 802.11ax-2021 §9.4.2.170 (RNR element). Not a vulnerability — a "
        "design feature. Still WCTF-relevant in 2026 because 6 GHz targets remain enumerable from "
        "2.4/5 GHz beacons without a 6 GHz capable card."
    ),
    "ru-based-ofdma-dos": (
        "Community research surface — 'malformed OFDMA Trigger frame DoS.' No canonical paper as "
        "of mid-2026; expect defensive research at WISEC / USENIX 2026. Still WCTF-relevant if a "
        "puzzle tests DoS-detection instrumentation."
    ),
    "ft-handshake-capture": (
        "Primary sources: IEEE 802.11-2020 §13 (Fast BSS Transition), hashcat mode 22000 docs. "
        "Frontier-adjacent — still lands in 2026 because FT-PSK captures are hashcat-crackable "
        "identically to plain 4-way captures, and enterprise FT-PSK deployments continue to "
        "grow."
    ),
    "ft-r0-shared-fleet-crack": (
        "Primary source: IEEE 802.11-2020 §13.2. Not a paper — a misconfiguration class. Still "
        "lands in 2026 because 11r deployments continue to reuse PMK-R0 across fleets in "
        "carrier / hospitality environments."
    ),
    "mc-mitm-dual-radio": (
        "Primary source: Vanhoef & Piessens, KRACK paper (CCS 2017, §5). Also underlies most "
        "post-2017 evil-twin flow that has to survive PMF. Still lands in 2026 as a primitive."
    ),
    "sae-h2e-followup-side-channel": (
        "Follow-up research to Vanhoef's Dragonblood (2019); community-tracked as 'H2E residual "
        "leakage.' No CVE issued as of mid-2026 for the specific residual paths. Still relevant "
        "because some 2021+ SAE stacks did not fully close the timing gap."
    ),
    "dragonblood-modp-downgrade": (
        "Paper: Vanhoef & Ronen, 'Dragonblood: A Security Analysis of WPA3's SAE Handshake' "
        "(2019). Still lands in 2026 wherever hostapd's `sae_groups` still permits MODP fallback."
    ),
    "eap-gtc-plaintext-token-capture": (
        "Primary sources: RFC 3748 §5.3 (EAP-GTC), Gabriel Ryan's eaphammer README (2017–). "
        "Still lands in 2026 in enterprise networks that permit PEAP → GTC downgrade for RSA / "
        "Duo / Yubico OTP flows."
    ),
    "mdm-profile-theft-captive-portal": (
        "Community research surface — no single canonical paper. Primary vector: Apple's mobile "
        "config profile install prompt + Android profile intents. Still lands in 2026 wherever "
        "MDM enrollment can be initiated from a captive portal on managed devices."
    ),
}


# ---------------------------------------------------------------------------
# A5 — missing Appendix-B records. 8 new attacks; 3 aliasable renames.
# ---------------------------------------------------------------------------

NEW_ATTACK_RECORDS: list[dict] = [
    {
        "id": "pmk-crack-mask-attack",
        "name": "PSK crack — hashcat mask attack against a captured 22000 line",
        "aliases": ["pmk-mask", "hashcat-mask-wpa"],
        "category": "attack",
        "region": "universal",
        "era_bounds": ["2011", None],
        "still_effective_2026": True,
        "confidence": "primary",
        "citations": ["hashcat-modes"],
        "see_also": [
            "hashcat-mode-22000",
            "hashcat-attack-mode-3",
            "wpa2-4way-capture",
            "pmkid-capture",
        ],
        "target_security": ["km-wpa2-psk"],
        "preconditions": [
            "captured 4-way handshake or PMKID (WPA*01 or WPA*02 line in a .22000 file)",
            "known or suspected mask shape (e.g. /^[A-Z]{4}[0-9]{6}$/ for many default PSKs)",
        ],
        "tools": [
            "hashcat -m 22000 -a 3 <hs.22000> '<mask>'",
            "maskprocessor (mp64) for candidate generation preview",
            "hashcat --custom-charset1..4 for domain-specific alphabets",
        ],
        "hashcat_mode": 22000,
        "transport": "analysis",
        "mitigation": ["strong PSK (12+ chars mixed alpha+digit+symbol) makes a mask impractical"],
        "flag_signature": "recovered PSK (the WCTF flag), assuming the mask covers the true shape",
        "notes": (
            "The default-PSK sibling of the straight-wordlist attack. Load-bearing whenever the "
            "target is a router with a documented factory PSK format — the mask attack outpaces "
            "any wordlist on that shape."
        ),
    },
    {
        "id": "pmk-crack-hybrid",
        "name": "PSK crack — hashcat hybrid (wordlist + mask) against a captured 22000 line",
        "aliases": ["pmk-hybrid"],
        "category": "attack",
        "region": "universal",
        "era_bounds": ["2011", None],
        "still_effective_2026": True,
        "confidence": "primary",
        "citations": ["hashcat-modes"],
        "see_also": [
            "hashcat-mode-22000",
            "hashcat-attack-mode-6",
            "hashcat-attack-mode-7",
            "wpa2-4way-capture",
        ],
        "target_security": ["km-wpa2-psk"],
        "preconditions": [
            "captured 4-way handshake or PMKID as a .22000 line",
            "candidate wordlist and a plausible append/prepend mask (e.g. 'YYYY' or '?d?d?d?d')",
        ],
        "tools": [
            "hashcat -m 22000 -a 6 <hs.22000> <wordlist> '?d?d?d?d' (append year/pattern)",
            "hashcat -m 22000 -a 7 <hs.22000> '?u?l?l?l' <wordlist> (prepend)",
            "cewl / crunch / psudohash for wordlist generation",
        ],
        "hashcat_mode": 22000,
        "transport": "analysis",
        "mitigation": ["strong PSK — the hybrid attack targets 'realword + suffix' patterns"],
        "flag_signature": "recovered PSK (the WCTF flag)",
        "notes": (
            "Second workhorse after straight -a 0. Load-bearing for 'password2024', 'admin1234', "
            "'CONFERENCE!2026' style PSKs."
        ),
    },
    {
        "id": "pmk-crack-hashcat",
        "name": "PSK crack — hashcat straight-wordlist against a captured 22000 line",
        "aliases": ["pmk-straight", "hashcat-wpa"],
        "category": "attack",
        "region": "universal",
        "era_bounds": ["2011", None],
        "still_effective_2026": True,
        "confidence": "primary",
        "citations": ["hashcat-modes"],
        "see_also": [
            "hashcat-mode-22000",
            "hashcat-attack-mode-0",
            "wpa2-4way-capture",
            "pmkid-capture",
        ],
        "target_security": ["km-wpa2-psk"],
        "preconditions": [
            "captured 4-way handshake or PMKID as a .22000 line",
            "wordlist that plausibly contains the PSK (rockyou.txt, venue-specific dictionary)",
        ],
        "tools": [
            "hashcat -m 22000 -a 0 <hs.22000> <wordlist> [-r rules/best64.rule]",
            "hcxpcapngtool (produce the 22000 line from a pcap)",
        ],
        "hashcat_mode": 22000,
        "transport": "analysis",
        "mitigation": [
            "strong PSK not present in any public wordlist",
            "WPA3-SAE eliminates the offline crack path",
        ],
        "flag_signature": "recovered PSK (the WCTF flag)",
        "notes": (
            "The workhorse. Cover record for what most WCTF operators mean by 'crack the "
            "handshake.' Subsumes prose in cracking-tradecraft/ walkthroughs."
        ),
    },
    {
        "id": "tim-dtim-poison",
        "name": "TIM/DTIM element poisoning (power-save queue exhaustion)",
        "aliases": ["tim-poison", "dtim-flood"],
        "category": "attack",
        "region": "universal",
        "era_bounds": ["2005", None],
        "still_effective_2026": True,
        "confidence": "community",
        "citations": ["ieee-802-11-2020"],
        "see_also": ["ie-tim", "framing-frames-power-save-poison"],
        "target_security": ["km-wpa2-psk", "km-open"],
        "preconditions": [
            "target AP or clients honor the TIM bitmap for power-save signaling",
            "monitor+injection-capable interface",
        ],
        "tools": [
            "scapy (craft Dot11Beacon with a manipulated TIM element)",
            "mdk4 f (fuzzer with beacon-IE injection modes)",
        ],
        "hashcat_mode": None,
        "transport": "ssh",
        "mitigation": [
            "AP-side rate limit on TIM anomalies at the WIDS",
            "client-side ignore-suspicious-TIM heuristics (rare)",
        ],
        "flag_signature": None,
        "notes": (
            "Precursor to Framing Frames. DoS-flavored — clients that trust the TIM bitmap can "
            "be starved of receive time by malformed or attacker-forged beacon TIM entries."
        ),
    },
    {
        "id": "snoopy-track",
        "name": "Snoopy — geographic probe-request tracking (SensePost 2012)",
        "aliases": ["snoopy"],
        "category": "attack",
        "region": "universal",
        "era_bounds": ["2012", None],
        "still_effective_2026": True,
        "confidence": "primary",
        "citations": ["sensepost-mana-2014"],
        "see_also": ["mana-karma", "karma-snoopy", "frame-mgmt-probe-request"],
        "target_security": ["km-open"],
        "preconditions": [
            "monitor-mode interface at multiple geographic points",
            "target clients that emit directed probe requests (not fully randomized)",
        ],
        "tools": [
            "Snoopy (the SensePost drone-borne framework)",
            "airodump-ng --write-interval and geolocation correlation",
        ],
        "hashcat_mode": None,
        "transport": "analysis",
        "mitigation": [
            "client-side probe-request MAC randomization (mitigates but does not fully prevent — "
            "sequence number continuity across randomizations is a residual signal)",
            "'associate only on explicit selection' policy",
        ],
        "flag_signature": (
            "target device's location trajectory inferred from probe-history correlation across "
            "sensor points"
        ),
        "notes": (
            "Older recon primitive but 2026-relevant because IE ordering and sequence-number "
            "continuity still allow cross-randomization correlation on many stacks. See "
            "client_fingerprints.json."
        ),
    },
    {
        "id": "broadpwn-broadcom-cve-2017-11120",
        "name": "Broadpwn — Broadcom Wi-Fi firmware RCE (CVE-2017-11120)",
        "aliases": ["broadpwn"],
        "category": "attack",
        "region": "universal",
        "era_bounds": ["2017-07", None],
        "still_effective_2026": True,
        "confidence": "primary",
        "citations": ["ieee-802-11-2020"],
        "see_also": [
            "chipset-broadcom-bcm43xx-broadpwn",
            "cve-2017-11120",
            "frame-mgmt-assoc-request",
        ],
        "target_security": ["km-wpa2-psk", "km-open"],
        "preconditions": [
            "target client uses a vulnerable Broadcom BCM43xx chipset with pre-July-2017 firmware",
            "attacker in RF range with a supported injection card",
        ],
        "tools": [
            "Nitay Artenstein PoC (BlackHat 2017)",
            "monitor+injection-capable interface (Alfa AWUS036ACH or similar)",
        ],
        "hashcat_mode": None,
        "transport": "ssh",
        "mitigation": ["patched Broadcom firmware (Apple iOS 10.3.3, Android Aug 2017 security bulletin)"],
        "flag_signature": (
            "code execution in the Broadcom Wi-Fi firmware — flag depends on the WCTF puzzle "
            "(e.g. attacker-controlled memory read, association-time RCE payload delivered)"
        ),
        "notes": (
            "Legacy but still lands in 2026 against the same unpatched IoT / older Android "
            "generation that hosts kr00k. Included for chipset-vuln coverage across the era-authentic "
            "hits Appendix B calls out."
        ),
    },
    {
        "id": "realtek-rtl87xx-cve-2021-28492",
        "name": "Realtek RTL8xxx family — Wi-Fi driver stack overflow (CVE-2021-28492)",
        "aliases": ["realtek-rtl87xx-cve"],
        "category": "attack",
        "region": "universal",
        "era_bounds": ["2021-04", None],
        "still_effective_2026": True,
        "confidence": "primary",
        "citations": ["ieee-802-11-2020"],
        "see_also": ["chipset-realtek-rtl8xxx-cve-2021-28492", "cve-2021-28492"],
        "target_security": ["km-wpa2-psk", "km-open"],
        "preconditions": [
            "target AP or client uses a vulnerable Realtek RTL87xx family Wi-Fi driver",
            "attacker in RF range with monitor+injection interface",
        ],
        "tools": [
            "public PoCs from ESET / Vdoo disclosure",
            "monitor+injection-capable interface",
        ],
        "hashcat_mode": None,
        "transport": "ssh",
        "mitigation": ["patched Realtek driver / firmware"],
        "flag_signature": (
            "stack-overflow-driven code execution or crash in the vulnerable driver — flag is "
            "puzzle-specific"
        ),
        "notes": (
            "Cheap IoT gear and consumer routers on Realtek chipsets remain in the field. "
            "Legacy-adjacent primitive, but useful in a WCTF that surfaces a chipset-fingerprint "
            "recognition path first."
        ),
    },
    {
        "id": "scapy-crafted-beacon-with-vendor-stego",
        "name": "Crafted-beacon-with-Vendor-Specific-IE stego (scapy-native workflow)",
        "aliases": ["scapy-beacon-stego"],
        "category": "attack",
        "region": "universal",
        "era_bounds": ["2010", None],
        "still_effective_2026": True,
        "confidence": "community",
        "citations": ["ieee-802-11-2020"],
        "see_also": [
            "beacon-stego-vendor-ie",
            "ie-vendor-specific",
            "frame-mgmt-beacon",
        ],
        "target_security": ["km-open"],
        "preconditions": [
            "monitor+injection-capable interface (attacker side)",
            "target has a passive capture in range for enough beacon intervals to reassemble",
        ],
        "tools": [
            "scapy (Dot11 + Dot11Beacon + Dot11EltVendorSpecific)",
            "airbase-ng (alternate rogue-beacon source)",
            "wireshark (verify on capture side)",
        ],
        "hashcat_mode": None,
        "transport": "ssh",
        "mitigation": [
            "detection-only — the primitive is 'attacker emits a legal 802.11 frame with attacker "
            "content in the Vendor-Specific IE'; there is no cryptographic defense"
        ],
        "flag_signature": (
            "flag reassembled from a custom OUI Vendor-Specific IE across many beacons (companion "
            "to beacon-stego-vendor-ie which describes the capture side)"
        ),
        "notes": (
            "The scapy-crafted-beacon variant Appendix B names distinct from the passive-capture "
            "beacon-stego-vendor-ie record. This one covers the attacker's transmit workflow — "
            "how to author, encode, and beacon a multi-frame payload from a laptop or Pineapple."
        ),
    },
]


# 3 aliasable renames — add the shorter/alt slugs as aliases on existing records.
ALIAS_ADDITIONS: dict[str, list[str]] = {
    "kr00k-qca-cve-2020-3702": ["kr00k-qualcomm-cve-2020-3702"],
    "packet-inject-arbitrary": ["frame-injection-arbitrary"],
}


# ---------------------------------------------------------------------------
# core pass
# ---------------------------------------------------------------------------


def apply(records: list[dict]) -> list[dict]:
    by_id = {r["id"]: r for r in records}

    # A1 — flag_signature
    for rid, sig in FLAG_SIGNATURES.items():
        rec = by_id.get(rid)
        if rec is None:
            continue
        # Only add if missing. Never overwrite an existing author-preferred string.
        if "flag_signature" not in rec:
            rec["flag_signature"] = sig  # may be None (JSON null) by design

    # Second pass: any attack that STILL lacks flag_signature after the map —
    # set it to null explicitly so the field is present.
    for r in records:
        if "flag_signature" not in r:
            r["flag_signature"] = None

    # A2 — mitigation
    for rid, mits in MITIGATIONS.items():
        rec = by_id.get(rid)
        if rec is None:
            continue
        existing = rec.get("mitigation")
        if not existing:
            rec["mitigation"] = mits  # may be None
    # Ensure all records carry the field.
    for r in records:
        if "mitigation" not in r:
            r["mitigation"] = None

    # A3 — preconditions ≥ 2. Replace only when existing count < 2 OR the entry
    # is empty. We never shrink.
    for rid, precs in PRECONDITIONS.items():
        rec = by_id.get(rid)
        if rec is None:
            continue
        if not precs:
            continue
        current = rec.get("preconditions") or []
        if len(current) < len(precs):
            # Merge, preserving the existing bullets first
            seen = set()
            merged: list[str] = []
            for x in list(current) + precs:
                if x in seen:
                    continue
                seen.add(x)
                merged.append(x)
            rec["preconditions"] = merged

    # A3 — tools depth: same logic
    for rid, tools in TOOLS.items():
        rec = by_id.get(rid)
        if rec is None:
            continue
        if not tools:
            continue
        current = rec.get("tools") or []
        if len(current) < len(tools):
            seen = set()
            merged = []
            for x in list(current) + tools:
                if x in seen:
                    continue
                seen.add(x)
                merged.append(x)
            rec["tools"] = merged

    # A4 — frontier notes. Preserve existing notes if present; only add when
    # missing.
    for rid, note in FRONTIER_NOTES.items():
        rec = by_id.get(rid)
        if rec is None:
            continue
        if "notes" not in rec or not rec.get("notes"):
            rec["notes"] = note

    # A5 — aliases on existing records
    for rid, extras in ALIAS_ADDITIONS.items():
        rec = by_id.get(rid)
        if rec is None:
            continue
        current = list(rec.get("aliases") or [])
        for a in extras:
            if a not in current:
                current.append(a)
        rec["aliases"] = current

    # A5 — new records. Insert at the end. Skip any that already exist (idempotent).
    existing_ids = {r["id"] for r in records}
    for new in NEW_ATTACK_RECORDS:
        if new["id"] not in existing_ids:
            records.append(new)

    return records


def main() -> int:
    data = json.loads(ATTACKS.read_text(encoding="utf-8"))
    data = apply(data)
    ATTACKS.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"depth-pass-attacks: wrote {ATTACKS} — {len(data)} records", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
