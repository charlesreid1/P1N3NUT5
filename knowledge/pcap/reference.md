# pcap / pcapng — how we read a capture

Two container formats. Both hold 802.11 frames prefixed by a radiotap
header that carries channel / rate / RSSI metadata.

## Classic pcap vs pcapng

- **Classic pcap** — simple. Magic `0xa1b2c3d4` (big-endian) or
  `0xd4c3b2a1` (little-endian) + 20-byte header + repeated
  {timestamp, len, payload} records. All the fixture pcaps under
  `tests/fixtures/pcaps/` are classic pcap.
- **pcapng** — block-oriented. Magic starts with `0x0a0d0d0a`. Richer
  metadata (interface descriptions, per-block options, comments).
  What `tcpdump -w` emits on most modern systems. What hcxdumptool
  emits.

`detect.parse_pcap()` in the MCP is a byte-level classic-pcap parser —
enough for a frame-type histogram + BSSID/SSID/client extraction. Full
pcapng needs scapy (via the `[pcap]` extra) or a shell to `tshark`.

## Radiotap header

Every captured 802.11 frame in a pcap starts with a radiotap header:

```
struct radiotap_header {
  u8  version;         # always 0
  u8  padding;
  u16 length;          # total radiotap length (little-endian!)
  u32 present_flags;   # bitmap of which optional fields follow
  ...                  # optional fields per present_flags
};
```

Skip `length` bytes to get to the 802.11 header. In the fixtures we
ship, the pcap link type is `LINKTYPE_IEEE802_11 (105)` — no radiotap
prefix. Real captures usually use `LINKTYPE_IEEE802_11_RADIOTAP (127)`.

**Three 802.11 pcap link types to know about:**

| DLT_ | libpcap number | Description                                        |
| ---  | ---            | ---                                                |
| 105  | IEEE802_11     | Bare 802.11 header — no radio metadata             |
| 127  | IEEE802_11_RADIOTAP | 802.11 + radiotap prefix (the modern default)  |
| 192  | PPI            | Per-Packet Information — CACE Technologies legacy  |

- **105** — no channel/RSSI. You cannot use `radiotap.*` display
  filters. Best to `mergecap -F pcapng` and add radiotap via a fresh
  capture; the metadata cannot be reconstructed after the fact.
- **127** — the standard. Every modern tool (hcxdumptool, airodump-ng,
  scapy, `tcpdump -y IEEE802_11_RADIO`) emits it.
- **192 / PPI** — older AirPcap Windows captures. Read with tshark
  (`tshark` handles PPI transparently); the fields become `ppi.*`
  rather than `radiotap.*`.

**Radiotap extended presence flags.** The `present_flags` is a 32-bit
bitmap. Bit 31 (`0x80000000`) is the **Extended Presence** bit —
when set, another 4-byte presence word follows. Multiple extensions
can chain until a `present_flags` word has bit 31 clear. Skipping
the wrong number of bytes when bit 31 is set is a common
parser-of-my-own bug; use scapy's `RadioTap` layer.

## tshark one-liners you will actually use

```
# AP enumeration
tshark -r cap.pcap -Y "wlan.fc.type_subtype == 8" \
       -T fields -e wlan.bssid -e wlan.ssid | sort -u

# Handshake completeness — how many M1/M2/M3/M4 per BSSID
tshark -r cap.pcap -Y "eapol" \
       -T fields -e wlan.bssid -e wlan.sa -e wlan.da -e eapol.type

# Probe-request profiling — every SSID any client asked about
tshark -r cap.pcap -Y "wlan.fc.type_subtype == 4" \
       -T fields -e wlan.sa -e wlan.ssid | sort -u

# Decrypt with a recovered PSK, per-STA PTK
tshark -r cap.pcap \
       -o "wlan.enable_decryption:TRUE" \
       -o "uat:80211_keys:\"wpa-pwd\",\"MyPassphrase:MyESSID\"" \
       -Y "http"
```

## The perception tools in the MCP

- `parse_pcap(path)` — frame counts + BSSID/SSID/client sets.
- `extract_handshakes(pcap, out)` — hcxpcapngtool WPA*02 output.
- `extract_pmkids(pcap, out)` — hcxpcapngtool WPA*01 output.
- `convert_to_hashcat(pcap, mode=22000, out)` — the combined output.

## Cite

- radiotap.org — radiotap header spec.
- pcapng draft — IETF specification for pcap-ng.
- hcxtools GitHub.
