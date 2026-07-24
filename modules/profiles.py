"""Configuration profile and MDM analysis helpers.

Note: Full profile extraction from a non-jailbroken device usually requires
parsing the backup. This module provides a starting point and placeholders
for deeper analysis once a backup is available.
"""

import plistlib
from pathlib import Path
from typing import List, Dict, Any, Optional


def find_profiles_in_backup(backup_path: Path) -> List[Dict[str, Any]]:
    """
    Attempt to locate configuration profiles inside an iOS backup.

    Profiles are often stored under certain domain paths. This is a best-effort
    heuristic and may need expansion for newer iOS versions.
    """
    profiles = []
    backup_path = Path(backup_path)

    # Common locations / patterns (simplified)
    # In practice you walk the Manifest.db or known domains.
    # For a first version we look for .mobileconfig / .plist that look like profiles.
    for p in backup_path.rglob("*.mobileconfig"):
        try:
            with open(p, "rb") as f:
                data = plistlib.load(f)
            profiles.append(
                {
                    "path": str(p.relative_to(backup_path)),
                    "payload_display_name": data.get("PayloadDisplayName"),
                    "payload_identifier": data.get("PayloadIdentifier"),
                    "payload_type": data.get("PayloadType"),
                    "payload_organization": data.get("PayloadOrganization"),
                    "raw_keys": list(data.keys()),
                }
            )
        except Exception:
            continue

    # Also scan for common profile-related plists
    for p in backup_path.rglob("*.plist"):
        name = p.name.lower()
        if "profile" in name or "configuration" in name or "mdm" in name:
            try:
                with open(p, "rb") as f:
                    data = plistlib.load(f)
                profiles.append(
                    {
                        "path": str(p.relative_to(backup_path)),
                        "note": "Possible profile-related plist",
                        "keys": list(data.keys()) if isinstance(data, dict) else [],
                    }
                )
            except Exception:
                continue

    return profiles


def assess_profile_risk(profile: Dict[str, Any]) -> str:
    """Simple heuristic risk rating."""
    name = (profile.get("payload_display_name") or "").lower()
    org = (profile.get("payload_organization") or "").lower()
    ident = (profile.get("payload_identifier") or "").lower()

    suspicious_keywords = [
        "mdm", "management", "remote", "spy", "monitor", "tracking",
        "enterprise", "vpn", "proxy", "certificate", "scep"
    ]

    score = 0
    for kw in suspicious_keywords:
        if kw in name or kw in org or kw in ident:
            score += 1

    if score >= 3:
        return "HIGH"
    if score >= 1:
        return "MEDIUM"
    return "LOW"
