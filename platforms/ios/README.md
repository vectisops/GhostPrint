# iOS and iPadOS device support

This folder documents GhostPrint's **scan target**, not a native application that runs on an iPhone or iPad. GhostPrint is a desktop program: it analyzes a backup made on a supported host computer.

## Current workflow

- On Windows, create the backup with Apple Devices or iTunes, then select its folder in the GhostPrint Windows app.
- GhostPrint copies the backup into private temporary working storage, runs MVT and configured STIX2 indicators, and removes its working copy on normal app exit or when the user requests a purge.
- Backup creation is currently guided/manual. GhostPrint does not create, restore, or modify an Apple backup itself.
- The current GUI does not collect a password for encrypted backups; use a backup MVT can open without one, or use the legacy CLI for password-protected backups.

There is no iOS/iPadOS installer or native iPhone/iPad executable in this repository. Device-side live scanning and direct USB acquisition are not claimed.
