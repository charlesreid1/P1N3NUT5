# wctf_playbook — operator-facing

The tool orchestration when you land in an unfamiliar WCTF room and
have 20 minutes to score. Structured by subgenre; each section is an
*index* to `knowledge/ctf/*.md` (the authoritative writeup) and to
the MCP tool + `run_sequence` recipe that fits.

## 60-second triage

Mirror the flow in
[`skills/pineapple/SKILL.md § Playbook — first 60 seconds`](../skills/pineapple/SKILL.md).
Short form:

1. `pineapple_status()` — which transport answered? If SSH is down,
   flag it now — every transmit tool will fail later.
2. `run_sequence([{"action":"recon_start","band":"both","dwell_ms":250},{"action":"wait","s":15},{"action":"recon_stop"}])`.
3. `list_aps(seen_since_s=20)`. Sort by security label. Reach for the
   fastest lane: PMKID-in-beacon > WPS-locked > 4-way capture >
   evil-twin > WPA3-transition-downgrade > WPA3-only.

## By subgenre

Every entry cross-references the CTF prose in `knowledge/ctf/`; do
not duplicate it here. Read the prose for the *why*; use the tool
recipe for the *how*.

### hidden-ssid-mazes

Cluster of beacons with the SSID IE zeroed out. Look up:
[`knowledge/ctf/hidden-ssid-mazes.md`](../knowledge/ctf/hidden-ssid-mazes.md).
Tool: `list_probe_requests(seen_since_s=20)` — a client that has ever
seen the network volunteers its SSID on next association. Rarely
needs a shot fired; wait and read the probes.

### pmf-required-targets

Beacon advertises `RSN Capabilities` with MFPR (bit 6) set. Look up:
[`knowledge/ctf/pmf-required-targets.md`](../knowledge/ctf/pmf-required-targets.md).
Tool: `do_deauth(bssid=…, respect_pmf=True)` will refuse with a
citation; the *puzzle* is usually to work another vector (side
channel, portal, cred-flag).

### wpa2-crack-flags

Classic WPA2-PSK. Look up:
[`knowledge/ctf/wpa2-crack-flags.md`](../knowledge/ctf/wpa2-crack-flags.md).
Two lanes:

- **PMKID present.** `capture_pmkid(bssid=…)` →
  `convert_to_hashcat(...)` → `crack_start(mode=22000)`. No client
  needed.
- **PMKID absent, live client.** `capture_handshake(bssid=…,
  deauth_client=<mac>, timeout_s=60)` → same crack tail.

### wpa3-transition-downgrade

RSN IE carries AKM=2 (PSK) *and* AKM=8 (SAE). Look up:
[`knowledge/ctf/wpa3-transition-downgrade.md`](../knowledge/ctf/wpa3-transition-downgrade.md).
Tool: `do_evil_twin(target_bssid=…, target_ssid=…, target_channel=…)`
advertising AKM=2 only; a WPA2-capable client will fall back and
give you a WPA2 4-way. Preconditions matter — a WPA3-only client
won't downgrade.

### evil-twin-farms

Multiple APs advertise the same SSID. Look up:
[`knowledge/ctf/evil-twin-farms.md`](../knowledge/ctf/evil-twin-farms.md).
Tool: `beacon_diff(bssid_a, bssid_b, pcap_path)` (L6) highlights the
odd one out via IE-set diff. For triage, the goal is usually to find
the *real* AP and associate with that.

### captive-portal-cred-flags

Open network that traps HTTP and asks for a login. The flag is what
a user types. Look up:
[`knowledge/ctf/captive-portal-cred-flags.md`](../knowledge/ctf/captive-portal-cred-flags.md).
Tool: `do_create_rogue_ap(ssid=<target>, security="open", channel=<ch>)`
next to the target SSID; deauth clients off; serve a portal that
templates the target's login page. Captive-portal template engine is
deferred (skill file § Deferred).

### pmkid-fastpath

WPA2-PSK with PMKID leaked in M1. Look up:
[`knowledge/ctf/pmkid-fastpath.md`](../knowledge/ctf/pmkid-fastpath.md).
`run_sequence([{"action":"capture_pmkid","bssid":"…"},{"action":"convert_to_hashcat",...},{"action":"crack_start",...}])`.

### beacon-flag-stego

Flag hidden inside a Vendor IE / RSN IE / country IE / custom IE
bytes. Look up:
[`knowledge/ctf/beacon-flag-stego.md`](../knowledge/ctf/beacon-flag-stego.md).
Tool: `parse_pcap` for coarse triage; `decode_ies(pcap_path)` (L6)
for byte-level walk. Also `lookup_ie(element_id)` for the layout.

### probe-request-flag

