"""Wrapper around Amnesty MVT for iOS analysis."""

import json
import shutil
import subprocess
import threading
import time
from pathlib import Path
from typing import Optional, Dict, Any, List
from .device import DeviceError
from .indicators import mvt_executable


class ScanCancelled(Exception):
    """Raised when the user cancels an active MVT scan."""


def check_mvt(executable: Optional[str] = None) -> bool:
    return bool(executable or mvt_executable() or shutil.which("mvt-ios"))


def run_mvt(
    backup_path: Path,
    output_dir: Path,
    password: Optional[str] = None,
    iocs_path: Optional[Path] = None,
    executable: Optional[str] = None,
    cancel_event: Optional[threading.Event] = None,
) -> Dict[str, Any]:
    """
    Run mvt-ios against a backup and return parsed summary + raw results path.

    Returns a dict with keys:
      - success: bool
      - findings: list of detected indicators (if any)
      - output_dir: Path
      - stdout / stderr
    """
    command = executable or mvt_executable() or shutil.which("mvt-ios")
    if not command:
        raise DeviceError(
            "mvt-ios not found. Install with: pip install mvt"
        )

    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    cmd = [
        command,
        "check-backup",
        "--output",
        str(output_dir),
    ]

    if password:
        cmd.extend(["--password", password])

    if iocs_path:
        if not Path(iocs_path).is_file():
            raise DeviceError(f"Indicator file does not exist: {iocs_path}")
        cmd.extend(["--iocs", str(iocs_path)])

    cmd.append(str(backup_path))

    try:
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
    except OSError as error:
        raise DeviceError(f"Could not start MVT: {error}") from error

    start_time = time.monotonic()
    while True:
        if cancel_event and cancel_event.is_set():
            if process.poll() is None:
                process.terminate()
            try:
                process.communicate(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
                process.communicate()
            raise ScanCancelled("Scan cancelled.")
        if time.monotonic() - start_time > 1800:
            if process.poll() is None:
                process.kill()
            process.communicate()
            raise DeviceError("MVT scan timed out after 30 minutes.")
        try:
            stdout, stderr = process.communicate(timeout=1)
            break
        except subprocess.TimeoutExpired:
            continue

    alerts_path = output_dir / "alerts.json"
    detection_files = (
        [alerts_path]
        if alerts_path.is_file()
        else sorted(output_dir.glob("*_detected.json"))
    )
    findings: List[Dict[str, Any]] = []
    parse_errors: List[str] = []
    for json_file in detection_files:
        try:
            data = json.loads(json_file.read_text(encoding="utf-8"))
            if isinstance(data, list):
                findings.extend(data)
            elif isinstance(data, dict):
                findings.append(data)
            else:
                parse_errors.append(f"{json_file.name}: unexpected JSON result shape")
        except (OSError, ValueError) as error:
            parse_errors.append(f"{json_file.name}: {error}")

    return {
        "success": process.returncode == 0 and not parse_errors,
        "returncode": process.returncode,
        "findings": findings,
        "parse_errors": parse_errors,
        "output_dir": str(output_dir),
        "stdout": stdout,
        "stderr": stderr,
        "detected_iocs": any(finding.get("matched_indicator") for finding in findings),
    }
