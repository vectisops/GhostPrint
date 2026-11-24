"""Refresh public indicator data used alongside MVT's built-in IOC set."""

import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional
from urllib.error import URLError
from urllib.parse import urlparse
from urllib.request import Request, urlopen


MAX_FEED_BYTES = 50 * 1024 * 1024
MAX_CONFIGURED_FEEDS = 10


def cache_directory() -> Path:
    """Return a persistent per-user location for public indicator data."""
    if os.name == "nt":
        base = os.environ.get("LOCALAPPDATA")
        if base:
            return Path(base) / "GhostPrint" / "indicators"
    return Path.home() / ".cache" / "ghostprint" / "indicators"


def mvt_executable() -> Optional[str]:
    """Locate MVT, including the sidecar used by the Windows installer."""
    if getattr(sys, "frozen", False):
        name = "mvt-ios.exe" if os.name == "nt" else "mvt-ios"
        bundled = Path(sys.executable).resolve().parent / name
        if bundled.is_file():
            return str(bundled)
    return shutil.which("mvt-ios")


def register_indicator_source(directory: Path, url: str) -> str:
    """Persist a user-selected HTTPS STIX2 feed for refreshes on later launches."""
    parsed = urlparse(url.strip())
    if (
        len(url) > 2048
        or parsed.scheme != "https"
        or not parsed.hostname
        or parsed.username
        or parsed.password
    ):
        raise ValueError("Indicator feed URLs must be HTTPS URLs without embedded credentials.")
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    config_path = directory / "sources.json"
    if config_path.is_file():
        sources = json.loads(config_path.read_text(encoding="utf-8"))
        if not isinstance(sources, list):
            raise ValueError("The saved indicator-feed configuration is invalid.")
    else:
        sources = []
    normalized_url = url.strip()
    if any(item.get("url") == normalized_url for item in sources if isinstance(item, dict)):
        raise ValueError("That indicator feed is already configured.")
    if len(sources) >= MAX_CONFIGURED_FEEDS:
        raise ValueError(f"GhostPrint supports up to {MAX_CONFIGURED_FEEDS} additional feeds.")
    name = parsed.hostname
    existing_names = {item["name"] for item in sources if isinstance(item, dict)}
    suffix = 2
    base_name = name
    while name in existing_names:
        name = f"{base_name}-{suffix}"
        suffix += 1
    sources.append({"name": name, "url": normalized_url})
    temporary_path = config_path.with_suffix(".tmp")
    temporary_path.write_text(json.dumps(sources, indent=2), encoding="utf-8")
    os.replace(temporary_path, config_path)
    return name


def _read_sources(directory: Path) -> list:
    config_path = directory / "sources.json"
    if not config_path.exists():
        return []
    sources = json.loads(config_path.read_text(encoding="utf-8"))
    if not isinstance(sources, list) or len(sources) > MAX_CONFIGURED_FEEDS:
        raise ValueError("The saved indicator-feed configuration is invalid.")
    for source in sources:
        if not isinstance(source, dict) or not isinstance(source.get("name"), str):
            raise ValueError("The saved indicator-feed configuration is invalid.")
        source_url = source.get("url", "")
        if not isinstance(source_url, str) or len(source_url) > 2048:
            raise ValueError("A saved indicator feed is not a valid HTTPS URL.")
        parsed = urlparse(source_url)
        if (
            parsed.scheme != "https"
            or not parsed.hostname
            or parsed.username
            or parsed.password
        ):
            raise ValueError("A saved indicator feed is not a valid HTTPS URL.")
    return sources


def _download_stix(destination: Path, url: str, timeout: int) -> None:
    request = Request(url, headers={"User-Agent": "GhostPrint/1.0"})
    with urlopen(request, timeout=timeout) as response:
        final_url = urlparse(response.geturl())
        if final_url.scheme != "https":
            raise ValueError("The indicator feed redirected away from HTTPS.")
        raw = response.read(MAX_FEED_BYTES + 1)
    if len(raw) > MAX_FEED_BYTES:
        raise ValueError("The STIX indicator feed exceeded the 50 MiB safety limit.")
    bundle = json.loads(raw.decode("utf-8"))
    if (
        not isinstance(bundle, dict)
        or bundle.get("type") != "bundle"
        or not isinstance(bundle.get("objects"), list)
        or not any(
            isinstance(item, dict) and item.get("type") == "indicator"
            for item in bundle["objects"]
        )
    ):
        raise ValueError("The downloaded file was not a STIX2 bundle containing indicators.")
    destination.parent.mkdir(parents=True, exist_ok=True)
    file_descriptor, temporary_name = tempfile.mkstemp(
        prefix=".indicator-feed-", suffix=".tmp", dir=str(destination.parent)
    )
    try:
        with os.fdopen(file_descriptor, "w", encoding="utf-8") as file:
            json.dump(bundle, file)
        os.replace(temporary_name, destination)
    except OSError:
        try:
            os.unlink(temporary_name)
        except OSError:
            pass
        raise