Flag hidden in the SSID field of a probe request from a specific
client. Look up:
[`knowledge/ctf/probe-request-flag.md`](../knowledge/ctf/probe-request-flag.md).
Tool: `list_probe_requests(seen_since_s=…)`, filter by
`client_mac`.

### deauth-forensics

Given a pcap of a deauth flood, reconstruct: who sent, who received,
did PMF hold? Look up:
[`knowledge/ctf/deauth-forensics.md`](../knowledge/ctf/deauth-forensics.md).
Tool: `parse_pcap(path)` for the frame-type histogram;
`lookup_frame(0, 12)` for deauth field layout.

### rogue-radius-eap-flag

The flag is buried in an EAP inner-method exchange (MSCHAPv2 hash,
GTC plaintext, cert CN). Look up:
[`knowledge/ctf/rogue-radius-eap-flag.md`](../knowledge/ctf/rogue-radius-eap-flag.md).
Tool: full rogue-RADIUS is out of scope (skill file § Deferred).
Read the offline capture with `parse_pcap` and look up the EAP method
via `lookup_eap`.

### wps-pin-flag

WPS is on. Look up:
[`knowledge/ctf/wps-pin-flag.md`](../knowledge/ctf/wps-pin-flag.md).
Tool: no in-MCP WPS PIN attack (uses `reaver`/`bully` on the
Pineapple over SSH). Read the record chain via
`lookup_attack("wps-reaver-online")` for the vendor+chipset gate
data.

### ssid-confusion-flag

CVE-2023-52424: SSID isn't in the 4-way handshake, so a client can be
tricked about which network it's on. Look up:
[`knowledge/ctf/ssid-confusion-flag.md`](../knowledge/ctf/ssid-confusion-flag.md).
Tool: `verify_claim("Do I need the target PSK for SSID Confusion?")`
returns `false` with the reason string.

### kr00k-tail-flag

Broadcom / QCA Kr00k tail on legacy IoT. Look up:
[`knowledge/ctf/kr00k-tail-flag.md`](../knowledge/ctf/kr00k-tail-flag.md).
Tool: `lookup_cve("CVE-2019-15126")` + `parse_pcap` on the tail-end
frames.

### wifi7-mlo-flag

Multi-Link Operation nonce-management surface. Look up:
[`knowledge/ctf/wifi7-mlo-flag.md`](../knowledge/ctf/wifi7-mlo-flag.md).
Tool: `lookup_ie("mld-basic")` for the MLD IE; corpus prose walks
the desync research.

### wifi6e-6ghz-flag

6 GHz-only WPA3 target. Look up:
[`knowledge/ctf/wifi6e-6ghz-flag.md`](../knowledge/ctf/wifi6e-6ghz-flag.md).
Tool: `lookup_channel(N, band=6)` for the reg data; the enumeration
path is often via 2.4 / 5 GHz RNR IEs advertising 6 GHz BSSIDs.

### hotspot2-anqp-flag

ANQP response leaks vendor-specific data. Look up:
[`knowledge/ctf/hotspot2-anqp-flag.md`](../knowledge/ctf/hotspot2-anqp-flag.md).
Tool: `lookup_ie("anqp-*")` for the sub-elements.

### ft-handshake-flag

Fast-Transition roam leaks an M1-analog PMKID. Look up:
[`knowledge/ctf/ft-handshake-flag.md`](../knowledge/ctf/ft-handshake-flag.md).
Tool: `capture_handshake` on the roam target, then `extract_pmkids`.

### framing-frames-flag

FragAttacks-family frame framing tricks. Look up:
[`knowledge/ctf/framing-frames-flag.md`](../knowledge/ctf/framing-frames-flag.md).
Tool: `lookup_attack("fragattacks-plaintext-injection")`.

### cert-phish-eap-flags

Rogue-RADIUS + phished cert acceptance. Look up:
[`knowledge/ctf/cert-phish-eap-flags.md`](../knowledge/ctf/cert-phish-eap-flags.md).
Tool: deferred; see corpus prose.

### default-psk-flags

Vendor default-PSK derivation. Look up:
[`knowledge/ctf/default-psk-flags.md`](../knowledge/ctf/default-psk-flags.md).
Tool: `search_records(category="default_psk", query=<vendor>)` +
the corpus `default-psk-derivation/` prose.

### scoring-recon

Meta — the puzzle is to reconstruct the score itself. Look up:
[`knowledge/ctf/scoring-recon.md`](../knowledge/ctf/scoring-recon.md).

### strategy

Meta — pacing, when to switch puzzles, wordlist selection. Look up:
[`knowledge/ctf/strategy.md`](../knowledge/ctf/strategy.md).

## Legal & consent

Every transmit tool refuses unless `--i-own-the-airspace` is set for
the session or a per-scope `authorization` config is passed. See
[`legal_and_consent.md`](legal_and_consent.md) for the constructor
and refusal semantics.
