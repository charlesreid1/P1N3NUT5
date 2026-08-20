# DoS — recognition

Two perspectives. If you're firing DoS, you want to know which paths
work against which target. If you're analyzing a pcap that IS the
puzzle, you want to identify the mode from the frame pattern.

## Which DoS works against which target

| target property                | works                     | broken               |
| ------------------------------ | ------------------------- | -------------------- |
| PMF-disabled                   | all deauth/disassoc       | (nothing)            |
| PMF-optional, non-PMF client   | targeted deauth/disassoc  | broadcast deauth     |
| PMF-required, all-PMF clients  | (deauth blocked)          | broadcast + targeted deauth |
| TKIP-active                    | Michael MIC DoS           | (n/a on CCMP-only)   |
| WPA2/3 CCMP-only               | (Michael MIC N/A)         | Michael MIC          |
| 802.1X authenticator           | EAPOL-Start flood         |                      |
| any AP with an association table | Assoc flood, Auth flood |                      |

## Identifying a DoS mode from a pcap

Frame pattern → mdk4 mode / primitive:

### Deauth flood (`d`)

- `wlan.fc.type_subtype == 0x0c`
- High rate (100s/sec) from one source MAC
- Reason code varies by tool version — legacy `aireplay-ng` (≤ 1.6)
  defaulted to 7 (Class 3 frame from nonassociated STA); modern
  aircrack-ng 1.7+ defaults to 1 (unspecified). `mdk4 d` defaults to
  1. A constant-7 storm is a legacy-aireplay fingerprint, not a
  general "deauth attack" fingerprint.
- Destination = broadcast or one specific STA

### Auth flood (`a`)

- `wlan.fc.type_subtype == 0x0b` (Authentication frame)
- Rapidly-changing source MACs
- All targeting the same destination BSSID
- Auth algorithm = Open (0), sequence = 1

### Beacon flood (`b`)

- `wlan.fc.type_subtype == 0x08`
- Many distinct BSSIDs (usually random)
- Many distinct SSIDs (from a wordlist)
- Same channel

### RTS/CTS NAV (scapy — no mdk4 mode)

mdk4 has no `v` mode; NAV-reservation floods are scapy-driven
(CTS-to-self with a large Duration field). Pcap fingerprint:

- `wlan.fc.type_subtype == 0x1b` (RTS) or `0x1c` (CTS)
- Duration/ID field near 0x7FFF (32767 μs) — maxed NAV
- No corresponding legitimate frame exchange (CTS with no matching
  RTS, or RTS with no matching CTS/data)
- RA = self on CTS-to-self ("cts-to-self silencing")

### Michael MIC DoS (`m`)

- MIC failure report frames
- TKIP-only network (RSN IE Pairwise Cipher = 00-0F-AC:02)
- Two failures within 60 s

### EAPOL-Start flood (`e`)

- `eapol.type == 1` (EAPOL-Start)
- High rate
- From spoofed source MACs (all different)

### Association flood

- `wlan.fc.type_subtype == 0x00` (Association Request)
- Rapidly-changing source MACs
- All targeting same BSSID
- Not preceded by legitimate 4-way

## Distinguishing a DoS from a legitimate load

Genuine WiFi traffic has:

- **Bidirectional** frame exchanges (request + response).
- **Consistent source MACs** for each STA session.
- **Timing distribution** matching human behavior (bursts + gaps).

A DoS pattern has:

- **Unidirectional** frames (attacker → victim, no response).
- **Rapidly-changing source MACs** (obviously spoofed).
- **Uniform timing** (mdk4 rate is ~1000/sec, unlike any real load).

## Flag-signal DoS puzzles

Some WCTF puzzles specifically look for a DoS pattern as the flag.
See `ctf/deauth-forensics.md` for the analysis playbook. The flag
often encodes into:

- Reason codes across a burst of deauths.
- Source MAC bytes across a run of frames.
- Inter-frame timing (Morse-encoded).
- The specific frame type / subtype combination.

## What a WIDS sees

Every mdk4 mode has a canonical signature. Modern WIDS (Kismet,
Aruba AirWave, Cisco WIPS) flag them within seconds:

- **Deauth flood** → per-BSSID alert with rate > N/sec.
- **Auth flood** → per-BSSID alert with unique-MAC count > N/window.
- **Beacon flood** → too many distinct BSSIDs on one channel.
- **Michael MIC** → MIC-failure alert.

Operate accordingly — pick the noisiest mode for a WCTF flag-signal
puzzle, the quietest for a legitimate follow-on (targeted deauth
for a specific-client 4-way capture).

## Cite

- aircrack-ng documentation — mdk4 mode catalog.
- IEEE Std 802.11-2020, §9.4 (management), §10.3 (NAV), §11.2
  (power management), §9.3.2.6 (Michael MIC).
- Kismet WIDS documentation.
- attacks.json: same records as walkthrough.
