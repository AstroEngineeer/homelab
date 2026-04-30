# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What This Repo Is

A homelab Docker Compose configuration. Each service lives in its own subdirectory with a `compose.yaml`. Services are managed via Dockge at `/home/debian/homelab`.

## Common Commands

```bash
# Start/stop a service stack
docker compose -f <service>/compose.yaml up -d
docker compose -f <service>/compose.yaml down

# Bootstrap the shared network (run once on a new host)
bash xutils/create-docker-networks.sh

# Format/normalize a compose file (targets staging-compose.yaml by default — edit find_compose_files() to target others)
python3 xutils/refactor-docker-compose.py
```

## Architecture

**Network:** `tk-proxy` (short for "traefik proxy") is the external bridge network that Traefik watches for container labels. **Any service that needs a hostname / public route must be on `tk-proxy`** — Traefik can only reach containers it shares a network with. Create it once per host with `xutils/create-docker-networks.sh`. Exceptions to the default attachment:
- `beszel-agent` and `scanopy-daemon` run with `network_mode: host` (need to see host network for monitoring/scanning) — they don't need Traefik routing
- The `*arr` services and `flaresolverr` use `network_mode: container:qbittorrentvpn`, sharing the VPN container's namespace. Because `qbittorrentvpn` itself is attached to `tk-proxy`, Traefik reaches the *arr WebUIs through it — so their Traefik labels are declared on `qbittorrentvpn`, not on the individual services

**Reverse proxy:** Traefik handles TLS termination and routing. Each service declares its own routing rules and port via Docker labels. The domain is purchased and managed in Cloudflare (DNS only — no Cloudflare tunnel). Three subdomains point to different entry points:
- `*.local.<domain>` — points to `matrix`'s static LAN IP; only reachable on the local network
- `*.ts.<domain>` — points to `domainforge` (Raspberry Pi Zero 2W), static LAN IP, configured via Tailscale DNS settings
- `*.cf.<domain>` — points to `matrix`'s Tailscale IP; same machine as `.local.` but accessed over Tailscale

Traefik config is split between two files in `traefik/container_data/traefik/`:
- `traefik.yml` — static config (entrypoints, providers, certresolver definitions)
- `config.yml` — file-provider dynamic config containing routes for services hosted on `domainforge` (the Pi). Services running on `matrix` declare their own routes via Docker labels; services on the Pi can't, so they're defined here as static file routes pointing to the Pi's backends.

TLS certificates are obtained via Cloudflare DNS challenge (API token in `traefik/.env`). Cert state lives in `traefik/container_data/traefik/acme.json` — losing this file forces full reissuance, which is rate-limited by Let's Encrypt; treat it as critical.

**LAN:** Subnet is hardcoded in the router. The same value must stay in sync in `qbittorrent_arr/compose.yaml` (`LAN_NETWORK`) — it's the only subnet the VPN killswitch lets bypass the tunnel, so LAN clients can reach the qBit/`*arr` WebUIs.

**LAN DNS:** `domainforge` (Pi Zero 2W, DietPi) runs AdGuard Home. The router uses it as primary DNS; secondary is `1.1.1.1`. Internal hostname resolution and ad-blocking happen there.

**Tailscale ACL:** Two Tailscale accounts are in use:
- `tag:owner` (admin account) — full access to all ports and SSH on owner-tagged devices
- `tag:member` (shared account used by friends) — restricted to the server's port 80 and 443 only (Traefik ingress), cannot reach any other device or port

The effect is that friends can reach services exposed through Traefik on the `.cf.` domain but have no lateral movement within the tailnet.

**VPN-isolated stack (`qbittorrent_arr`):** All traffic for the *arr services and FlareSolverr is forced through the OpenVPN tunnel inside `qbittorrentvpn` (ProtonVPN). Killswitch is enforced by the VPN container's iptables rules — if the tunnel drops, none of the dependent containers can reach the internet. `VPN_INPUT_PORTS` in `qbittorrent_arr/.env` whitelists the WebUI ports through the firewall.

**Jellyfin:** Uses Intel VA-API via `/dev/dri/renderD128` with `group_add: '105'` (the host `render` group) for H.264 hardware transcoding. JellySearch intercepts search queries at the Traefik router level and proxies them to MeiliSearch. Transcode temp is on the SSD (`./container_data/jellyfin/transcode`), cache on SSD (`./container_data/jellyfin/cache`).

**Media data layout (`/mnt/void/data`):** Shared filesystem contract across the media stack:
- `/mnt/void/data/torrents` — qBittorrent download target
- `/mnt/void/data/media` — final library, consumed by Jellyfin and Bazarr
- qBittorrent and the *arrs all bind-mount `/mnt/void/data` (the parent), not just their subtree. This is intentional — it lets the *arrs hardlink between `torrents/` and `media/` instead of copying. Changing the mount paths to point at the subtree directly will silently double disk usage.

**Host-specific paths:** A few bind mounts assume this is `matrix`:
- `/mnt/void/.beszel` (beszel-agent disk monitoring)
- `/dev/dri/renderD128` + `group_add: '105'` (Jellyfin GPU/render group)
- `/home/debian/homelab` (Dockge stack directory)

These need adjusting if the repo moves to a different host.

**Secrets and data:** `.env` files (gitignored) hold secrets referenced as `${VAR}`. Persistent data lives in `<service>/container_data/` (gitignored).

**Backups:** None currently. `xutils/backup.sh` is a WIP scaffold and not in use — `container_data/` and `acme.json` are not snapshotted anywhere. To-do.

**Inbound ports:** No port forwarding is configured on the router — nothing on this host is reachable from the public internet, only from LAN and Tailscale. Only Traefik's `80` and `443` are published to the host.

**Tribal-knowledge Traefik middlewares** (easy to break inadvertently when editing labels):
- `qbittorrent` — clears `Origin` and `Referer` headers and sets `passhostheader: false`. qBit's CSRF check rejects requests where `Origin` doesn't match the bind address; clearing them is what makes the WebUI work behind Traefik.
- `jellyfin` — full HSTS hardening (preload, includeSubdomains, 10-year max-age), `frameDeny`, `contentTypeNosniff`, plus a custom `X-Robots-Tag: noindex,nofollow,...` so the public Jellyfin URL doesn't show up in search engines.
- `whoami` — injects `Connection: Upgrade` / `Upgrade: websocket` headers (it's a WebSocket demo).

**Observability:** Beszel (host metrics + agent), Uptime Kuma (HTTP uptime), Dozzle (live container logs), Homepage (dashboard). Start here when something looks wrong.

## Compose File Conventions

- Volumes use the expanded bind-mount format with explicit `read_only` keys. Host paths for persistent data follow `./container_data/<container_name>/<basename>` where `<basename>` matches the last component of the container-side path (e.g. `/app/config` → `./container_data/homepage/config`, `/beszel_data` → `./container_data/beszel/beszel_data`).
- `environment` and `labels` sections use dict format (not list), sorted alphabetically.
- `restart: unless-stopped` on all services.
- LinuxServer.io images use `PUID: 1000`, `PGID: 1000`, `TZ: Asia/Kolkata`.
- Service keys within each service block are sorted alphabetically. This is followed manually — `xutils/refactor-docker-compose.py` exists as a one-off helper but is hardcoded to format `staging-compose.yaml` only and is not part of any automated workflow.
