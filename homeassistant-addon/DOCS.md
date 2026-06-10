# Vinted Notifications — Home Assistant add-on

Runs [Vinted-Notifications](https://github.com/jscarrott/Vinted-Notifications)
as a Home Assistant OS add-on. The web UI, Telegram and RSS work out of the
box. Signal and Cloudflare-bypass (FlareSolverr) are handled by separate
community add-ons (see below).

## Prerequisites

Push your changes to your fork first:

```bash
git push origin main
```

The add-on ships with **prebuilt images**. On every push to `main` that
touches `homeassistant-addon/**`, the `Build add-on images` GitHub Action
builds `aarch64`/`amd64`/`armv7` images and pushes them to GHCR
(`ghcr.io/jscarrott/<arch>-vinted-notifications`). Home Assistant then *pulls*
the image instead of building on-device, so installs are fast.

After the first successful workflow run, **make the GHCR packages public** so
HA can pull them without auth: GitHub → your profile → Packages → each
`*-vinted-notifications` package → Package settings → Change visibility →
Public.

> Build on-device instead? Remove the `image:` line from `config.yaml`. Then HA
> builds the `Dockerfile`, which clones the app from GitHub at build time
> (override the source with the `VN_REPO` / `VN_REF` build args).

## Install

1. In Home Assistant: **Settings → Add-ons → Add-on Store → ⋮ (top right) →
   Repositories**.
2. Add: `https://github.com/jscarrott/Vinted-Notifications`
3. The **Vinted Notifications** add-on appears in the store. Open it and click
   **Install** (first build takes a few minutes — it clones and pip-installs).
4. **Start** the add-on, then click **Open Web UI** (or browse to
   `http://<HA-host>:8000`).

All configuration — queries, Telegram, Signal, RSS, proxies — is done in the
web UI and stored in the SQLite database on the persistent `/data` mount, so it
survives restarts and updates.

## Ports

| Port | Purpose |
|------|---------|
| 8000 | Web UI  |
| 8080 | RSS feed |

## Signal (optional)

This add-on does **not** bundle Signal. Install a community
`signal-cli-rest-api` add-on, then point this app at it:

1. Add a community add-on repository that provides **signal-cli-rest-api**
   (search the community / forums for a maintained one), install and start it.
2. Link your Signal account (Linked Devices → scan the QR from that add-on's
   `/v1/qrcodelink` endpoint). Do **not** re-register your primary number.
3. In the Vinted web UI → **Config → Signal**, set:
   - **Signal API URL**: `http://<HA-host-ip>:<signal-addon-port>`
     (use the host IP and the port the Signal add-on publishes; this is the
     most reliable way for add-ons to reach each other)
   - **Phone Number** and **Recipient**: your Signal numbers
4. Enable Signal and Start it.

## FlareSolverr (optional, only if Vinted starts Cloudflare-challenging you)

FlareSolverr is **not** an HTTP proxy — do not put it in the Proxy List. Install
a community **FlareSolverr** add-on if/when you need it; it requires a code
integration in `pyVintedVN/requester.py` (call its `/v1` API, reuse the
returned `cf_clearance` cookie + user-agent). Until that integration exists,
leave it unused.

## Proxies (optional)

The **Config → Proxy Settings** panel takes ordinary HTTP/SOCKS forward
proxies (IP rotation to dodge rate limits), semicolon-separated. Note SOCKS5
support needs `PySocks` and a small fix to the proxy-dict handling — not wired
up yet.

## Data location

- Database: `/data/vinted_notifications.db`
- Logs: `/data/logs/vinted.log`

Both live on the add-on's persistent volume.
