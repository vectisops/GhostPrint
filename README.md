  ____ _               _   
 / ___| |__   ___  ___| |_ 
| |  _| '_ \ / _ \/ __| __|
| |_| | | | | (_) \__ \ |_ 
 \____|_| |_|\___/|___/\__|
 ____       _       _   
|  _ \ _ __(_)_ __ | |_ 
| |_) | '__| | '_ \| __|
|  __/| |  | | | | | |_ 
|_|   |_|  |_|_| |_|\__|


**Check iPhones, iPads, and Macs for spyware, tracking, or suspicious activity — private, offline, and GUI-first.**

**GhostPrint** runs on **your own computer** with a guided visual interface designed for non-technical users. It keeps inspection offline and isolated so your device data isn't sent to third-party cloud services.

- **Portfolio (plain guide):** [vectisops.github.io/projects/ghostprint.html](https://vectisops.github.io/projects/ghostprint.html)  
- **Technical deep dive:** [vectisops.github.io/projects/ghostprint-technical.html](https://vectisops.github.io/projects/ghostprint-technical.html)  
- **Home:** [vectisops.github.io](https://vectisops.github.io/)  
- **Repository:** [github.com/vectisops/GhostPrint](https://github.com/vectisops/GhostPrint)

---

## What Is GhostPrint, in Everyday Language?

Most "phone cleaner" or security apps demand accounts, send telemetry to external servers, or only look for basic viruses. Targeted spyware, stalkerware, and covert tracking often leave subtle traces that ordinary antivirus misses.

GhostPrint is a **guided local checking tool** with a visual desktop interface:
1. **Checks your host Mac first** before pulling data from another device, helping ensure your starting computer is in good shape.
2. **Inspects connected iPhones or iPads** (via USB backup/diagnostics) or **Macs** (MacBook / iMac) for spyware indicators, unauthorized remote-management profiles, trackers, and suspicious items.
3. **Runs analysis inside an isolated container** (`--network=none`, read-only root where supported) so untrusted files from a suspect device stay contained.
4. **Uses a local LLM (via Ollama)** to summarize findings in plain English—highlighting **first and foremost** whether tracking, spyware, or malware indicators were detected, alongside practical optimization and cleanup advice.

---

## Key Capabilities

| Area | What GhostPrint Does |
|------|---------------------|
| **Guided macOS GUI** | Step-by-step visual screens, one-click setup/scan controls, and plain-language status badges—no terminal expertise required for everyday use. |
| **Host Pre-Check Gate** | Optional/automatic startup check on the host Mac (SIP, Gatekeeper, profiles, startup items) before cloning or inspecting data from another device. |
| **Sandboxed Inspection** | Runs backup/log parsing inside a locked-down, network-isolated container environment so suspicious artifacts cannot freely execute on the host. |
| **iPhone & iPad Support** | Inspects iOS and iPadOS backups (including encrypted backup support) and diagnostic/log archives using Amnesty International's **Mobile Verification Toolkit (MVT)** plus profile/app/tracker checks. |
| **iMac & MacBook Support** | Checks macOS persistence (LaunchAgents/LaunchDaemons), MDM/configuration profiles, privacy permissions, code signing, and listening network endpoints. |
| **Expanded Threat & Tracker Checks** | Combines multi-source STIX2 spyware indicators with configuration-profile checks, suspicious app/bundle heuristics, tracker/telemetry domain checks, and anomaly flags. |
| **Local LLM Triage & Optimization** | Uses a local Ollama model to deliver a clear priority verdict on **tracking, spyware, or malware**, sanity-check potential false positives, and suggest safe system/privacy optimizations. |

---

## Priority Triage: Tracking, Spyware & Malware First

GhostPrint is designed so you don't have to wade through raw logs just to know what matters most:

- **Top Priority Verdict:** Clearly states whether **spyware, tracking, or malware indicators** were detected, how confident the check is, and what to look at first.
- **Confirmed Indicators vs. Anomalies:** Separates known indicator matches and risky remote-control/profile findings from general anomalies or tracker warnings that may simply need a closer look.
- **Optimization & Cleanup Advice:** Offers plain-English recommendations for decluttering startup items, reviewing background services or permissions, and keeping devices tidy.

---

## What GhostPrint Can and Cannot Do

**Can help with**
- Checking iPhones, iPads, and Macs for known spyware indicators (via MVT STIX2 feeds)
- Spotting unexpected MDM / configuration profiles, suspicious apps/identifiers, and tracker patterns
- Giving non-technical users a structured starting point, plain report, and local AI summary

**Cannot**
- Guarantee a device is 100% clean or catch brand-new zero-day spyware with no public indicators
- Monitor a live device continuously in real time
- Automatically remove deep compromises or bypass device passcodes/encryption

> **If something serious is flagged:** Preserve your report, avoid making hasty changes that destroy evidence, remove unauthorized profiles only after reviewing what they are, change passwords from a known-clean device, and consider a clean erase & setup as **new** (without restoring from a suspect backup) or seek specialist digital-security help.

---

## Safety & Consent Rules

1. **Only scan devices you own or have explicit, informed permission to examine.** Unauthorised access or inspection of another person's device may be unlawful.
2. **Unlock iPhones/iPads and tap "Trust"** when prompted on the device screen.
3. **Encrypted backups matter:** An encrypted backup on iOS/iPadOS includes sensitive forensic records that unencrypted backups omit—keep track of your backup password if using one.
4. **Allow time for full backups:** Large backups can take 30–90+ minutes depending on storage size and cable speed; keep devices powered and connected.
5. **Keep operating systems updated:** Regular iOS, iPadOS, and macOS updates patch known vulnerabilities.

---

## Getting Started (macOS GUI Workflow)

### 1. Clone & Set Up
```bash
git clone [https://github.com/vectisops/GhostPrint.git](https://github.com/vectisops/GhostPrint.git)
cd GhostPrint

Run the setup script or launch the GUI setup wizard to install system/Python dependencies (pywebview, mvt, libimobiledevice / pymobiledevice3 as configured for your setup) and download initial spyware indicator sets:
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

2. Launch the GUI
python gui/app.py

3. Typical Guided Flow in the App
 * Setup / Readiness Check: Confirms required tools, container runtime, indicator files, and optional local Ollama LLM availability.
 * Host Mac Pre-Check: Optionally scans the host Mac first so you know your starting machine is clean before pulling data from another device.
 * Select & Scan Target: Connect an iPhone/iPad via USB (and trust the computer) or scan a Mac / imported log bundle inside the isolated container.
 * Review Priority Report & Optimizations: Read the top-level tracking/spyware/malware assessment, inspect detailed findings, and export a summary report.
(Existing CLI workflows such as auditor.py can still be maintained alongside the GUI for scripted or headless use.)
Privacy & Offline Operation
GhostPrint is built to stay offline-first on your own hardware. Network access is only needed when initially installing dependencies, updating indicator feeds, or pulling a local LLM model—inspections themselves can run offline and inside a restricted container.
Credits & Licence
 * Amnesty International's Mobile Verification Toolkit (MVT) — mobile forensic analysis and indicator matching engine.
 * libimobiledevice / pymobiledevice3 & pywebview — device communication and lightweight desktop webview rendering.
 * Licence: MIT (subject to upstream tool licenses and consensual-use rules, including MVT's consensual-use terms).
Vectis Ops: vectisops.github.io · GitHub @vectisops

