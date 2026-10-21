#!/usr/bin/env python3
"""Build the latest published Adventurers Guild PWA for Cloudflare Pages.

The release manifest is the single source of truth. Each successful unified
Beta publish updates version.json; Cloudflare Pages then rebuilds this site,
downloads the matching PWA ZIP, verifies it, and exposes it from dist/.
"""

from __future__ import annotations

import hashlib
import json
import shutil
import urllib.request
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent
MANIFEST = ROOT / "version.json"
OUTPUT = ROOT / "dist"
ARCHIVE = ROOT / ".cloudflare-pwa.zip"


def safe_extract(zf: zipfile.ZipFile, destination: Path) -> None:
    root = destination.resolve()
    for member in zf.infolist():
        target = (destination / member.filename).resolve()
        if target != root and root not in target.parents:
            raise SystemExit(f"Unsafe ZIP member: {member.filename}")
    zf.extractall(destination)


def main() -> None:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    if not manifest.get("published"):
        raise SystemExit("version.json is not marked published")

    url = manifest.get("pwa_download_url")
    expected_sha = str(manifest.get("pwa_sha256") or "").lower()
    expected_size = int(manifest.get("pwa_size_bytes") or 0)
    if not url or not expected_sha or not expected_size:
        raise SystemExit("PWA release metadata is incomplete in version.json")

    request = urllib.request.Request(
        url,
        headers={"User-Agent": "adventurers-guild-cloudflare-pages/1"},
    )
    with urllib.request.urlopen(request, timeout=180) as response:
        data = response.read()

    if len(data) != expected_size:
        raise SystemExit(
            f"PWA size mismatch: got {len(data)}, expected {expected_size}"
        )

    actual_sha = hashlib.sha256(data).hexdigest()
    if actual_sha != expected_sha:
        raise SystemExit(
            f"PWA SHA-256 mismatch: got {actual_sha}, expected {expected_sha}"
        )

    if OUTPUT.exists():
        shutil.rmtree(OUTPUT)
    OUTPUT.mkdir(parents=True)
    ARCHIVE.write_bytes(data)

    with zipfile.ZipFile(ARCHIVE) as zf:
        safe_extract(zf, OUTPUT)
    ARCHIVE.unlink(missing_ok=True)

    required = (
        "index.html",
        "manifest.json",
        "flutter_bootstrap.js",
        "main.dart.js",
        "pwa_service_worker.js",
    )
    missing = [name for name in required if not (OUTPUT / name).is_file()]
    if missing:
        raise SystemExit("PWA package is missing: " + ", ".join(missing))

    # Keep the update-critical shell files revalidated at the edge.
    (OUTPUT / "_headers").write_text(
        "/pwa_service_worker.js\n"
        "  Cache-Control: no-cache, no-store, must-revalidate\n"
        "/index.html\n"
        "  Cache-Control: no-cache, must-revalidate\n"
        "/flutter_bootstrap.js\n"
        "  Cache-Control: no-cache, must-revalidate\n",
        encoding="utf-8",
    )
    (OUTPUT / "_redirects").write_text("/* /index.html 200\n", encoding="utf-8")
    (OUTPUT / "build-meta.json").write_text(
        json.dumps(
            {
                "version": manifest.get("version"),
                "build": manifest.get("build"),
                "channel": manifest.get("channel"),
                "pwa_sha256": actual_sha,
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    print(
        "Cloudflare Pages output ready: "
        f"{manifest.get('version')}+{manifest.get('build')} -> {OUTPUT}"
    )


if __name__ == "__main__":
    main()
