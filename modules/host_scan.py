"""Read-only, limited Windows host inventory; this is not an antivirus scan."""

import os
import shutil
import subprocess
from typing import Any, Dict, List


def scan_windows_host() -> Dict[str, Any]:
    """Inventory common startup entries and Microsoft Defender status on Windows."""
    if os.name != "nt":
        raise RuntimeError("The optional host inventory is available only on Windows.")

    import winreg

    startup_entries: List[Dict[str, str]] = []
    locations = (
        (winreg.HKEY_CURRENT_USER, "HKCU", r"Software\Microsoft\Windows\CurrentVersion\Run"),
        (winreg.HKEY_LOCAL_MACHINE, "HKLM", r"Software\Microsoft\Windows\CurrentVersion\Run"),
        (winreg.HKEY_CURRENT_USER, "HKCU", r"Software\Microsoft\Windows\CurrentVersion\RunOnce"),
        (winreg.HKEY_LOCAL_MACHINE, "HKLM", r"Software\Microsoft\Windows\CurrentVersion\RunOnce"),
    )
    for hive, hive_name, key_path in locations:
        try:
            with winreg.OpenKey(hive, key_path) as key:
                index = 0
                while True:
                    try:
                        name, command, _kind = winreg.EnumValue(key, index)
                    except OSError:
                        break
                    startup_entries.append({
                        "location": f"{hive_name}\\{key_path}",
                        "name": str(name),
                        "command": str(command),
                    })
                    index += 1
        except OSError:
            continue

    powershell = shutil.which("powershell.exe") or shutil.which("powershell")
    defender_status = "Not available"
    if powershell:
        command = (
            "(Get-MpComputerStatus | Select-Object -ExpandProperty "
            "RealTimeProtectionEnabled) -join ''"
        )
        try:
            result = subprocess.run(
                [powershell, "-NoProfile", "-NonInteractive", "-Command", command],
                capture_output=True,
                text=True,
                timeout=20,
                check=False,
            )
            if result.returncode == 0 and result.stdout.strip().lower() in ("true", "false"):
                defender_status = result.stdout.strip()
            elif result.returncode != 0:
                defender_status = "Unavailable or access denied"
        except (OSError, subprocess.TimeoutExpired):
            defender_status = "Unavailable"

    return {
        "scope": "Read-only startup-entry inventory; no malware verdict.",
        "defender_realtime_protection": defender_status,
        "startup_entries": startup_entries,
    }
