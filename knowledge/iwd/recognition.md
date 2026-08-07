# iwd recognition

Distinguishing an iwd-driven client from a wpa_supplicant client
based on observed on-air and DHCP behavior. iwd is common enough on
Fedora, Arch, some embedded / IoT distros, and increasingly on
consumer Linux desktops that a WCTF assumption of "Linux client =
wpa_supplicant" is wrong more often than it used to be.

## Association Request — IE ordering

Both supplicants emit an RSN IE and a SupportedRates IE, but the
order and the exact bit layout differ. Rough signature:

- **wpa_supplicant** emits: Supported Rates → Extended Rates → RSN
  (with Group Cipher, Pairwise Cipher, AKM as the wpa_supplicant
  config specifies) → Vendor-Specific (WPA/WMM).
- **iwd** emits: Supported Rates → Extended Rates → RSN with a
  slightly tighter capabilities bit pattern (defaults to
  PMF-optional, MFPC=1 MFPR=0) → HT/VHT/HE Capabilities if the
  driver supports them → no proprietary Vendor-Specific WMM padding
  (iwd relies on driver-supplied WMM handling).

Not decisive by itself, but combined with other signals below,
narrows the identification.

## MFP negotiation posture

- **iwd defaults to PMF-optional** (MFPC=1, MFPR=0) unless configured
  otherwise. It happily associates with PMF-disabled APs but will
  negotiate PMF when the AP offers it.
- **wpa_supplicant defaults vary by build.** Ubuntu ships with
  PMF-optional; Fedora historically shipped PMF-required in newer
  releases; NetworkManager's config layer overrides both.

Behavioral tell: if a client refuses to associate with an AP whose
RSN Capabilities bit 6/7 = 0/0 (no PMF), it's a PMF-required
wpa_supplicant. iwd will always associate in that scenario.

## Response to malformed 4-way messages

iwd's state machine is stricter:

- **Malformed M2 responses** (bad MIC, out-of-order EAPOL-Key
  descriptor version): iwd drops silently and re-initiates from M1.
- **wpa_supplicant** ≤2.9 sometimes tolerated malformed M2 in
  specific driver contexts. Post-2.10 tightened.
- **Reinstall attempts (KRACK-style)**: iwd never had the CVE-
  2017-13077 all-zero-PTK bug that wpa_supplicant 2.4–2.6 shipped.
  A capture where the client's post-M3-replay data frames decrypt
  under the previous PTK (not zero) suggests iwd or a patched
  wpa_supplicant.

## DHCP behavior — the hostname-delay tell

iwd runs its own tiny DHCP client (systemd-networkd or its own
built-in). Observable pattern:

- iwd DHCPDISCOVER: typically **no Option 12 (Host Name)** in the
  first request; hostname arrives later or is announced separately
  via systemd-hostnamed.
- wpa_supplicant + dhclient / dhcpcd: DHCPDISCOVER **usually
  includes Option 12** from the first packet, with the OS's
  configured hostname.

Filter in tshark:

```
tshark -r cap.pcapng -Y 'bootp && bootp.option.type == 12' \
  -T fields -e eth.src -e bootp.option.hostname
```

Absence of Option 12 on the first DHCPDISCOVER from a Linux MAC is
a weak-but-real iwd signal.

## Probe request behavior

- iwd prefers passive scanning by default. When it does probe, its
  probe requests carry a minimal IE set (SSID, Supported Rates,
  Extended Rates, HT Capabilities) — no Vendor-Specific WMM or
  Microsoft-flavored IEs.
- wpa_supplicant probes typically include more IEs, especially with
  NetworkManager driving.

Sparse probe request IE set from a Linux MAC → iwd is likely.

## MAC randomization

- iwd supports per-network MAC randomization via
  `[General] AddressRandomization=network`. Default is "off" on
  older versions; newer versions default to per-network.
- wpa_supplicant via NetworkManager supports the same feature but
  the config path is different, and default varies by distro.

If a Linux client is randomizing per-network in a way that produces
predictable per-SSID stable pseudo-MACs, that's consistent with
iwd's implementation.

## The full recognition heuristic

Assemble the signals:

| signal | weight |
| ------ | ------ |
| Linux vendor OUI (or randomized MAC with Linux-ish IE fingerprint) | prerequisite |
| Sparse probe request IE set | strong iwd |
| DHCPDISCOVER missing Option 12 initially | strong iwd |
| PMF-optional posture (MFPC=1, MFPR=0) in Assoc Req | weak iwd |
| No KRACK-vulnerable behavior on tested reinstall | weak iwd |
| Absence of proprietary WMM/WPA1 Vendor-IEs in Assoc Req | moderate iwd |

Three-out-of-six → likely iwd. Two-out-of-six → ambiguous.

## Why we care

The attack picks change:

- **Kr00k**: iwd-side behavior on disassoc is the driver's, not
  iwd's, so Kr00k against iwd clients still works when the underlying
  chipset is vulnerable. But iwd's cleaner disassoc handshake means
  fewer stray frames post-disassoc than wpa_supplicant.
- **KRACK**: iwd was never in the CVE-2017-13077 blast radius. Don't
  bother running KRACK PoCs against iwd clients.
- **Weak-cert enterprise phish**: iwd's TLS validation was
  historically stricter than wpa_supplicant's — check the iwd
  version before assuming a cert-phish will work.

## Cite

- iwd project (freedesktop.org).
- knowledge/iwd/reference.md.
- attacks.json: `krack-linux-all-zero-ptk` (does not apply to iwd),
  `kr00k-broadcom-cve-2019-15126` (still applies at the chipset
  layer regardless of supplicant).
