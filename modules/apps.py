"""Installed apps listing and basic heuristics."""

import subprocess
from typing import List, Dict, Optional
from .device import DeviceError, _run


def list_installed_apps(udid: Optional[str] = None) -> List[Dict[str, str]]:
    """
    List installed applications using ideviceinstaller.

    Returns list of dicts with at least 'cfbundleidentifier' and 'cfbundledisplayname'
    when available.
    """
    cmd = ["ideviceinstaller"]
    if udid:
        cmd.extend(["-u", udid])
    cmd.extend(["-l"])

    try:
        out = _run(cmd, timeout=120)
    except DeviceError as e:
        # Fallback: some systems use different flags
        raise DeviceError(f"Could not list apps: {e}")

    apps = []
    for line in out.splitlines():
        line = line.strip()
        if not line or line.startswith("Total:"):
            continue
        # Typical format: com.example.app - App Name - Version
        parts = [p.strip() for p in line.split(" - ")]
        if len(parts) >= 1:
            entry = {"identifier": parts[0]}
            if len(parts) >= 2:
                entry["name"] = parts[1]
            if len(parts) >= 3:
                entry["version"] = parts[2]
            apps.append(entry)
    return apps


def flag_suspicious_apps(apps: List[Dict[str, str]]) -> List[Dict[str, str]]:
    """
    Very basic heuristics. Expand with known-bad lists or allow/deny lists.
    """
    suspicious = []
    # Example patterns – replace / expand with real intelligence
    bad_keywords = [
        "spy", "track", "monitor", "keylog", "hidden", "stealth",
        "mspy", "flexispy", "hoverwatch", "cerberus"
    ]
    for app in apps:
        ident = (app.get("identifier") or "").lower()
        name = (app.get("name") or "").lower()
        for kw in bad_keywords:
            if kw in ident or kw in name:
                app_copy = dict(app)
                app_copy["reason"] = f"Keyword match: {kw}"
                suspicious.append(app_copy)
                break
    return suspicious
