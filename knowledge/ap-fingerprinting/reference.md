# AP fingerprinting — the first 60 seconds

Same discipline as client fingerprinting, but for APs. The goal is
usually one of:
- Identify vendor to pick the right attack (WPS vendor PIN, default
  PSK, known chipset CVE).
- Spot the odd one out among a set of same-SSID APs (evil-twin farm).
- Cross-reference against the Wi-Fi Alliance certification database
  to confirm firmware family.

## Signals

- **Beacon Vendor-Specific IEs.** Every real AP emits at least one
  Vendor-Specific IE with a manufacturer OUI. See `ies.json:ie-vendor-
  specific` for notable OUIs.
- **WPS IE.** Even when WPS is "disabled" many APs still emit the
  WPS IE with Manufacturer / Model Name / Model Number filled in.
  Cross-reference against `attacks.json:wps-vendor-pin-derivation`
  for the derivation-tool table.
- **Beacon interval + DTIM period.** Consumer routers default to
  100 TU / DTIM 2 or 3. Enterprise gear varies. Odd values (e.g.
  50 TU) are a strong "not the real AP" signal in an evil-twin
  farm.
- **Rate set.** Real APs advertise every rate 1..54 Mbps. hostapd
  rogues sometimes omit low rates.
- **RSN IE field order + capabilities bit ordering.** Per-driver
  quirks — mac80211 hostapd vs. ath9k firmware AP vs. Broadcom
  firmware AP all have subtle differences.
- **Country IE regulatory triplets.** A real AP in the US has the
  FCC triplets; a rogue built on a laptop often uses the driver's
  factory default (usually US or "world").

## Cross-references

- **beacon_diff** — the MCP tool that highlights IE differences
  between two BSSIDs. Perfect for evil-twin-farm triage.
- **Wi-Fi Alliance certification database** — verify vendor + product
  + firmware. Reachable at wi-fi.org.

## Records

Every AP-fingerprint signal is backed by an IE record in
`records/ies.json`. Cross-linked from every attack that depends on
the fingerprint.

## Cite

- IEEE Std 802.11-2020, §9.4.
- Wi-Fi Alliance certification database.
- knowledge/ies/reference.md — future write; the record set is in
  records/ies.json today.
