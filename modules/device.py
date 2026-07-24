"""Device communication helpers using libimobiledevice tools."""

import json
import subprocess
import shutil
from typing import Dict, Optional, List
from pathlib import Path


class DeviceError(Exception):
    pass


def _run(cmd: List[str], timeout: int = 60) -> str:
    """Run a command and return stdout. Raise DeviceError on failure."""
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )
        if result.returncode != 0:
            raise DeviceError(
                f"Command failed ({result.returncode}): {' '.join(cmd)}\n{result.stderr}"
            )
        return result.stdout.strip()
    except FileNotFoundError:
        raise DeviceError(
            f"Required tool not found: {cmd[0]}. "
            "Install libimobiledevice-utils (and usbmuxd)."
        )
    except subprocess.TimeoutExpired:
        raise DeviceError(f"Command timed out: {' '.join(cmd)}")


def check_tools() -> Dict[str, bool]:
    """Verify that required CLI tools are available."""
    tools = ["idevice_id", "ideviceinfo", "idevicebackup2", "ideviceinstaller"]
    return {t: shutil.which(t) is not None for t in tools}


def list_devices() -> List[str]:
    """Return list of connected UDIDs."""
    out = _run(["idevice_id", "-l"])
    if not out:
        return []
    return [line.strip() for line in out.splitlines() if line.strip()]


def get_device_info(udid: Optional[str] = None) -> Dict[str, str]:
    """Return key device information as a dictionary."""
    cmd = ["ideviceinfo"]
    if udid:
        cmd.extend(["-u", udid])
    raw = _run(cmd)
    info = {}
    for line in raw.splitlines():
        if ": " in line:
            key, value = line.split(": ", 1)
            info[key.strip()] = value.strip()
    return info


def get_basic_summary(udid: Optional[str] = None) -> Dict[str, str]:
    """Return a focused subset of useful fields."""
    info = get_device_info(udid)
    keys = [
        "DeviceName",
        "ProductType",
        "ProductVersion",
        "BuildVersion",
        "SerialNumber",
        "UniqueDeviceID",
        "HardwareModel",
        "DeviceClass",
        "CPUArchitecture",
        "WiFiAddress",
        "BluetoothAddress",
        "TimeZone",
    ]
    return {k: info.get(k, "N/A") for k in keys}


def is_trusted(udid: Optional[str] = None) -> bool:
    """Simple check whether we can talk to the device (implies trust)."""
    try:
        get_device_info(udid)
        return True
    except DeviceError:
        return False
