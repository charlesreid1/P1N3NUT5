# iwd — walkthrough

**Verified against:** iwd 2.20 as of 2026-Q3

The systemd-native wireless daemon. Different behavior under attack
conditions from wpa_supplicant — matters when the target is a
modern Fedora / Arch / IoT client.

## Preconditions

- iwd installed (`apt install iwd` on Debian, default on many
  modern distros).
- User in the `netdev` group (or root).
- NetworkManager disabled if it was managing the same iface.

## Path A — Join a WPA2-PSK network as a legitimate STA

For post-crack validation of a recovered PSK on a Fedora/Arch host:

```
# /var/lib/iwd/<SSID>.psk
cat > /var/lib/iwd/CorpWiFi.psk <<EOF
[Security]
Passphrase=<recovered passphrase>
EOF

# Connect via iwctl:
iwctl station wlan0 connect CorpWiFi

# Confirm state:
iwctl station wlan0 show
# State: connected
```

## Path B — Join WPA3-SAE

```
cat > /var/lib/iwd/WPA3Net.psk <<EOF
[Security]
Passphrase=<passphrase>
EOF

iwctl station wlan0 connect WPA3Net
```

Same file format; iwd auto-detects SAE if the AP advertises AKM 8.

## Path C — Join WPA2-Enterprise (EAP-PEAP-MSCHAPv2)

```
cat > /var/lib/iwd/CorporateEAP.8021x <<EOF
[Security]
EAP-Method=PEAP
EAP-Identity=alice@corp.local
EAP-PEAP-Phase2-Method=MSCHAPV2
EAP-PEAP-Phase2-Identity=alice
EAP-PEAP-Phase2-Password=<password>
EAP-PEAP-CACert=/etc/ssl/certs/corp-ca.crt
EAP-ServerDomainMask=*.corp.local
EOF

iwctl station wlan0 connect CorporateEAP
```

`EAP-ServerDomainMask` is what stops trust-and-continue prompts on
iwd. If the CN doesn't match, iwd refuses — good client hygiene,
harder to attack.

**Key renames (iwd 2.0, 2022):** older writeups reference the
pre-2.0 spellings. Modern iwd expects the new names but accepts the
legacy ones as aliases:

| pre-2.0 (deprecated alias)         | 2.0+ (canonical)             |
| ---------------------------------- | ---------------------------- |
| `EAP-Phase2-Identity`              | `EAP-PEAP-Phase2-Identity`   |
| `EAP-PEAP-ServerDomainMask`        | `EAP-ServerDomainMask`       |

Prefer the canonical form in new profiles; leave the alias only in
snippets you're preserving verbatim for an old-iwd audience.

## Path D — Recognize an iwd client under attack

iwd's supplicant behavior differs from wpa_supplicant in ways that
matter:

- **Strict frame ordering.** Malformed M2 that wpa_supplicant
  tolerates, iwd drops.
- **PMF handling.** iwd defaults to *optional*; wpa_supplicant
  defaults vary. On a target using iwd, PMF status is negotiated
  fresh per session.
- **Kr00k trigger.** iwd sometimes ignores disassoc timing that
  wpa_supplicant honors. Kr00k tail-frame capture may need a slower
  trigger cadence.
- **Association Request IE order** differs slightly. See
  `client_fingerprints.json` for the iwd fingerprint.

If your target OS is Fedora ≥ 33, Arch, or a systemd-based IoT
distro, assume iwd unless probed otherwise.

## Path E — Drive iwd from a script

```
# Non-interactive form.
iwctl --passphrase '<passphrase>' station wlan0 connect CorpWiFi

# Or:
dbus-send --system --print-reply \
  --dest=net.connman.iwd \
  /net/connman/iwd/0/0/wlan0 \
  net.connman.iwd.Station.Connect \
  string:"CorpWiFi"
```

## Path F — Verify + hand-off

After association:

```
iwctl station wlan0 show
# Signal, cipher, EAP details.

# DHCP:
dhclient wlan0
ip addr show wlan0
```

Once the address lands, the "post-crack" milestone is met. Stop
here for WCTF; anything past is a LAN pentest handoff (see
`post-crack-rf/`).

## Failure modes

- **`iwctl` says "Unable to find network".** iwd's scan didn't
  catch the SSID this window. `iwctl station wlan0 scan` then retry.
- **Association fails with "not authorized".** PSK wrong or PMF
  requirement mismatch. Verify against a Wireshark decrypt (see
  `post-crack-rf/walkthrough.md`).
- **iwd refuses to associate.** Cert validation strict — this is
  iwd doing the right thing. Provide the right CA in
  `/etc/ssl/certs/`.
- **NetworkManager fights iwd.** Set `NetworkManager.conf`
  `[device]/wifi.backend=iwd` or disable NetworkManager entirely
  on the interface.

## Cite

- iwd upstream — git.kernel.org/pub/scm/network/wireless/iwd.
- freedesktop D-Bus API for iwd.
- `client_fingerprints.json` — iwd probe-request signature.
