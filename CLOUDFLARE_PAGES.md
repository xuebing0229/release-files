# Cloudflare Workers deployment

This repository is the deployment source for the Adventurers Guild PWA at
`guild.apixb.top`.

Cloudflare Git settings:

- Production branch: `main`
- Build command: `python3 cloudflare-pages-build.py`
- Deploy command: `npx wrangler deploy`
- Root directory: repository root
- Worker name: `adventurers-guild-pwa`

Every successful unified Beta release updates `version.json`. Cloudflare then
rebuilds this repository, downloads the exact PWA ZIP referenced by the
manifest, verifies its size and SHA-256, and publishes it from `dist/`.

The same Worker now also exposes:

- `/sync`: hibernatable Durable Object WebSocket relay.
- `/sync-health`: relay health check.

## Sync privacy boundary

The Worker does not save Adventurers Guild workspace messages or maintain an
offline queue. Android, Windows and PWA encrypt application payloads with
AES-GCM before sending them to the relay, and both endpoints must be online at
the same time. Cloudflare still necessarily handles network-layer metadata such
as connection IPs/timestamps while carrying the WebSocket connection.

The Durable Object namespace uses the SQLite backend because Cloudflare
requires it for new namespaces, but this relay never writes business payloads
to Durable Object storage.

## Native clients

Android and Windows default to:

```
https://guild.apixb.top/sync
```

A test environment can override that at build time with
`PUBLIC_SYNC_RELAY_URL`.
