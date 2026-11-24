# GhostPrint

GhostPrint is a local-first, guided desktop tool for reviewing iPhone and iPad backups with Amnesty International's Mobile Verification Toolkit (MVT). The current GUI targets Windows and uses a restrained cyberpunk-dark palette; the existing command-line auditor remains available for scripted use.

## Start here

- **Windows users:** Read the [Windows installation and first-scan guide](platforms/windows/INSTALLATION.txt). The shareable download ZIP contains the installer and guide; no Python or terminal is required.
- **iPhone/iPad support:** See [iOS and iPadOS backup scanning](platforms/ios/README.md). GhostPrint runs on a computer; it is not an iPhone/iPad app.
- **Linux:** Check [Linux package status](platforms/linux/README.md); a one-click desktop package is not yet available.
- **Contributors:** Shared code is in `gui.py` and `modules/`, tests are in `tests/`, and Windows packaging is under `platforms/windows/`.

## Windows GUI

The **Windows installer** GitHub Actions workflow builds `GhostPrint-Windows-Download.zip`, containing `GhostPrint-Setup.exe` and a plain-language first-scan guide. When a version is released, download this ZIP from the public GitHub Releases page or share it directly with a recipient. The installer includes the GUI and MVT scanner, so users do not need a GitHub account, Python, or terminal commands.

1. Connect the iPhone or iPad to the PC, unlock it, and trust the computer.
2. In Apple Devices or iTunes, make a local backup. The current GUI does not collect an encrypted-backup password; use a backup MVT can open without one, or use the legacy CLI workflow for password-protected backups.
3. In GhostPrint, choose the completed backup folder and scan it. GhostPrint does not create backups using an unsupported Apple API.

The app also supports an optional, read-only Windows host inventory: Microsoft Defender real-time-protection status and common `Run`/`RunOnce` registry entries. This is an inventory, **not an antivirus scan or malware verdict**.

## Platform folders and downloads

- [`platforms/windows`](platforms/windows) contains the supported Windows installer build and host workflow.
- [`platforms/ios`](platforms/ios) describes iPhone/iPad backup scanning as a **device target**; it is not a native iOS app.
- [`platforms/linux`](platforms/linux) records Linux package status; a first-class Linux desktop distribution is not yet available.

Shared Python source stays at the repository root to avoid divergent copies. The platform folders hold packaging and guidance. A GitHub source ZIP always contains the whole repository, not a single folder; use the Windows download ZIP when you only need the installer and guide.

## Backup and privacy handling

- The original Apple backup is never edited. GhostPrint rejects backup trees containing symbolic links or unsupported special files, then copies the selected backup into an app-managed temporary workspace before analysis.
- Temporary backup copies and detailed MVT output are removed when the app closes or when **Purge temporary data now** is used. If the app or system stops unexpectedly, a later launch attempts to remove abandoned GhostPrint workspaces.
- Temporary storage is not RAM-only. SSD wear-leveling, Windows, filesystem snapshots, backup software, or other system features may retain data; deletion is **not guaranteed secure erasure**.
- The optional saved summary contains source names and aggregate match counts, not the backup path or raw MVT findings. It is only written when the user explicitly saves it.
- The app refreshes MVT's Amnesty indicator data and any additional HTTPS STIX2 feeds configured by the user. Feed URLs and public indicators are stored locally; backup contents are not sent to feed providers. Only configure indicator sources you trust.
- An unavailable feed is shown as stale or not updated. GhostPrint can use a previously cached additional feed, but MVT does not report its indicator count through the updater.

## Indicator and scan limitations

GhostPrint runs MVT's normal backup scan and, separately, scans each configured STIX2 indicator feed. Additional feeds must be direct HTTPS URLs serving a STIX2 bundle with indicator objects; add them in the GUI. No default third-party feed is bundled. Feed coverage and quality vary, and generic feeds are not necessarily mobile-specific.

A match is a lead for human review, not confirmation of compromise. A scan with no matches does not prove a device is clean. Coverage is limited by the backup contents, supported MVT modules, the selected indicator feeds, and what is publicly known. GhostPrint does not infer a confidence score or remove profiles, apps, or other data.

## Windows Support & Verification

Windows 11 validation covered the GUI and bundled MVT executable; GUI and MVT smoke checks passed, along with 14 automated tests. A Windows run loaded 11,494 STIX2 indicators from a locally staged cache.

In a blind check of two anonymized backup copies, one produced 3 MVT alerts, each with a matched indicator, and the other produced 0 alerts. GhostPrint's results agreed with direct MVT output, and the counts remained the same after changing only the opaque parent-directory names. Internal backup structure was preserved for scanning. These results validate the tested scan path, not a false-positive rate or the ground-truth cleanliness of the zero-alert backup.

## Interpreting Scan Results

> **Important:** Zero alerts means only that this scan reported no matching known indicators in the artifacts MVT could inspect. It does **not** guarantee that a device is clean or free of spyware.

- **Known-indicator limits:** MVT checks known indicators using its supported modules. New, undocumented, or unmatched threats may not trigger alerts, and indicators may not cover every relevant artifact.
- **Backup scope:** An iOS backup does not contain the entire filesystem, volatile memory, or all system logs. GhostPrint currently scans iTunes backup folders; it does not ingest or analyze `sysdiagnose` archives. Those require separate tools and review.
- **Network and privacy:** MVT analyzes the selected local backup copy, but refreshing indicators invokes MVT's downloader and fetches any configured HTTPS STIX2 feeds, so GhostPrint is not offline-only by default. GhostPrint's feed requests retrieve indicator data and do not include backup contents or scan results; this repository has no backup/result upload workflow.

## Development

The GUI uses Python's built-in Tkinter. For a source checkout, install `requirements.txt` and run `python gui.py` from a Python environment with MVT installed. On a Windows runner, `platforms/windows/build.ps1` packages the GUI and MVT with PyInstaller; the workflow uses Inno Setup to create the installer and attaches it to `v*` GitHub Releases.

The legacy CLI is in `auditor.py`:

```text
python auditor.py --help
```

## Useful follow-on work

These are not current capabilities: Apple-supported in-app backup creation, richer per-finding severity/provenance and evidence views, additional curated mobile-focused indicator sources, and deeper Windows persistence coverage. The current workflow deliberately guides users through Apple Devices/iTunes instead of automating undocumented backup operations.

## Credits and safe use

- [Mobile Verification Toolkit](https://github.com/mvt-project/mvt) by Amnesty International and contributors.
- Use only on devices and backups you own or have explicit permission to examine.
- GhostPrint is provided as an investigative aid, not a guarantee of safety or a substitute for specialist advice.
