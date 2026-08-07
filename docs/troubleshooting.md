# troubleshooting — when the engagement breaks

Read this when a tool call surprised you. Each section is one failure
mode → what to check → what to do. Order is roughly "most common in
practice."

The universal first move: `call_log(ssh=True, api=True)`. Every SSH
command sent, every API path hit, every exit code and stderr. Almost
every failure below has its receipt there.

## F1 — `do_capture_handshake` returned `ok=True` but no EAPOL landed

This is the single biggest engagement-killer. See the deeper diagnostic
in [`handshake_forensics.md`](handshake_forensics.md); the quick
triage:

1. **Did the deauth actually go out?** `call_log()` → look for the
   `aireplay-ng` line. Exit code non-zero → interface wasn't in
   monitor mode. Exit code zero but no traffic on the channel → PMF
   ate the deauth (see F4).
2. **Wrong channel?** `list_aps(bssid_regex="AA:BB:CC:DD:EE:FF")` and
   compare its `channel` to what the capture script was pinned to.
   Recon can lag; the AP may have hopped (5 GHz DFS avoidance,
   auto-channel).
3. **Client not associating?** `list_associations()`. If the target
   client isn't there, it moved rooms, went to sleep, or the deauth
   was too aggressive (10+ deauths and the client's STA gives up for
   a lockout window).
4. **Radio saturated.** Con floors. Move channels or physical
   position; see [`field_notes.md § RF survival`](field_notes.md).

Full diagnostic: [`handshake_forensics.md`](handshake_forensics.md).

## F2 — `crack_start` at 0% after N minutes

1. **Verify the hash file is well-formed.**
   ```
   hcxpcapngtool --info /tmp/hs.pcapng
   ```
   If it reports 0 handshakes or 0 PMKIDs, your `.22000` file is empty
   — the "crack" is instantly complete against nothing. Recapture.
2. **Wrong mode.** `crack_start(mode=…)` — 22000 for modern combined,
   22001 (rare) for known-PMK, 2500 for the old aircrack `.hccapx`
   flow. `lookup_hashcat_mode(22000)` for the record.
3. **Wordlist unresolved.** `crack_start` resolves `wordlist_path`
   against `WORDLIST_DIR` if it's not absolute; if `WORDLIST_DIR` isn't
   set, a bare `rockyou.txt` errors out. Fix env or pass absolute.
4. **Hashcat not on PATH.** `HASHCAT_PATH` env, or a full path.
5. **GPU silently unused.** `hashcat -I` from a shell — if it shows
   only CPU, you're at ~10 kH/s and rockyou is 20 minutes. Wrong
   driver, or the box is running Wayland with GPU access sandboxed.

## F3 — `do_deauth` refused with a PMF cite

The AP advertises `MFPR=1` (mandatory) in its RSN Capabilities. `respect_pmf=True`
is the default and refused correctly. Options:

- **Look for a legacy client.** Sometimes the AP is PMF-required but
  a straggler is grandfathered off-band. Rare; check `list_clients()`.
- **Attack the client side** — the client's probe requests, its
  probe-response acceptance (evil twin), a rogue-RADIUS on a different
  SSID it also trusts.
- **Downgrade path** if the AP is WPA3-transition — see recipe R6 in
  [`recipes.md`](recipes.md).
- **Force with `respect_pmf=False`.** Will no-op against 802.11w-required
  clients but sometimes lands on grandfathered non-PMF stragglers on
  the same AP. Corpus:
  [`knowledge/ctf/pmf-required-targets.md`](../knowledge/ctf/pmf-required-targets.md).

## F4 — `AuthorizationRequired` on a transmit tool

You forgot the airspace flag. Two fixes:

```python
# Sanctioned airspace (WCTF village, your lab, your contract)
run_sequence(steps=[...], i_own_the_airspace=True)

# Scoped engagement (per-target allowlist)
from p1n3nut5_mcp.attacks import Authorization
authz = Authorization(ssid_allowlist=("target-lab-2G",),
                      bssid_allowlist=("aa:bb:cc:dd:ee:ff",))
```

Deeper: [`legal_and_consent.md`](legal_and_consent.md).

## F5 — Pineapple SSH dropped mid-engagement

Symptoms: every `do_*` returns an SSH connection error; API still
works. Order of checks:

1. **Ping the box.** `ping 172.16.42.1` — if that fails, USB tether
   dropped. Reseat the cable; check `dmesg` on the laptop for tether
   re-enumeration.
2. **SSH port reachable.** `nc -zv 172.16.42.1 22`.
3. **dropbear alive.** From WebUI or via the API — the API can restart
   dropbear: `POST /api/system/service/dropbear/restart` (path depends
   on firmware).
4. **Fell back to WebUI-only.** Set `PINEAPPLE_TRANSPORT_PREF=api` and
   keep working on recon + PineAP; transmit tools will refuse until
   SSH is back.
5. **Overheating throttle.** Mk VII under sustained load throttles
   the CPU. Move to a cooler surface, don't sit it on your laptop
   exhaust vent.

## F6 — Rogue AP won't launch

`do_create_rogue_ap` returns `ok=False` and warnings cite `hostapd`:

