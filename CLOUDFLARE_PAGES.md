# Cloudflare Pages deployment

This repository is the deployment source for the Adventurers Guild PWA.

Cloudflare Pages settings:

- Production branch: `main`
- Build command: `python3 cloudflare-pages-build.py`
- Build output directory: `dist`
- Root directory: repository root
- Environment variables: none required

Every successful unified Beta release updates `version.json`. Cloudflare Pages
will rebuild automatically, download the exact PWA ZIP referenced by that
manifest, verify its byte size and SHA-256, and publish it.

A custom domain such as `guild.apixb.top` can be attached in Cloudflare Pages.
