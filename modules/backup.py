"""Backup creation and management via idevicebackup2."""

import subprocess
from pathlib import Path
from typing import Optional, List
from .device import DeviceError, _run


def create_backup(
    destination: Path,
    udid: Optional[str] = None,
    full: bool = True,
    password: Optional[str] = None,
) -> Path:
    """
    Create an iOS backup using idevicebackup2.

    Returns the path to the backup directory (UDID-named folder).
    """
    destination = Path(destination)
    destination.mkdir(parents=True, exist_ok=True)

    cmd: List[str] = ["idevicebackup2"]
    if udid:
        cmd.extend(["-u", udid])

    if password:
        # For encrypted backups the password is usually set interactively
        # or via environment in some versions. We pass it if supported.
        # Note: recent idevicebackup2 may require interactive entry.
        pass

    cmd.append("backup")
    if full:
        cmd.append("--full")
    cmd.append(str(destination))

    try:
        # Longer timeout for full backups
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=3600,  # up to 1 hour
            check=False,
        )
        if result.returncode != 0:
            raise DeviceError(
                f"Backup failed:\n{result.stderr}\n{result.stdout}"
            )
    except subprocess.TimeoutExpired:
        raise DeviceError("Backup timed out after 1 hour")

    # The backup is stored under destination/<UDID>/
    # Find the newest or only directory
    subdirs = [d for d in destination.iterdir() if d.is_dir()]
    if not subdirs:
        raise DeviceError("Backup completed but no backup folder found")
    # Prefer the one that looks like a UDID
    for d in subdirs:
        if len(d.name) == 40 and all(c in "0123456789abcdefABCDEF" for c in d.name):
            return d
    return subdirs[0]


def list_backups(backup_root: Path) -> List[Path]:
    """List existing backup directories."""
    backup_root = Path(backup_root)
    if not backup_root.exists():
        return []
    return [d for d in backup_root.iterdir() if d.is_dir()]