1. **Channel busy or DFS.** Pick a UNII-1 (36–48) or 2.4 GHz channel
   not in use. Corpus: [`knowledge/hardware-and-antennas/walkthrough.md § Path E`](../knowledge/hardware-and-antennas/walkthrough.md).
2. **Interface already in use.** `do_list_interfaces()` — if wlan1 is
   in `type managed`, hostapd wants monitor+AP. Kill NetworkManager
   equivalents on the Pineapple side: `killall wpa_supplicant` over
   SSH.
3. **hostapd conf syntax error.** `call_log()` shows the exact
   generated conf. Look for missing `wpa_passphrase` (needed for
   `wpa2_psk`), or `wpa_key_mgmt` mismatch.
4. **`security="wpa2_eap"` raises `NotImplementedError`.** Rogue-RADIUS
   is deferred — use eaphammer / hostapd-wpe manually over SSH. See
   [`knowledge/hostapd-wpe/`](../knowledge/hostapd-wpe/).
5. **`MAX_ROGUE_MINUTES` killed it.** Check `list_rogue_aps()`; if
   it's empty and the pid file is gone, an earlier
   `enforce_rogue_limits` reaped it. Bump the env var.

## F7 — API 401 / 429 / 5xx

- **401 Unauthorized.** Token expired or rotated. WebUI →
  Configuration → API → regenerate → update `PINEAPPLE_TOKEN` →
  restart the MCP server so `Config.from_env` re-reads.
- **429 Too Many Requests.** Rate-limited. Two options:
  - `export PINEAPPLE_TRANSPORT_PREF=ssh` and keep working; recon +
    PineAP have SSH fallbacks where declared in
    [`transport_split.md`](transport_split.md).
  - Slow down: increase `dwell_ms` in `recon_start`; batch
    `list_aps` less aggressively.
- **5xx from the WebUI.** Firmware bug or overload. Look in
  `call_log()` for the actual HTTP body — sometimes the WebUI returns
  200 with a JSON error field; sometimes 500 with a traceback. If
  reproducible, upgrade firmware.

## F8 — `parse_pcap` says frame count is 0 on a pcapng that clearly has traffic

1. **File magic.** `xxd -l 4 /path/file` — pcapng is `0a 0d 0d 0a`.
2. **scapy available.** `python -c "import scapy; print(scapy.__version__)"`
   — must be `>= 2.5`. If missing, `pip install .` again; scapy is a
   hard dep since Phase L6.
3. **Truncated file.** If `hcxpcapngtool --info` also says 0, the
   file's malformed. Check whether hcxdumptool was killed mid-flush
   (`kill -9` doesn't SIGTERM its flush loop).
4. **Encrypted data frames only, no beacons or EAPOL.** `parse_pcap`
   summarizes frame types; a pcap of 10k CCMP data frames with no
   management frames looks empty for handshake purposes but is not
   truly empty. Check the summary payload's frame-type histogram.

## F9 — `list_aps` returns fewer APs than you can hear on your phone

1. **Recon not running.** `recon_status()` — if not "running," start
   it. `list_aps` reads a cached DB; if recon is off, you're reading
   stale data.
2. **`seen_since_s` too tight.** `list_aps(seen_since_s=300)` widens
   the window.
3. **Band mismatch.** `recon_start(band="2.4")` won't populate 5 GHz
   entries. Use `"both"`.
4. **Antenna direction.** Directional antenna pointed away from most
   of the room. Rotate.
5. **Regdomain.** 5 GHz DFS channels silent-avoid on some drivers;
   set regdomain (`iw reg set US` over SSH) before recon.

## F10 — `run_sequence` returned `ok=True` overall but a step in the middle failed

Look at `steps[]` in the payload. Every step has its own envelope; a
mid-sequence PMF-refused `deauth` step will have `ok=False` while the
overall call is `ok=True` (the orchestrator continues by design). Two
patterns:

- **Continue-on-error is what you want** (recon + attack + capture:
  losing one attack shouldn't kill the recon+capture flow).
- **Fail-fast is what you want** (crack pipeline: if convert failed,
  don't hit crack_start). Split into two `run_sequence` calls and
  gate on the first's `ok`.

## F11 — Everything works but you can't tell what did what

`call_log(ssh=True, api=True)`. Merged timeline of every command and
API hit with timing. Save the payload to a file — it's the writeup
artifact.

## F12 — Something completely undocumented

1. **`verify_claim("your hypothesis about what's happening")`** — the
   trap catalog covers 22 patterns and the "unverified" verdict tells
   you honestly when it doesn't know.
2. **`search_lore("keyword")`** — the corpus is 55 topic dirs; the
   thing you're seeing has probably been seen before.
3. **`explain_attack("closest-name-you-can-guess")`** — never refuses;
   returns steps + preconditions even for exotic techniques.
4. **`lookup_cve("CVE-…")`** if a CVE ID is in play.

If the tool surface itself is the problem — a call returning a shape
you didn't expect, or an envelope key missing — that's a bug, not a
config issue. `call_log()` payload + `git rev-parse HEAD` are what a
bug report needs.

## When you're really stuck

Move to another puzzle. The scoring math for most CTFs rewards
puzzle-count more than depth on one. See
[`knowledge/ctf/strategy.md § Two-op recon/attack split`](../knowledge/ctf/strategy.md).