def refresh_indicator_sets(
    directory: Optional[Path] = None,
    timeout: int = 30,
    mvt_command: Optional[str] = None,
) -> Dict[str, Dict[str, Any]]:
    """Refresh MVT's official indicators and all configured HTTPS STIX2 feeds."""
    directory = Path(directory) if directory is not None else cache_directory()
    directory.mkdir(parents=True, exist_ok=True)
    results: Dict[str, Dict[str, Any]] = {}

    command = mvt_command or mvt_executable()
    if command:
        try:
            completed = subprocess.run(
                [command, "download-iocs"],
                capture_output=True,
                text=True,
                timeout=240,
                check=False,
            )
            if completed.returncode == 0:
                updated_at = datetime.now(timezone.utc).isoformat()
                status_path = directory / "amnesty-status.json"
                temporary_status = status_path.with_suffix(".tmp")
                temporary_status.write_text(
                    json.dumps({"last_updated": updated_at}), encoding="utf-8"
                )
                os.replace(temporary_status, status_path)
                results["amnesty"] = {
                    "ok": True,
                    "message": "Amnesty/MVT indicator data refreshed.",
                    "last_updated": updated_at,
                }
            else:
                detail = (completed.stderr or completed.stdout).strip()
                results["amnesty"] = {
                    "ok": False,
                    "message": detail or f"MVT updater exited with code {completed.returncode}.",
                }
        except (OSError, subprocess.TimeoutExpired) as error:
            results["amnesty"] = {"ok": False, "message": str(error)}
    else:
        results["amnesty"] = {
            "ok": False,
            "message": "MVT is not installed; its Amnesty indicator updater is unavailable.",
        }
    if not results["amnesty"].get("last_updated"):
        status_path = directory / "amnesty-status.json"
        try:
            previous = json.loads(status_path.read_text(encoding="utf-8"))
            results["amnesty"]["last_updated"] = previous.get("last_updated")
        except (OSError, UnicodeError, ValueError, AttributeError):
            results["amnesty"]["last_updated"] = None

    try:
        sources = _read_sources(directory)
    except (OSError, UnicodeError, ValueError) as error:
        results["feeds"] = {"ok": False, "message": str(error)}
        return results

    for source in sources:
        name = source["name"]
        feed_path = directory / (hashlib.sha256(source["url"].encode("utf-8")).hexdigest() + ".stix.json")
        try:
            _download_stix(feed_path, source["url"], timeout)
            results[f"feed:{name}"] = {
                "ok": True,
                "message": f"{name} STIX2 indicator data refreshed.",
                "source_url": source["url"],
                "path": str(feed_path),
                "indicator_count": _indicator_count(feed_path),
                "last_updated": datetime.fromtimestamp(
                    feed_path.stat().st_mtime, timezone.utc
                ).isoformat(),
            }
        except (OSError, UnicodeError, ValueError, URLError, TimeoutError) as error:
            cached_count = None
            cached_updated = None
            cached_path = None
            if feed_path.is_file():
                try:
                    cached_count = _indicator_count(feed_path)
                    cached_updated = datetime.fromtimestamp(
                        feed_path.stat().st_mtime, timezone.utc
                    ).isoformat()
                    cached_path = str(feed_path)
                except (OSError, UnicodeError, ValueError, KeyError, TypeError):
                    error = ValueError(
                        f"{error}; the cached feed is invalid and will not be used."
                    )
            results[f"feed:{name}"] = {
                "ok": False,
                "message": str(error),
                "source_url": source["url"],
                "path": cached_path,
                "indicator_count": cached_count,
                "last_updated": cached_updated,
            }
    return results


def _indicator_count(path: Path) -> int:
    bundle = json.loads(path.read_text(encoding="utf-8"))
    if (
        not isinstance(bundle, dict)
        or bundle.get("type") != "bundle"
        or not isinstance(bundle.get("objects"), list)
    ):
        raise ValueError("The cached file is not a STIX2 bundle.")
    return sum(
        1
        for item in bundle["objects"]
        if isinstance(item, dict) and item.get("type") == "indicator"
    )
