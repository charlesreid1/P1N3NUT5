# Glossary

Just the alphabet-soup. Every entry links to a deeper doc where one
exists.

- **AKM** — Authentication and Key Management. Suite in the RSN IE.
  Per IEEE 802.11-2020 Table 9-151, the wire selector's trailing byte
  is the AKM number *in hex*: AKM 2 = PSK (0x02); AKM 8 = SAE (0x08);
  AKM 12 = 802.1X Suite-B 192 (0x0C); AKM 18 = OWE (0x12); AKM 24 =
  SAE-EXT-KEY (0x18). H2E is signaled via RSNXE (IE 244) bit 5, NOT
  by any distinct AKM number. See `wpa2/reference.md`,
  [[akm-selector-glossary]].
- **AKM-selector encoding** — the byte `00-0F-AC:XX` is a decimal
  AKM number **written in hex**. 0x12 = 18 (OWE); 0x18 = 24
  (SAE-EXT-KEY). The most common corpus-wide error is to read the
  hex byte as a decimal ("AKM 18 = SAE-EXT-KEY"). Confirm against
  `records/security_suites.json`.
- **ANonce** — AP-side nonce in the 4-way handshake (M1, M3).
- **ANQP** — Access Network Query Protocol (802.11u). Pre-association
  recon. See `hotspot2/`.
- **BSSID** — Basic Service Set ID; the AP's MAC address in beacons.
- **BTM** — BSS Transition Management (802.11v). See `fast-transition/`.
- **CCMP** — Counter Mode with CBC-MAC Protocol. AES-based cipher for
  WPA2/WPA3 pairwise data. Cipher selector 00-0F-AC:04. See
  `wpa2/reference.md`.
- **DFS** — Dynamic Frequency Selection. Required on many 5 GHz
  channels; radar-avoidance.
- **DS Parameter Set** — IE 3, single-byte current channel number.
- **EAP** — Extensible Authentication Protocol. See `records/eap_methods.json`.
- **EAPOL-Key** — the 4-way handshake carrier. EtherType 0x888E.
- **FT** — Fast Transition (802.11r). See `fast-transition/`.
- **GAS** — Generic Advertisement Service. The transport for ANQP.
- **GCMP** — Galois/Counter Mode Protocol. AES-GCM based; used in WPA3
  and Wi-Fi 6/6E where GCMP-256 is optional. Cipher selectors
  00-0F-AC:08 / 09.
- **GTK** — Group Temporal Key. Broadcast/multicast data key. Delivered
  in M3.
- **H2E** — Hash-to-Element (Simplified SWU / SSWU). Dragonblood
  mitigation for SAE PWE derivation — constant-time password-to-curve
  mapping. Signaled by the **RSNXE (IE 244) H2E-only capability
  bit**, NOT by any AKM number. See `dragonblood-deep/`.
- **hcxdumptool** — the modern PMKID + 4-way capture tool. See
  `hcx-tools/`.
- **IE** — Information Element. Every non-fixed part of a beacon /
  probe / assoc frame. Element ID + Length + payload. See
  `records/ies.json`.
- **KCK** — Key Confirmation Key. First 128 bits of the PTK; used
  for the MIC in the 4-way.
- **KEK** — Key Encryption Key. Next 128 bits; wraps the GTK in M3.
- **MDE** — Mobility Domain Element (IE 54). Signals 802.11r-capable AP.
- **MFP** — Management Frame Protection. Same as PMF.
- **MIC** — Message Integrity Code. HMAC over the EAPOL-Key body,
  keyed with KCK.
- **MLD** — Multi-Link Device. Wi-Fi 7 client that operates across
  2.4/5/6 GHz simultaneously. See `wifi7-mlo/`.
- **MODP** — Modular Exponentiation groups (RFC 3526). Dragonblood
  timing-oracle target when hostapd allows them for SAE.
- **OFDMA** — Orthogonal Frequency-Division Multiple Access. 802.11ax.
  Resource Units + Trigger frames.
- **OUI** — Organizationally Unique Identifier. First 3 bytes of a
  MAC or a vendor IE — identifies the vendor.
- **OWE** — Opportunistic Wireless Encryption (AKM 12). Encryption
  on open networks; NOT authentication.
- **Passpoint** — Wi-Fi Alliance profile on top of 802.11u. Automatic
  association via Roaming Consortium OI matching. See `hotspot2/`.
- **PMF** — Protected Management Frames (802.11w). See `std-802-11w`
  record.
- **PMK** — Pairwise Master Key. Derived from PSK+ESSID in WPA2 or from
  SAE commit/confirm in WPA3.
- **PMKID** — PMK Identifier. HMAC-SHA1-128 over ("PMK Name" || MAC_AP
  || MAC_STA). Leaked in M1 by many APs → Steube 2018 fastpath.
  See `pmkid/`.
- **PN** — Packet Number. Per-frame counter in CCMP/GCMP. Reuse under
  the same key breaks confidentiality.
- **PTK** — Pairwise Transient Key. Derived from PMK + nonces + MACs
  in the 4-way. Broken into KCK, KEK, TK.
- **RNR** — Reduced Neighbor Report (IE 201). See `wifi6-6e/`.
- **RSN** — Robust Security Network. Everything WPA2+ in the RSN IE
  (element 48).
