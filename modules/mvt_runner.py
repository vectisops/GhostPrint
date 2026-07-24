"""Wrapper around Amnesty MVT for iOS analysis."""

import json
import subprocess
import shutil
from pathlib import Path
from typing import Optional, Dict, Any, List
from .device import DeviceError


def check_mvt() -> bool:
    return shutil.which("mvt-ios") is not None


def run_mvt(
    backup_path: Path,
    output_dir: Path,
    password: Optional[str] = None,
    iocs_path: Optional[Path] = None,
) -> Dict[str, Any]:
    """
    Run mvt-ios against a backup and return parsed summary + raw results path.

    Returns a dict with keys:
      - success: bool
      - findings: list of detected indicators (if any)
      - output_dir: Path
      - stdout / stderr
    """
    if not check_mvt():
        raise DeviceError(
            "mvt-ios not found. Install with: pip install mvt"
        )

    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    cmd = [
        "mvt-ios",
        "check-backup",
        "--output",
        str(output_dir),
    ]

    if password:
        cmd.extend(["--password", password])

    if iocs_path and Path(iocs_path).exists():
        cmd.extend(["--iocs", str(iocs_path)])

    cmd.append(str(backup_path))

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=1800,  # 30 min
            check=False,
        )
    except subprocess.TimeoutExpired:
        raise DeviceError("MVT scan timed out")

    findings: List[Dict[str, Any]] = []
    # MVT writes JSON results into the output directory
    for json_file in output_dir.glob("*.json"):
        try:
            data = json.loads(json_file.read_text())
            if isinstance(data, list):
                findings.extend(data)
            elif isinstance(data, dict):
                findings.append(data)
        except Exception:
            continue

    return {
        "success": result.returncode == 0,
        "returncode": result.returncode,
        "findings": findings,
        "output_dir": str(output_dir),
        "stdout": result.stdout,
        "stderr": result.stderr,
        "detected_iocs": len(findings) > 0,
    }
