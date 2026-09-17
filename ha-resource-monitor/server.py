#!/usr/bin/env python3
"""Small, dependency-free web UI for Home Assistant Supervisor statistics."""

from __future__ import annotations

import json
import logging
import os
import time
import urllib.error
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any

PORT = 8099
STATIC = Path(__file__).parent / "static"
SUPERVISOR = os.environ.get("SUPERVISOR_URL", "http://supervisor").rstrip("/")
TOKEN = os.environ.get("SUPERVISOR_TOKEN", "")
LOG = logging.getLogger("ha-resource-monitor")


def api_get(path: str) -> dict[str, Any]:
    request = urllib.request.Request(
        f"{SUPERVISOR}{path}",
        headers={"Authorization": f"Bearer {TOKEN}", "Accept": "application/json"},
    )
    try:
        with urllib.request.urlopen(request, timeout=8) as response:
            payload = json.load(response)
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
        raise RuntimeError(f"Supervisor API {path}: {exc}") from exc
    if payload.get("result") not in (None, "ok"):
        raise RuntimeError(payload.get("message") or f"Błąd Supervisor API: {path}")
    return payload.get("data", payload)


def first_api(paths: list[str]) -> dict[str, Any]:
    errors = []
    for path in paths:
        try:
            return api_get(path)
        except RuntimeError as exc:
            errors.append(str(exc))
    raise RuntimeError("; ".join(errors))


def normalize(name: str, kind: str, stats: dict[str, Any], slug: str = "") -> dict[str, Any]:
    return {
        "name": name,
        "kind": kind,
        "slug": slug,
        "memory_usage": int(stats.get("memory_usage") or 0),
        "memory_limit": int(stats.get("memory_limit") or 0),
        "memory_percent": float(stats.get("memory_percent") or 0),
        "cpu_percent": float(stats.get("cpu_percent") or 0),
        "network_rx": int(stats.get("network_rx") or 0),
        "network_tx": int(stats.get("network_tx") or 0),
        "blk_read": int(stats.get("blk_read") or 0),
        "blk_write": int(stats.get("blk_write") or 0),
    }


def addon_stats(addon: dict[str, Any]) -> dict[str, Any] | None:
    slug = addon.get("slug", "")
    encoded = urllib.parse.quote(slug, safe="")
    try:
        stats = first_api([f"/addons/{encoded}/stats", f"/apps/{encoded}/stats"])
        return normalize(addon.get("name") or slug, "addon", stats, slug)
    except RuntimeError as exc:
        LOG.warning("Nie udało się pobrać statystyk %s: %s", slug, exc)
        return None


def collect() -> dict[str, Any]:
    core = first_api(["/core/stats"])
    listing = first_api(["/addons", "/apps"])
    addons = listing.get("addons") or listing.get("apps") or []
    running = [item for item in addons if item.get("state") == "started"]

    warnings = []
    components = [normalize("Home Assistant Core", "core", core, "core")]
    with ThreadPoolExecutor(max_workers=min(8, max(1, len(running)))) as pool:
        futures = [pool.submit(addon_stats, addon) for addon in running]
        for future in as_completed(futures):
            item = future.result()
            if item:
                components.append(item)
            else:
                warnings.append("Brak odczytu jednej z uruchomionych aplikacji.")

    # Supervisor stats are available on supported HA OS versions. Failure is non-fatal.
    try:
        components.append(normalize("Supervisor", "supervisor", api_get("/supervisor/stats"), "supervisor"))
    except RuntimeError:
        warnings.append("Statystyki Supervisora są niedostępne.")

    components.sort(key=lambda item: item["memory_usage"], reverse=True)
    known_memory = sum(item["memory_usage"] for item in components)
    memory_limit = max((item["memory_limit"] for item in components), default=0)
    return {
        "timestamp": int(time.time()),
        "components": components,
        "warnings": warnings,
        "summary": {
            "known_memory": known_memory,
            "memory_limit": memory_limit,
            "known_percent": (known_memory / memory_limit * 100) if memory_limit else 0,
            "cpu_sum": sum(item["cpu_percent"] for item in components),
            "running_addons": len(running),
        },
    }


class Handler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:  # noqa: N802
        path = urllib.parse.urlparse(self.path).path.rstrip("/")
        if path.endswith("/api/stats") or path == "/api/stats":
            try:
                self.send_json(collect())
            except Exception as exc:  # Keep UI alive and return a useful diagnostic.
                LOG.exception("Błąd pobierania danych")
                self.send_json({"error": str(exc)}, 502)
            return

        filename = "app.js" if path.endswith("/app.js") else "style.css" if path.endswith("/style.css") else "index.html"
        mime = {"app.js": "text/javascript; charset=utf-8", "style.css": "text/css; charset=utf-8", "index.html": "text/html; charset=utf-8"}[filename]
        body = (STATIC / filename).read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", mime)
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def send_json(self, payload: dict[str, Any], status: int = 200) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, fmt: str, *args: Any) -> None:
        LOG.info(fmt, *args)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    if not TOKEN:
        LOG.warning("Brak SUPERVISOR_TOKEN — uruchom dodatek wewnątrz Home Assistant OS")
    LOG.info("HA Resource Monitor działa na porcie %s", PORT)
    ThreadingHTTPServer(("0.0.0.0", PORT), Handler).serve_forever()
