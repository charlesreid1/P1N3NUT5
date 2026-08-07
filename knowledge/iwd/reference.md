# iwd — the systemd-native wireless supplicant

Increasingly the client-side default on modern Linux (Fedora 40+,
Arch defaults, many IoT distros). Where wpa_supplicant is a monolith
with a legacy config-file surface, iwd is a small daemon speaking
D-Bus.

## Why the difference matters to attackers

- **State machine.** iwd is stricter about frame ordering. Malformed
  M2 responses that wpa_supplicant tolerates, iwd drops. Kr00k-style
  disassoc timing that wpa_supplicant accepts, iwd sometimes ignores.
- **Retry behavior on 4-way failure.** Different backoff.
- **PMF handling.** iwd defaults to PMF-optional; wpa_supplicant
  defaults vary by build. When targeting Fedora / Arch clients,
  assume iwd unless probed otherwise.

## Recognition from a pcap

- **Association Request IE order.** iwd emits the RSN IE in a slightly
  different position than wpa_supplicant. Not a strong signal by
  itself but combines with vendor MAC OUI.
- **Absence of a hostname in DHCP requests** for the first few
  seconds — iwd delays announcing the hostname; wpa_supplicant does
  not.

## Driving iwd on the Pineapple

The Pineapple runs OpenWRT — wpa_supplicant is the stock supplicant.
When we drive `iwctl station wlan0 connect …` from a Pineapple-side
script, we are talking to iwd on a separate rig (not the Pineapple).

## Cite

- iwd freedesktop.org project.
- attacks.json: `krack-linux-all-zero-ptk` (the wpa_supplicant ≤2.6
  bug does not apply to iwd, which has never had this class of PTK
  reinstall bug).
