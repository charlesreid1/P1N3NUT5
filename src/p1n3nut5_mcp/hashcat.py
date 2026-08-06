"""
Thin wrapper around a local hashcat install.

Phase 0 stub. Backs the crack tools:

  * `convert_to_hashcat(pcap_path, mode=22000|2500, out_path?)` — wraps
    `hcxpcapngtool`; mode 22000 (PMKID/EAPOL, all-in-one 2018+) is the
    default per plan-knowledge.md
  * `crack_start(hash_path, wordlist_path?, rules_path?, mode)` — spawns
    hashcat, returns a job id
  * `crack_status(job_id)` / `crack_result(job_id)` / `crack_stop(job_id)`

Honors `HASHCAT_PATH` and `WORDLIST_DIR` from the env-var table in
plan-organize.md.
"""

from __future__ import annotations
