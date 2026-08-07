# PMKID capture (Steube 2018)

## The primitive

WPA2's M1 message optionally carries a **PMKID** field in the EAPOL-Key
IE. The PMKID is:

```
PMKID = HMAC-SHA1-128(PMK, "PMK Name" || MAC_AP || MAC_STA)[0..15]
```

If we can capture one M1 that carries a PMKID, we have everything
hashcat mode 22000 needs to attempt an offline dictionary attack on
the PMK — without waiting for a client to complete a 4-way.

## Why APs emit it

The PMKID field is defined for **PMKSA caching** — a re-associating STA
can present a PMKID to skip re-authentication. Many APs emit the PMKID
in every M1 by default, whether or not the target STA is caching.

## When it doesn't work

- AP firmware suppresses PMKID emission (a documented mitigation).
- AP is WPA3-SAE only (no WPA2 transition side).
- The PSK is not in a reachable wordlist.

## Tooling

- `hcxdumptool` — captures the pcap.
- `hcxpcapngtool -o <out.22000> <in.pcapng>` — extracts hashes.
- `hashcat -m 22000 <out.22000> <wordlist>` — cracks.

The 22000 line for a PMKID looks like:

```
WPA*01*<PMKID>*<AP_MAC>*<STA_MAC>*<ESSID hex>***
```

## Cite

- Steube 2018 — hashcat forum thread 7717.
- hashcat wiki — example hashes, mode 22000.
- hcxtools GitHub — hcxdumptool README.
