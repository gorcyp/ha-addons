#!/usr/bin/env python3
"""Small, dependency-free web UI for Home Assistant Supervisor statistics."""

from __future__ import annotations

import json
import logging
import os
import re
import secrets
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any

PORT = 8099
STATIC = Path(__file__).parent / "static"
SUPERVISOR = os.environ.get("SUPERVISOR_URL", "http://supervisor").rstrip("/")
TOKEN = os.environ.get("SUPERVISOR_TOKEN", "")
LOG = logging.getLogger("ha-resource-monitor")
CSRF_TOKEN = secrets.token_urlsafe(32)
SNAPSHOT = None
SNAPSHOT_AT = 0.0
SNAPSHOT_LOCK = threading.Lock()
STOP_LOCK = threading.Lock()


def api_get(path: str, method: str = "GET") -> dict[str, Any]:
    request = urllib.request.Request(
        f"{SUPERVISOR}{path}",
        headers={"Authorization": f"Bearer {TOKEN}", "Accept": "application/json"},
        method=method,
    )
    try:
        with urllib.request.urlopen(request, timeout=60 if method == "POST" else 8) as response:
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


def read_swap(path: Path = Path("/proc/meminfo")) -> dict[str, Any]:
    """Kernel-wide counters on HAOS; never substitute missing readings with zero."""
    try:
        values = {}
        for line in path.read_text().splitlines():
            key, _, value = line.partition(":")
            if key in ("SwapTotal", "SwapFree"):
                parts = value.split()
                if len(parts) != 2 or parts[1] != "kB":
                    raise ValueError("Invalid swap unit")
                values[key] = int(parts[0]) * 1024
        total, free = values["SwapTotal"], values["SwapFree"]
        if not 0 <= free <= total:
            raise ValueError("Invalid swap counters")
        return {"available": True, "total": total, "free": free,
                "used": total - free, "percent": (total - free) / total * 100 if total else 0,
                "source": "/proc/meminfo"}
    except (OSError, ValueError, KeyError):
        return {"available": False, "total": None, "free": None,
                "used": None, "percent": None, "source": "/proc/meminfo"}


def collect() -> dict[str, Any]:
    core = first_api(["/core/stats"])
    listing = first_api(["/addons", "/apps"])
    addons = listing.get("addons") or listing.get("apps") or []
    running = [item for item in addons if item.get("state") == "started"]

    warnings = []
    components = [normalize("Home Assistant Core", "core", core, "core")]
    for addon in running:
        item = addon_stats(addon)
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
    for item in components:
        item["can_stop"] = item["kind"] == "addon" and not item["slug"].endswith("_ha_resource_monitor")
    known_memory = sum(item["memory_usage"] for item in components)
    memory_limit = max((item["memory_limit"] for item in components), default=0)
    return {
        "timestamp": int(time.time()),
        "csrf_token": CSRF_TOKEN,
        "components": components,
        "swap": read_swap(),
        "warnings": warnings,
        "summary": {
            "known_memory": known_memory,
            "memory_limit": memory_limit,
            "known_percent": (known_memory / memory_limit * 100) if memory_limit else 0,
            "cpu_sum": sum(item["cpu_percent"] for item in components),
            "running_addons": len(running),
        },
    }


def snapshot():
    global SNAPSHOT, SNAPSHOT_AT
    with SNAPSHOT_LOCK:
        if SNAPSHOT is None or time.monotonic() - SNAPSHOT_AT >= 5:
            SNAPSHOT = collect()
            SNAPSHOT_AT = time.monotonic()
        return SNAPSHOT


def stop_addon(slug):
    global SNAPSHOT
    if not isinstance(slug, str) or not re.fullmatch(r"[a-z0-9_]+", slug):
        raise ValueError("Nieprawidłowa aplikacja.")
    if slug in ("core", "supervisor", "self") or slug.endswith("_ha_resource_monitor"):
        raise ValueError("Tego komponentu nie można zatrzymać z panelu.")
    with STOP_LOCK:
        listing = api_get("/addons")
        candidates = listing.get("addons", listing.get("apps", []))
        if not any(x.get("slug") == slug and x.get("state") == "started" for x in candidates):
            raise ValueError("Aplikacja nie jest uruchomiona lub nie istnieje.")
        try:
            api_get(f"/addons/{slug}/stop", method="POST")
        finally:
            with SNAPSHOT_LOCK:
                SNAPSHOT = None
    return {"message": "Supervisor przyjął zatrzymanie aplikacji."}


class Handler(BaseHTTPRequestHandler):
    def trusted_ingress(self):
        return self.client_address[0] == "172.30.32.2"

    def do_POST(self):
        if not self.trusted_ingress() or not secrets.compare_digest(self.headers.get("X-CSRF-Token", ""), CSRF_TOKEN):
            self.send_json({"error": "Odmowa dostępu. Otwórz panel przez Home Assistant."}, 403)
            return
        if urllib.parse.urlparse(self.path).path.rstrip("/") != "/api/stop":
            self.send_json({"error": "Nieznana operacja."}, 404)
            return
        try:
            length = int(self.headers.get("Content-Length", "0"))
            if not 0 < length <= 1024:
                raise ValueError("Nieprawidłowe żądanie.")
            body = json.loads(self.rfile.read(length))
            if not isinstance(body, dict):
                raise ValueError("Nieprawidłowe żądanie.")
            self.send_json(stop_addon(body.get("slug")))
        except (ValueError, TypeError) as exc:
            self.send_json({"error": str(exc)}, 400)
        except RuntimeError:
            self.send_json({"error": "Nie potwierdzono zatrzymania. Sprawdź stan aplikacji w HA przed ponowieniem."}, 502)

    def do_GET(self) -> None:  # noqa: N802
        if not self.trusted_ingress():
            self.send_json({"error": "Otwórz panel przez Ingress Home Assistanta."}, 403)
            return
        path = urllib.parse.urlparse(self.path).path.rstrip("/")
        if path.endswith("/api/stats") or path == "/api/stats":
            try:
                self.send_json(snapshot())
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
        LOG.debug(fmt, *args)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    if not TOKEN:
        LOG.warning("Brak SUPERVISOR_TOKEN — uruchom dodatek wewnątrz Home Assistant OS")
    LOG.info("HA Resource Monitor działa na porcie %s", PORT)
    ThreadingHTTPServer(("0.0.0.0", PORT), Handler).serve_forever()
