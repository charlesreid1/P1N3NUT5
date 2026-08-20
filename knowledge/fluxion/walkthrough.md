# fluxion — walkthrough

**Verified against:** fluxion `master` (FluxionNetwork/fluxion) as of 2026-Q3

Install once, run the chain, exit clean. Fluxion is menu-driven —
this walkthrough covers what to select at each step.

## Preconditions

- Kali or a similar distro with monitor+injection-capable adapter.
- Root privileges.
- Target AP identified: SSID, BSSID, channel.

## Setup

```
git clone https://github.com/FluxionNetwork/fluxion.git
cd fluxion
sudo ./fluxion.sh       # first launch prompts for missing deps
                        # (hostapd, dnsmasq, mdk4, php, aircrack-ng)
```

The current upstream doesn't expose a bare `-i` install flag; the
main script installs missing dependencies on first run.

## The engagement

```
sudo ./fluxion.sh
# menu-driven from here.
```

Selection sequence:

1. **Language** → English.
2. **Attack type** → `Captive Portal`.
3. **Channel to scan** → `all channels` (or the target's if known).
4. **Interface** → the monitor-capable adapter (e.g. `wlan1`).
5. Wait for the scan; Ctrl-C when the target appears in the list.
6. **Target** → pick from the enumerated APs.
7. **Interface for AP creation** → same or second adapter.
8. **Interface for jamming** → any (a third radio helps but Fluxion
   can share).
9. **Handshake capture method** → `aireplay-ng` (fast) or
   `mdk4` (louder, sometimes more effective).
10. **Verify handshake** → Fluxion pauses until it sees a full 4-way.
11. **Web interface language + template** → pick the target's vendor
    (e.g. "Xfinity", "T-Mobile", "generic Wi-Fi Sign-in").
12. **Cert type** → self-signed (Fluxion generates one).
13. Fluxion kicks off:
    - Rogue AP on the target SSID (open).
    - dnsmasq intercepts DNS.
    - PHP-based portal serves the login page.
    - Deauth flood pushes clients off the real AP.

When a user submits a passphrase, Fluxion validates it against the
captured handshake and:

- If wrong → refuses, keeps the portal open.
- If right → prints the PSK, shuts down the rogue, and exits.

## Where the flag lands

Handshakes captured by the "Handshake Snooper" sub-attack live under
`attacks/Handshake Snooper/handshakes/<ESSID>-<BSSID>.cap` inside the
cloned fluxion tree. The Captive Portal attack consumes that
handshake and, on a valid submission, prints the PSK to the terminal
and records it under `attacks/Captive Portal/` in the same tree.

## Failure modes

- **No handshake captured.** Client didn't reassoc during the deauth
  window. Try `mdk4 d` mode (louder), or `airodump-ng` in a separate
  shell to visualize what's happening.
- **Portal doesn't load in client's browser.** dnsmasq isn't
  intercepting. Check `iptables -L` for stray rules.
- **User dismisses the portal.** Vendor branding didn't match.
  Match the target SSID's expected sign-in page — Xfinity users are
  calibrated to Xfinity portal design.
- **PMF-required target.** Deauth doesn't push clients. Fluxion
  falls back to waiting for natural reassocs; slow.
- **Fluxion crashes at "verify handshake".** Missing `hcxpcapngtool`
  in path, or old aircrack-ng that doesn't understand pcapng. Update.

## When to give up on Fluxion

- **Target is WPA3-only.** No 4-way to capture; the whole flow
  breaks. Move to `wpa3/walkthrough.md`.
- **You have a Pineapple.** Native chain in
  `captive-portal/walkthrough.md` is more flexible and quieter.

## Cite

- FluxionNetwork/fluxion — README + attack script sources.
- aircrack-ng — handshake validation.
- attacks.json: `evil-twin-clone`, `captive-portal-cred-capture`.
