# Dragonblood deep — walkthrough

Three concrete plays against a WPA3-SAE deployment: transition-mode
downgrade, MODP-group downgrade, and hunt-loop-timing-oracle attack.
The transition-mode play is the practical one; the two side channels
are correctness references for hardened targets.

## Preconditions

- Target AP is WPA3-SAE (RSN AKM 8) or WPA3-transition (both AKM 2
  and AKM 8 present in the RSN IE).
- At least one WPA2-capable client on the target network (for the
  transition-mode play).
- Monitor+injection interface (`wlan1mon` on the Pineapple).

## Path A — Transition-mode downgrade

This is the fast lane. If the RSN IE lists AKM 2 alongside AKM 8, you
skip Dragonblood entirely.

```
# 1. Stand up a rogue on the target SSID+BSSID advertising WPA2-only
#    (no AKM 8). WPA2-capable clients fail over to you.
cat > /tmp/wpa2rogue.conf <<EOF
interface=wlan1
ssid=<TargetSSID>
hw_mode=g
channel=6
wpa=2
wpa_key_mgmt=WPA-PSK
rsn_pairwise=CCMP
wpa_passphrase=<placeholder — client will 4-way with you>
EOF
hostapd /tmp/wpa2rogue.conf

# 2. Capture the 4-way M2 / M3 the client sends. hostapd logs the
#    EAPOL; alternatively run airodump alongside.
# 3. Convert to hashcat 22000 and crack. The SAE and WPA2 passwords
#    are identical in transition-mode deployments, so the WPA2 PSK
#    IS the WPA3 password.
```

See `attacks.json:wpa3-transition-downgrade` for the record.

## Path B — MODP-group downgrade

Applies when the AP still advertises legacy MODP groups (19..21 are
elliptic-curve, 22..24 are MODP). If the AP is willing to negotiate a
weak MODP group, the hunt-and-peck timing oracle is trivially
observable.

```
# hostapd on the attacker side, only offering group 22:
sae_groups=22
```

Force the client to renegotiate (deauth if not PMF, or wait for a
natural reassoc), and observe SAE Commit frame timing for the
password-element derivation loop.

## Path C — Cache / timing side channel

The published Dragonblood side channels require either co-location
with the SAE implementation (cache attacks) or fine-grained timing
against a remote target. For a WCTF this is usually not the fastest
path — but recognize the fingerprint:

- Long, variable-latency Commit response times = still using hunt-and-peck.
- Constant-time Commit response = H2E (AKM 18) or SAE-PT — timing
  oracle is gone; move on.

Tools published with the paper: `dragondrain` (co-location cache
probe), `dragontime` (timing collection).

## Recognition — is this target vulnerable?

- **AKM 8 alone** → check for H2E support (an AKM 18 offer). Absent
  H2E, the timing oracle is on the table.
- **AKM 18 present** → SAE-PT / H2E — hunt loop is gone. Attack the
  transition-mode side (AKM 2) if it exists.
- **AKM 8 + AKM 18** → mixed; the client may pick either. Weak
  clients pick 8 and remain oracle-exposed.
- **AKM 8 + AKM 2** → transition mode. Downgrade path is open.
- **AKM 8 only + AKM 18 + PMF-required** → hardened. Move on.

## Failure modes

- **Client refuses WPA2 side.** Some 2024+ enterprise supplicants
  reject transition-mode APs entirely. If the client only speaks
  SAE, transition downgrade doesn't apply.
- **H2E in place, no MODP.** Both side-channel paths close. Attack
  surface reduces to weak-passphrase brute after a legitimate
  handshake — which SAE resists by design.
- **PMF-required.** You can't push the client off the real AP; wait
  for a natural reassoc.

## Cite

- Vanhoef & Ronen 2019 — Dragonblood, IEEE S&P 2020.
- Wi-Fi Alliance WPA3 Specification (H2E / SAE-PT).
- IEEE Std 802.11-2020, §12.4.
- attacks.json: `dragonblood-sidechannel`, `dragonblood-timing`,
  `dragonblood-modp-downgrade`, `sae-h2e-followup-side-channel`,
  `wpa3-transition-downgrade`.
