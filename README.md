```
   ██████╗ ██╗  ██╗ ██████╗ ███████╗████████╗
  ██╔════╝ ██║  ██║██╔═══██╗██╔════╝╚══██╔══╝
  ██║  ███╗███████║██║   ██║███████╗   ██║   
  ██║   ██║██╔══██║██║   ██║╚════██║   ██║   
  ╚██████╔╝██║  ██║╚██████╔╝███████║   ██║   
   ╚═════╝ ╚═╝  ╚═╝ ╚═════╝ ╚══════╝   ╚═╝   
  ██████╗ ██████╗ ██╗███╗   ██╗████████╗
  ██╔══██╗██╔══██╗██║████╗  ██║╚══██╔══╝
  ██████╔╝██████╔╝██║██╔██╗ ██║   ██║   
  ██╔═══╝ ██╔══██╗██║██║╚██╗██║   ██║   
  ██║     ██║  ██║██║██║ ╚████║   ██║   
  ╚═╝     ╚═╝  ╚═╝╚═╝╚═╝  ╚═══╝   ╚═╝   
```

**Check if your iPhone has been hacked or is being secretly tracked — private, offline, and simple.**

**Ghostprint** runs completely on **your own computer**. It never uploads your phone data to a company cloud. Everything stays under your control.

- **Portfolio (plain guide):** [vectisops.github.io/projects/ghostprint.html](https://vectisops.github.io/projects/ghostprint.html)  
- **Technical deep dive:** [vectisops.github.io/projects/ghostprint-technical.html](https://vectisops.github.io/projects/ghostprint-technical.html)  
- **Home:** [vectisops.github.io](https://vectisops.github.io/)

GitHub repo name: `ios-security-auditor` · Product name: **Ghostprint**

---

## What is this, in everyday language?

Most “phone security” apps either want an account, send data to the internet, or only look for ordinary viruses. Serious spyware is different — it can leave quiet digital fingerprints that ordinary antivirus never sees.

Ghostprint is a **private checking tool**. You plug your iPhone into a computer with a USB cable. Ghostprint makes a careful backup copy, then searches that copy for known spyware fingerprints, odd remote-control settings, and suspicious apps. At the end you get a report written so a non-technical person can understand the important parts.

---

## Main features

| Feature | What it means for you |
|--------|------------------------|
| **USB connection** | Works like a normal computer backup — unlock phone, tap Trust |
| **Full backup scan** | Examines a copy of the phone’s data, not the live phone while you use it |
| **Spyware fingerprint search** | Uses Amnesty International’s free MVT engine, which knows many commercial spyware families |
| **Settings / profile check** | Looks for unknown “management” profiles that can give someone remote control |
| **App name heuristics** | Flags apps whose names look like tracking or spy tools |
| **Plain report** | Markdown report you can open in any text editor, plus a JSON file for technical use |
| **Offline after install** | No phone-home; no required cloud account |
| **Isolation-friendly** | Designed to run on a dedicated Linux machine, VM, or clean user account |

---

## Who it is for / typical uses

- **Anyone worried their iPhone may have been compromised** after a suspicious event, shared device, or strange behaviour
- **Journalists, activists, and higher-risk users** who need a private check without commercial cloud tools
- **People who refuse “phone cleaner” apps** that demand accounts and internet access
- **Technical helpers** assisting a friend or family member (with permission) who want a structured starting point

**It is not** a magic guarantee the phone is perfectly clean, a real-time monitor, or an automatic “fix” button.

---

## What it can and cannot do

**Can help find**
- Known commercial spyware families (including some linked to high-end tools such as Pegasus)
- Unexpected remote-management / configuration profiles
- Roughly suspicious app names

**Cannot**
- Guarantee 100% cleanliness (brand-new spyware with no public fingerprints is hard to catch)
- Watch the phone live while you use it
- Automatically remove infection
- Work if the phone stays locked and never trusts the computer

If something serious appears, the usual safest path is: save the report → remove unknown profiles → change Apple ID password from another device → consider erase and set up as **new** (do not restore from a suspect backup).

---

## Safety notes (please read)

1. Only check phones you **own** or have **clear permission** to examine.  
2. Prefer a **clean computer** you do not use for banking or everyday email.  
3. **Unlock** the phone and tap **Trust**.  
4. Backups can take **30–90+ minutes** — leave the phone charged and connected.  
5. Keep **iOS updated**; many attacks are fixed by updates alone.

---

## Quick setup (Ubuntu / Debian-style Linux)

```bash
sudo apt update
sudo apt install -y libimobiledevice-utils usbmuxd python3-pip python3-venv git

git clone https://github.com/vectisops/ios-security-auditor.git
cd ios-security-auditor

python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pip install mvt
```

**Run a full check**

```bash
python auditor.py scan --output reports/
```

**Other commands**

| Command | What it does |
|---------|--------------|
| `python auditor.py info` | Phone name, iOS version, serial, etc. |
| `python auditor.py apps` | List apps; flag suspicious names |
| `python auditor.py profiles` | Search existing backups for profiles |

---

## Understanding the report

- **MVT / Spyware IOC Results** — “IOCs detected: YES” means known spyware fingerprints were found. Treat seriously.  
- **Configuration Profiles** — anything you do not recognise (MDM, Management, Remote, VPN) deserves a look under **Settings → General → VPN & Device Management**.  
- **Suspicious Apps** — name-based warnings only; not proof of guilt.  
- **Recommendations** — practical next steps at the end of every report.

---

## Future plans

These are directions, not promises with dates:

- Clearer “traffic light” summary at the top of every report (green / amber / red in plain language)
- Better handling of **encrypted** backups with guided password steps
- Optional one-command install scripts for common Linux distros
- Container / Podman recipes so the whole tool runs in an isolated box by default
- Expanded profile detection for newer iOS backup layouts
- Small companion notes for high-risk users (what to do after a bad finding)
- Keep everything offline-first — no cloud dependency will be added as a requirement

---

## Privacy & legal

Ghostprint does not phone home. After dependencies are installed, it can run offline.  
**Consensual use only** — you must own the device or have explicit permission. Unauthorised examination of someone else’s phone may be a criminal offence.

---

## Credits

- **libimobiledevice** — lets Linux talk to iPhones  
- **Amnesty International’s Mobile Verification Toolkit (MVT)** — spyware detection engine  
- Built so ordinary people can check their own devices without commercial cloud services

## Licence

MIT — free to use, modify, and share.

---

**More from Vectis Ops:** [vectisops.github.io](https://vectisops.github.io/) · [GitHub @vectisops](https://github.com/vectisops)
