# GhostPrint for Windows

This is the supported first desktop distribution. The download ZIP contains the GhostPrint installer and a plain-language first-scan guide. The installer bundles the GUI and MVT scanner; users do not need Python or terminal commands.

## Get the app

For end users, download **GhostPrint-Windows-Download.zip** from a GitHub Release, or receive the ZIP directly from a trusted sender. Extract it, run `GhostPrint-Setup.exe`, and follow [`INSTALLATION.txt`](INSTALLATION.txt). Pull requests and manual workflow runs also publish the ZIP as an Actions artifact for review. A GitHub source-code ZIP always contains the entire repository; the platform folders are not independently downloadable source archives.

## Scan an iPhone or iPad backup

1. Install and launch GhostPrint.
2. Use Apple Devices or iTunes to create a local backup, unlock and trust the device when prompted, then wait for the backup to finish. The current GUI does not collect an encrypted-backup password; choose a backup MVT can open without one.
3. In GhostPrint, select the backup folder and scan.

Backup creation is guided through Apple's desktop software; this project does not automate undocumented Apple backup operations. The source backup is copied to temporary working storage for scanning and is not modified. See the repository README for cleanup and indicator limitations.

## Build from a checkout

On a Windows machine with Python 3.11, run `python -m pip install -r requirements.txt pyinstaller`, then run `.\platforms\windows\build.ps1` in PowerShell. Compile `platforms\windows\GhostPrint.iss` with Inno Setup 6, then run `.\platforms\windows\package.ps1` to create `dist\GhostPrint-Windows-Download.zip`. The GitHub Actions workflow runs these steps and publishes the ZIP as a build artifact; version-tag releases include both the installer and ZIP.

The optional **Check this PC** action inventories Defender real-time protection and common startup registry entries. It is not a malware verdict.
