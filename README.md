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

Ghostprint runs completely on your own computer. It never sends your data anywhere. Everything stays private and under your control.

---

## What does Ghostprint actually do?

Imagine you suspect someone has been secretly watching your iPhone — reading your messages, listening through the microphone, tracking your location, or installing hidden software. Ghostprint helps you look for the digital “fingerprints” that kind of spyware often leaves behind.

It does four main things:

1. **Talks to your iPhone over a USB cable**  
   Just like plugging your phone into a computer to back it up.

2. **Takes a careful copy (backup) of the phone’s data**  
   This is similar to the backup iTunes or Finder makes, but Ghostprint then examines it.

3. **Looks for known spyware signatures**  
   It uses a free, respected security tool originally created by Amnesty International (called MVT) that knows the digital fingerprints of sophisticated spyware such as Pegasus and similar programs.

4. **Checks for suspicious settings and apps**  
   It looks for unknown “configuration profiles” (special settings that can give someone remote control) and apps that might be used for spying.

At the end it writes a clear report you can read.

---

## Who is Ghostprint for?

- People who are worried their phone may have been compromised
- Journalists, activists, or anyone in a high-risk situation
- Anyone who wants a private way to check their own device without using commercial “phone cleaner” apps
- Technical users who want a starting point for deeper investigation

**Important:** This is not a magic “virus scanner” that finds every possible problem. It is a serious forensic-style check focused on known spyware and suspicious configurations.

---

## What Ghostprint can and cannot do

### It can help detect:
- Known commercial spyware (including some variants of Pegasus and related tools)
- Unknown or unexpected configuration profiles that can control the phone
- Apps that look suspicious based on their names
- Basic signs that something unusual has been installed

### It cannot:
- Guarantee the phone is 100% clean (brand-new spyware with no public fingerprints is hard to find)
- Watch the phone while you are using it in real time
- Fix the problem automatically — it only investigates and reports
- Work well if the phone is locked and you refuse to unlock it or trust the computer

If Ghostprint finds something serious, the safest advice is usually to erase the phone and set it up as new (without restoring from an old backup).

---

## Before you start – important safety notes

1. **Only check phones you own or have clear permission to examine.** Using this tool on someone else’s phone without permission is illegal in most places.

2. **Use a clean computer if possible.** Ideally run Ghostprint on a Linux computer that you do not use for banking, email, or other sensitive work. A separate USB stick or a virtual machine is even better.

3. **Unlock your iPhone and tap “Trust”** when the phone asks whether you trust the computer. Ghostprint cannot work if the phone stays locked.

4. **The backup can take a long time** (sometimes 30–90 minutes depending on how much data is on the phone). Leave the phone connected and plugged into power.

5. **Keep your iPhone updated.** Many attacks are fixed by simply installing the latest iOS version.

---

## What you need

### Computer
- A Linux computer (Ubuntu, Debian, Fedora, etc. work well).  
  macOS can also work but Linux is preferred for privacy.

### Software that must be installed first
You will need a few free tools. Someone technical can help you install them, or you can follow the commands below carefully.

**On Ubuntu / Debian / similar:**

```bash
sudo apt update
sudo apt install -y libimobiledevice-utils usbmuxd python3-pip python3-venv git
```

**Then set up Ghostprint:**

```bash
git clone https://github.com/vectisops/ios-security-auditor.git
cd ios-security-auditor
git checkout feature/initial-auditor

python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pip install mvt
```

(The last command installs the Amnesty spyware detection engine.)

---

## How to run a full check (step by step)

1. Unlock your iPhone and connect it to the computer with a USB cable.
2. When the phone asks “Trust This Computer?”, tap **Trust** and enter your passcode.
3. On the computer, make sure you are inside the tool folder and the virtual environment is active (you should see `(.venv)` at the start of the command line).
4. Run the full scan:

```bash
python auditor.py scan --output reports/
```

5. Wait. Ghostprint will:
   - Show basic information about the phone
   - Create a backup (this is the longest step)
   - Scan the backup for known spyware fingerprints
   - Look for suspicious profiles and apps
   - Write a report into the `reports/` folder

When it finishes you will see two files, for example:
- `ios-audit-XXXXXXXX-20260724T123456Z.md` ← easy to read
- `ios-audit-XXXXXXXX-20260724T123456Z.json` ← machine-readable version

Open the `.md` file with any text editor or Markdown viewer.

---

## Other simple commands

| Command | What it does |
|---------|--------------|
| `python auditor.py info` | Quickly shows the phone’s name, iOS version, serial number, etc. |
| `python auditor.py apps` | Lists all installed apps and flags ones with suspicious names |
| `python auditor.py profiles` | Looks inside existing backups for configuration profiles |

---

## Understanding the report

The report is written in plain language as much as possible. Look especially for these sections:

- **MVT / Spyware IOC Results**  
  If it says “IOCs detected: YES”, treat this seriously. It means Ghostprint found digital fingerprints that match known spyware.

- **Configuration Profiles**  
  Any profile you do not recognise (especially ones with words like MDM, Management, Remote, or VPN) should be investigated. On the iPhone you can check them under  
  **Settings → General → VPN & Device Management**.

- **Suspicious Apps**  
  These are only rough warnings based on names. Many legitimate apps will not appear here.

- **Recommendations**  
  The tool always ends with practical next steps.

---

## What to do if something looks wrong

1. **Do not panic.** Many “suspicious” findings turn out to be nothing.
2. Take screenshots or save the report.
3. On the iPhone, go to **Settings → General → VPN & Device Management** and remove any profile you do not recognise.
4. Change your Apple ID password from a different, trusted computer or phone.
5. Review the list of devices signed into your Apple ID (Settings → [Your Name]).
6. Consider erasing the iPhone completely and setting it up as a new phone (do **not** restore from a backup if you suspect the backup itself is infected).
7. If you are a journalist, activist, or high-risk person, contact a digital security specialist or an organisation that helps with spyware cases.

---

## Privacy & isolation tips (recommended)

- Run Ghostprint under a normal user account, not as the all-powerful “root” user.
- Even better: run it inside a disposable virtual machine or a container so nothing can spread.
- After you finish, you can delete the backup folder to free space and remove sensitive data from the computer.
- Ghostprint itself never phones home and does not need an internet connection once the software is installed.

---

## Limitations (please read)

- Ghostprint works best on phones that are **not jailbroken**.
- Brand-new spyware that has never been publicly analysed may not be detected.
- Some newer iPhones or very new iOS versions may need a more recent version of the underlying communication library.
- Creating a full backup can take a lot of disk space (often several gigabytes).

---

## Legal note

This software is provided for **consensual** security checking only. You must own the device or have explicit permission from the owner. Using it to examine someone else’s phone without authorisation may be a criminal offence.

---

## Credits & thanks

- **libimobiledevice** – the free software that lets Linux computers talk to iPhones
- **Amnesty International’s Mobile Verification Toolkit (MVT)** – the spyware detection engine
- Built as a private, offline tool so ordinary people can check their own devices without relying on commercial cloud services

---

## Licence

MIT Licence – free to use, modify, and share, with very few restrictions.

---

If you get stuck, the best first step is usually to make sure the iPhone is unlocked, trusted the computer, and that the basic command `idevice_id -l` shows your phone’s identifier. After that, the rest of the process is mostly automatic.
