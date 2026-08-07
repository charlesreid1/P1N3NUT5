# handshake_forensics — is this capture good?

Most single-puzzle deaths in a WPA2 crack pipeline happen here: you
captured *something*, `convert_to_hashcat` produced a `.22000` file,
you fed it to hashcat, and it either finished instantly (0
candidates) or crunches forever (crack failing on a bad hash). This
doc is the diagnostic between capture and crack.

## The 30-second check

```python
parse_pcap(path="/tmp/hs.pcapng")
```

Look at the payload's frame-type histogram. You want:

- **Beacons** — target BSSID is present.
- **EAPOL** — at least 2 frames (M1 + M2 minimum for mode 22000
  type=02; M1 alone is enough for type=01 / PMKID).
- **Deauth** (if you fired one) — confirms you transmitted.

Zero EAPOL → nothing to crack. Recapture.

## The definitive check

```
hcxpcapngtool --info /tmp/hs.pcapng
```

Not an MCP tool — run it directly on the box or the laptop after
`scp`. The output tells you exactly what mode-22000 lines will be
produced. Look for:

- **`EAPOL M12/M14/M32/M34`** — pairs that matter.
  - `M12` — M1+M2 seen; the standard mode-22000 type=02 recipe.
  - `M14` / `M32` / `M34` — additional pairs; more is better.
- **`PMKID(s) written`** — non-zero → mode-22000 type=01 lines are
  in the output.
- **`ESSID:`** — must match the target SSID. Wrong ESSID = wrong
  salt = crack finds nothing even with the right passphrase.

If the block above is empty or missing pieces, the crack will run
against nothing — recapture first, or read on for whether a partial
is workable.

## Convert only after the check passes

```python
convert_to_hashcat(pcap_path="/tmp/hs.pcapng",
                   out_path="/tmp/hs.22000")
```

Verify the output is non-empty and each line starts with `WPA*`:

```
head -1 /tmp/hs.22000
# WPA*02*<32-hex>*<12-hex>*<12-hex>*<hex-essid>*<64-hex-anonce>*<eapol-hex>*<hex>
```

Line format reference:

```
WPA*<type>*<PMKID/MIC>*<AP_MAC>*<STA_MAC>*<ESSID_hex>*<ANonce>*<EAPOL_frame>*<MC>
```

- **type `01`** — PMKID (M1 only); the fastpath.
- **type `02`** — EAPOL 4-way (at least M2 present).

## What "handshake looks incomplete" actually means

The 4-way handshake is four frames: M1 (AP→STA, ANonce), M2 (STA→AP,
SNonce + MIC), M3 (AP→STA, GTK + MIC), M4 (STA→AP, ACK). For hashcat
you need:

- **PMKID mode (type=01):** just M1 with the RSN IE PMKID field
  populated. Some APs strip it; some emit it always; some only on the
  first association. Modern hcxdumptool triggers M1 emission by
  associating.
- **4-way mode (type=02):** at minimum M1 + M2. The MIC on M2 is what
  hashcat verifies against candidate PSKs.

M3+M4 give you additional verification but aren't required. If your
capture has M1+M3 but no M2, you can't crack — the client's SNonce
never made it through.

## Common capture failures and their tells

| symptom in `hcxpcapngtool --info`      | cause                                     | fix                                      |
| -------------------------------------- | ----------------------------------------- | ---------------------------------------- |
| 0 EAPOL, 0 PMKID                       | Recon ran, no attack fired                | Fire the deauth; check `call_log`        |
| EAPOL present, 0 M12/M14/M32/M34       | M1 only, no client response               | Client isn't associating; retry with fresh deauth |
| M12 present but crack yields nothing   | Wrong ESSID salt                          | Verify SSID in `--info`; if AP was hidden, target the reveal step first |
| Multiple ESSIDs in one file            | You captured across a rescan              | Split by BSSID with `hcxpcapngtool -o` filters |
| M12 present, MIC field looks wrong     | Corruption, wrong channel mid-capture     | Recapture; verify channel didn't hop     |
| PMKID present but crack fails          | AP emits a fake / zeroed PMKID            | Some APs do this by design; fall back to 4-way |

## Recapture vs. crack-anyway — the decision

- **PMKID present, ESSID correct** → convert and crack. Even a partial
  4-way is superfluous for the type=01 line.
- **M1+M2 present, ESSID correct, one clean pair** → crack. Ignore
  the noise.
- **Multiple M12 pairs from different clients, same ESSID** → crack;
  hashcat will find the passphrase against whichever pair is valid.
- **M1 only, no M2 anywhere** → recapture. The client's response
  didn't land.
- **ESSID hex looks weird (control chars, empty)** → the AP was
  hidden or the capture caught a fake beacon. Fix upstream.

## Why crack_start finishes in seconds against a valid PSK

- **Wordlist not the size you think.** `wc -l rockyou.txt` — if it's
  50 lines, you're pointed at a file with the same name in the wrong
  dir. Set `WORDLIST_DIR` or use an absolute path.
- **Hash file is empty.** `wc -l /tmp/hs.22000` == 0 → convert failed
  silently. Re-check `hcxpcapngtool --info`.
- **`--brain-client` remembered a prior null run.** Delete the brain
  cache or use `--brain-host 127.0.0.1 --brain-port 6863
  --brain-session=fresh`.
- **`--session` restore is picking up stale state.** Check
  `~/.local/share/hashcat/sessions/`.

## Why crack_start runs forever against a valid PSK

- **Passphrase not in the wordlist and no rules match.** Escalate:
  `-r best64` → `-r OneRuleToRuleThemAll` → structured masks →
  SSID-derived (`cewl venue.example`).
- **Wrong mode.** Confirm mode=22000. Mode 2500 is legacy; mode 22001
  wants a known PMK, not a passphrase.
- **Wrong hash line.** Verify with a `hashcat --show` after loading
  the file — should print the format hashcat parsed.

## The one hashcat option every operator misses

```
--outfile-format=2 --outfile=/tmp/hs.cracked
```

Writes only the passphrase (no hash prefix). When the crack lands,
this is the flag — copy it to the scoreboard directly.

## Preserving the capture for the writeup

```
mv /tmp/hs.pcapng /mnt/sd/captures/hs-<bssid>-<utc>.pcapng
```

Big captures should go to SD before reboot (Pineapple `/tmp` is
RAM). See [`knowledge/pineapple-mk7/walkthrough.md § Path H`](../knowledge/pineapple-mk7/walkthrough.md).

## Deeper corpus

- **4-way handshake byte-by-byte** — [`knowledge/4-way-handshake/`](../knowledge/4-way-handshake/).
- **PMKID** — [`knowledge/pmkid/`](../knowledge/pmkid/).
- **hcx tools** — [`knowledge/hcx-tools/`](../knowledge/hcx-tools/).
- **Cracking tradecraft** — [`knowledge/cracking-tradecraft/`](../knowledge/cracking-tradecraft/).
- **Hashcat mode 22000** — `lookup_hashcat_mode(22000)`.
