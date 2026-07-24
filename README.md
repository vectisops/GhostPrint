# iOS Security Auditor

**Independent, offline iOS security auditing tool** designed for Linux (primary) or macOS.

Scans connected iPhones over USB for signs of compromise, spyware Indicators of Compromise (IOCs), unknown configuration profiles, suspicious apps, and basic vulnerability indicators. Built for isolated, sovereign operation — no cloud dependencies.

## Features

- USB device detection and trust handling via `libimobiledevice`
- Full / partial encrypted or unencrypted backups
- Amnesty International **Mobile Verification Toolkit (MVT)** integration for Pegasus-family and related spyware IOC scanning
- Configuration / MDM / VPN profile enumeration and risk flagging
- Installed apps listing with basic heuristics
- Structured Markdown + JSON reports
- Completely offline-capable once dependencies and IOC feeds are cached

## Requirements

### System packages (Linux)

```bash
sudo apt update
sudo apt install -y libimobiledevice-utils usbmuxd libimobiledevice-dev python3-pip python3-venv git
```

On some distributions you may need to compile a recent `libimobiledevice` from source for the newest iOS versions.

### Python

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### MVT

```bash
pip install mvt
# or from source for latest IOCs
```

## Quick Start

1. Connect the iPhone via USB and unlock it. Trust the computer when prompted.
2. Activate the virtual environment.
3. Run:

```bash
python auditor.py scan --output reports/
```

Common options:

```bash
python auditor.py scan --backup-dir /path/to/backups --encrypted --password "your-backup-password"
python auditor.py info          # quick device info only
python auditor.py profiles      # list configuration profiles
python auditor.py apps          # list installed apps
```

## Architecture

```
ios-security-auditor/
├── auditor.py              # CLI entry point
├── modules/
│   ├── device.py           # libimobiledevice wrappers + device info
│   ├── backup.py           # Backup creation & management
│   ├── mvt_runner.py       # MVT execution + result parsing
│   ├── profiles.py         # Configuration / MDM profile analysis
│   ├── apps.py             # App listing & heuristics
│   └── report.py           # Report generation
├── requirements.txt
└── README.md
```

## Isolation Recommendations

- Run under a dedicated non-root Linux user.
- Prefer Podman/Docker with USB device passthrough for stronger isolation.
- Or use a disposable Qubes VM / dedicated macOS VM.
- Never run this tool on a machine that also handles highly sensitive unrelated work if you are analysing a potentially compromised device.

## Limitations

- Non-jailbroken devices only (by design for safety and broad compatibility).
- Detection of novel / unknown spyware without public IOCs is limited.
- Live process / memory analysis is not performed.
- Some modern iOS versions may require the latest `libimobiledevice`.

## Legal & Ethical

This tool is intended **only** for consensual analysis of devices you own or have explicit permission to examine. Do not use it against devices without authorisation.

## Credits

- [libimobiledevice](https://libimobiledevice.org/)
- [Amnesty International Mobile Verification Toolkit (MVT)](https://github.com/mvt-project/mvt)
- Built as an independent offline tool for sovereign security work.

## Licence

MIT
