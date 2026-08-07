# karma-family

The attack family tree PineAP implements one subset of. KARMA (2004)
answers every probe request positively; MANA (2014) does it per-STA
so it's harder to fingerprint; MANA Loud broadcasts the union of all
seen probes; Known Beacons (2018) beacons a curated SSID dictionary
to farm associations; Snoopy uses probe correlation to track people
geographically.

Read this dir alongside `pineap/` — PineAP is the Mark VII's KARMA-
family engine, and each family member maps to a specific set of
PineAP toggles.

Records: `karma_family.json` has one entry per member and one for
each PineAP-implementation slice.
