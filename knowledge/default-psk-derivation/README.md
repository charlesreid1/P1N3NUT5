# default-psk-derivation

The "no packets sent" attack. Some vendors ship default PSKs that are
deterministically derived from BSSID, SSID suffix, or serial number.
If you can identify the vendor from the beacon, you already have the
PSK — or a small candidate list to trial against a captured PMKID /
handshake.

**Still relevant in 2026** despite being a 2010s discovery. Vendor
default PSKs still ship on new consumer gear in EU/UK markets (UPC/UBEE
mesh, Sky Broadband, BT SmartHub generations), and any old consumer
router still deployed after a factory reset is a target.

Records: `default_psks.json` (`dpsk-*` ids). Attacks:
`attacks.json` (`default-psk-*` ids).