- **RU** — Resource Unit. OFDMA subdivision of a channel.
- **SAE** — Simultaneous Authentication of Equals (Dragonfly). WPA3
  personal auth. AKM 8. See `wpa3/`.
- **SNonce** — STA-side nonce (M2).
- **SSID** — Service Set Identifier. Human-readable network name.
- **TIM** — Traffic Indication Map (IE 5). Power-save queue signal.
  See `framing-frames/`.
- **TK** — Temporal Key. Last 128 bits of the PTK; the actual data
  cipher key.
- **TWT** — Target Wake Time (802.11ax). Power-save schedule. See
  `wifi6-6e/`.
- **WIDS/WIPS** — Wireless Intrusion Detection / Prevention System.
- **BIP-CMAC-128 / BIP-CMAC-256** — Broadcast/Multicast Integrity
  Protocol using AES-CMAC. Group-management-frame integrity under PMF.
  Cipher selectors 00-0F-AC:06 (128) and 00-0F-AC:0D (256).
- **BIP-GMAC-128 / BIP-GMAC-256** — GMAC variants of BIP. Selectors
  00-0F-AC:0B and 00-0F-AC:0C. Required for WPA3-Enterprise 192-bit.
- **BSS Color** — 6-bit spatial-reuse identifier (802.11ax). Advertised
  in the HE Operation IE.
- **DTIM** — Delivery Traffic Indication Message. Broadcast/multicast
  wake indicator inside the TIM IE (IE 5).
- **EAPOL** — EAP over LAN. Wrapper for the 4-way handshake key frames
  (EtherType 0x888E).
- **EMSK** — Extended Master Session Key. Additional 64-byte key derived
  by the EAP inner method; typically 0 in Wi-Fi deployments.
- **ESSID** — Extended SSID. Human-readable network name across all
  BSSs in an ESS; identical to SSID in practice.
- **GMK** — Group Master Key. AP-generated random used to derive the
  GTK/IGTK.
- **GO Negotiation** — Group Owner negotiation in Wi-Fi Direct / P2P.
  Determines which peer acts as the AP.
- **MDID** — Mobility Domain Identifier. 2-byte field in the MDE (IE 54)
  that groups FT-capable APs.
- **MFPC** — MFP Capable. Bit 7 of RSN Capabilities. AP/STA supports PMF.
- **MFPR** — MFP Required. Bit 6 of RSN Capabilities. PMF mandatory —
  broadcast deauth no-ops against MFPR-required peers.
- **ML-IE** — Multi-Link Element. Wi-Fi 7 IE (Ext ID 106/107/108/109
  variants) carrying MLD MAC and per-link setup info.
- **MSK** — Master Session Key. 64-byte key exported by the EAP inner
  method; first 32 bytes become the PMK.
- **NAV** — Network Allocation Vector. Duration field in 802.11 headers;
  peers defer for the stated microseconds. CTS-to-self with a large NAV
  is a classic silencing attack.
- **P2P** — Peer-to-Peer / Wi-Fi Direct. Client-to-client Wi-Fi without
  an AP; uses Group Owner + Client roles.
- **PMKSA / PTKSA** — PMK / PTK Security Association. The keying context
  cached on both AP and STA.
- **PSC** — Preferred Scanning Channels. Every 4th 20 MHz channel on 6
  GHz (5, 21, 37, ..., 229) — the channels a client will actually probe.
- **PSK** — Pre-Shared Key. The passphrase-derived 256-bit key used as
  PMK in WPA-Personal.
- **RSNE** — RSN Element (IE 48). Same thing as the RSN IE.
- **RSNXE** — RSN Extension Element (IE 244). Carries the SAE H2E-only
  bit (bit 5) and other post-2018 capability bits (Secure LTF, etc.).
- **SA Query** — Security Association Query. Category 8 Action frame
  pair used to verify a STA is still associated when PMF is required
  and an unprotected disassoc/deauth arrives.
- **TSN** — Transition Security Network. WPA + WPA2 mixed-mode advertised
  in the beacon during a fleet upgrade.
- **TXOP** — Transmission Opportunity. Reserved airtime block; a
  station holding a TXOP can burst up to `TXOP Limit` microseconds.
- **WFD** — Wi-Fi Direct. Same as P2P.
- **WPS PBC** — WPS Push-Button Configuration. 2-minute window during
  which any WPS-capable client can enroll without a PIN.
- **WPS PIN** — 8-digit WPS Personal Identification Number, split into
  two halves for external-registrar authentication. Cracked in
  ~11k tries by Reaver (CVE-2011-5053) unless AP Setup Lock kicks in.

## Wrong entries to avoid duplicating

- **PMKID hashing**. The hash algorithm depends on the AKM: SHA-1 for
  AKM 2 (WPA2-PSK), SHA-256 for AKM 8/12/other SHA-256 KDF AKMs,
  SHA-384 for AKM 12 (Suite-B-192) / 13 (FT-802.1X-SHA384) / 24
  (SAE-EXT-KEY). hashcat mode 22000 handles all three via the WPA*04
  and WPA*05 variants.
- **KCK length varies with PRF.** 128 bits for AKM 2/6 (SHA-1/SHA-256),
  192 bits for AKM 12/13/24 (SHA-384). Never assume "KCK = 16 bytes."

## Growing

Add entries as they earn their keep. Every acronym in a corpus doc
that is not already here belongs here.
