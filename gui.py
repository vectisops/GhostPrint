"""Windows-friendly, local-only GhostPrint desktop interface."""

import json
import os
import queue
import threading
import tkinter as tk
from datetime import datetime, timezone
from pathlib import Path
from tkinter import filedialog, messagebox, simpledialog, ttk
from typing import Any, Dict, Optional, Tuple

from modules.device import DeviceError
from modules.host_scan import scan_windows_host
from modules.indicators import (
    cache_directory,
    mvt_executable,
    refresh_indicator_sets,
    register_indicator_source,
)
from modules.mvt_runner import ScanCancelled, run_mvt
from modules.secure_workspace import (
    PrivateWorkspace,
    WorkspaceError,
    cleanup_stale_workspaces,
)


class GhostPrintApp:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("GhostPrint — Local Device Check")
        self.root.geometry("790x660")
        self.root.minsize(660, 540)
        self.root.configure(bg="#0b1020")

        self.events: "queue.Queue[Tuple[str, Any]]" = queue.Queue()
        self.selected_backup: Optional[Path] = None
        self.workspaces = []
        self.indicator_results: Dict[str, Dict[str, Any]] = {}
        self.indicator_ready = False
        self.mvt_command = mvt_executable()
        self.last_summary = ""
        self.cancel_event: Optional[threading.Event] = None
        self.scan_thread: Optional[threading.Thread] = None
        self.close_pending = False
        self._closing = False

        style = ttk.Style()
        style.theme_use("clam")
        style.configure("TFrame", background="#0b1020")
        style.configure("Card.TFrame", background="#121a2b")
        style.configure("TLabel", background="#0b1020", foreground="#e6edf7")
        style.configure("Title.TLabel", background="#0b1020", font=("Segoe UI", 23, "bold"), foreground="#e6fbff")
        style.configure("Subtitle.TLabel", background="#0b1020", font=("Segoe UI", 10), foreground="#b7c4d6")
        style.configure("Section.TLabel", background="#0b1020", font=("Segoe UI", 12, "bold"), foreground="#53e0e8")
        style.configure("Primary.TButton", font=("Segoe UI", 10, "bold"), padding=(12, 9), background="#00aeb9", foreground="#06141b")
        style.map("Primary.TButton", background=[("active", "#53e0e8"), ("disabled", "#354658")])
        style.configure("TButton", font=("Segoe UI", 10), padding=(10, 7), background="#1c2a3d", foreground="#e6edf7")
        style.map("TButton", background=[("active", "#2c405b"), ("disabled", "#192333")])

        self._build_ui()
        self.root.protocol("WM_DELETE_WINDOW", self._close)
        if not self.mvt_command:
            self._append(
                "Scanner unavailable: MVT was not found. The Windows installer bundles "
                "the scanner; a source checkout requires MVT to be installed separately."
            )
        try:
            cleanup = cleanup_stale_workspaces()
            if cleanup["removed"]:
                self.status_var.set("Removed a previous session's temporary files.")
            if cleanup["errors"]:
                self._append(
                    "Some previous temporary files could not be removed:\n"
                    + "\n".join(cleanup["errors"])
                )
        except WorkspaceError as error:
            self.status_var.set("Temporary storage could not be prepared.")
            self._append(str(error))

        self.root.after(150, self._poll_events)
        self._refresh_indicators()

    def _build_ui(self) -> None:
        outer = ttk.Frame(self.root, padding=(28, 22))
        outer.pack(fill="both", expand=True)
        ttk.Label(outer, text="GhostPrint", style="Title.TLabel").pack(anchor="w")
        ttk.Label(
            outer,
            text="A local, guided review of an iPhone or iPad backup.",
            style="Subtitle.TLabel",
        ).pack(anchor="w", pady=(2, 18))

        privacy = tk.Label(
            outer,
            text=(
                "Your original backup is not changed. GhostPrint copies it to a private "
                "temporary working folder and removes that copy when this window closes. "
                "If cleanup is interrupted, the next launch tries again. This is not "
                "guaranteed secure erasure: Windows, SSD wear-leveling, backups, or other "
                "storage software may retain data."
            ),
            justify="left",
            wraplength=710,
            bg="#14283b",
            fg="#d4eaff",
            padx=14,
            pady=12,
            font=("Segoe UI", 9),
        )
        privacy.pack(fill="x", pady=(0, 18))

        ttk.Label(outer, text="1. Create or choose a backup", style="Section.TLabel").pack(
            anchor="w"
        )
        ttk.Label(
            outer,
            text=(
                "Use Apple Devices or iTunes on this PC to create a local backup. "
                "An encrypted backup contains more data; keep its password available. "
                "Then select the backup folder below."
            ),
            wraplength=710,
            style="Subtitle.TLabel",
        ).pack(anchor="w", pady=(5, 10))
        backup_row = ttk.Frame(outer)
        backup_row.pack(fill="x")
        self.choose_button = ttk.Button(
            backup_row, text="Choose backup folder…", command=self._choose_backup
        )
        self.choose_button.pack(side="left")
        ttk.Button(backup_row, text="Backup instructions", command=self._show_instructions).pack(
            side="left", padx=(8, 0)
        )
        self.backup_var = tk.StringVar(value="No backup selected")
        ttk.Label(
            outer, textvariable=self.backup_var, wraplength=710, style="Subtitle.TLabel"
        ).pack(anchor="w", pady=(8, 18))

        ttk.Label(outer, text="2. Refresh indicators and scan", style="Section.TLabel").pack(
            anchor="w"
        )
        ttk.Label(
            outer,
            text=(
                "The scan uses Amnesty/MVT indicators plus any trusted HTTPS STIX2 feeds "
                "you add. Additional feeds refresh at launch; their quality and scope vary. "
                "These checks do not cover every threat."
            ),
            wraplength=710,
            style="Subtitle.TLabel",
        ).pack(anchor="w", pady=(5, 10))
        action_row = ttk.Frame(outer)
        action_row.pack(fill="x")
        self.refresh_button = ttk.Button(
            action_row, text="Refresh indicators", command=self._refresh_indicators
        )
        self.refresh_button.pack(side="left")
        self.add_feed_button = ttk.Button(
            action_row, text="Add HTTPS STIX feed…", command=self._add_indicator_feed
        )
        self.add_feed_button.pack(side="left", padx=(8, 0))
        self.scan_button = ttk.Button(
            action_row,
            text="Scan selected backup",
            style="Primary.TButton",
            command=self._scan_backup,
            state="disabled",
        )
        self.scan_button.pack(side="left", padx=(8, 0))
        self.cancel_button = ttk.Button(
            action_row, text="Cancel scan", command=self._cancel_scan, state="disabled"
        )
        self.cancel_button.pack(side="left", padx=(8, 0))
        self.host_button = None
        if os.name == "nt":
            self.host_button = ttk.Button(
                action_row, text="Check this PC", command=self._scan_host
            )

        privacy_row = ttk.Frame(outer)
        privacy_row.pack(fill="x", pady=(8, 0))
        self.purge_button = ttk.Button(
            privacy_row, text="Purge temporary data now", command=self._purge_now
        )
        self.purge_button.pack(side="left")
        self.save_button = ttk.Button(
            privacy_row, text="Save summary…", command=self._save_summary, state="disabled"
        )
        self.save_button.pack(side="left", padx=(8, 0))
        if self.host_button:
            self.host_button.pack(side="right")
        self.status_var = tk.StringVar(value="Refreshing public indicator sets…")
        ttk.Label(outer, textvariable=self.status_var, style="Subtitle.TLabel").pack(
            anchor="w", pady=(12, 6)
        )
        self.output = tk.Text(
            outer,
            height=8,
            wrap="word",
            bg="#101827",
            fg="#dce8f5",
            insertbackground="#53e0e8",
            relief="solid",
            borderwidth=1,
            padx=12,
            pady=10,
            font=("Segoe UI", 9),
            state="disabled",
        )
        self.output.pack(fill="both", expand=True)

    def _append(self, text: str) -> None:
        self.output.configure(state="normal")
        self.output.insert("end", text.rstrip() + "\n\n")
        self.output.see("end")
        self.output.configure(state="disabled")

    def _choose_backup(self) -> None:
        selected = filedialog.askdirectory(
            title="Select the iPhone or iPad backup folder",
            mustexist=True,
        )
        if selected:
            self.selected_backup = Path(selected)
            self.backup_var.set(str(self.selected_backup))
            self._update_scan_state()

    def _show_instructions(self) -> None:
        messagebox.showinfo(
            "Create a local Apple-device backup",
            "1. Connect the iPhone or iPad by USB, unlock it, and tap Trust if asked.\n"
            "2. Open Apple Devices (or iTunes) on this PC and select the device.\n"
            "3. Choose a backup to this computer. Enable encrypted backup if you need "
            "the additional protected data, and keep the password safe.\n"
            "4. Select Back Up Now, wait for it to finish, then choose its backup folder "
            "in GhostPrint.\n\n"
            "GhostPrint does not create backups through an unsupported Apple API. "
            "It scans a copy and never edits the original.",
            parent=self.root,
        )

    def _refresh_indicators(self) -> None:
        self.refresh_button.configure(state="disabled")
        self.add_feed_button.configure(state="disabled")
        self.scan_button.configure(state="disabled")
        self.status_var.set("Refreshing configured indicator sets…")

        def worker() -> None:
            try:
                result = refresh_indicator_sets(cache_directory())
                self.events.put(("indicators", result))
            except OSError as error:
                self.events.put(("indicator_error", str(error)))

        threading.Thread(target=worker, name="ghostprint-indicators", daemon=True).start()

    def _add_indicator_feed(self) -> None:
        url = simpledialog.askstring(
            "Add an indicator feed",
            "Enter a trusted HTTPS URL that serves a STIX2 bundle. "
            "The feed URL is saved locally and refreshed when GhostPrint launches. "
            "Backup contents are never sent to the feed provider.",
            parent=self.root,
        )
        if not url:
            return
        try:
            name = register_indicator_source(cache_directory(), url)
        except (OSError, ValueError) as error:
            messagebox.showerror("Could not add indicator feed", str(error), parent=self.root)
            return
        self._append(f"Added {name}. Refreshing configured indicator feeds.")
        self._refresh_indicators()

    def _update_scan_state(self) -> None:
        can_scan = (
            self.indicator_ready
            and self.selected_backup is not None
            and bool(self.mvt_command)
        )
        self.scan_button.configure(state="normal" if can_scan else "disabled")

    def _scan_backup(self) -> None:
        if self.selected_backup is None:
            return
        if not self.mvt_command:
            messagebox.showerror(
                "MVT is unavailable",
                "The MVT scanner is not installed. Use the GhostPrint Windows installer "
                "or install MVT before scanning.",
                parent=self.root,
            )
            return
        source = self.selected_backup
        try:
            workspace = PrivateWorkspace()
        except WorkspaceError as error:
            messagebox.showerror("Temporary storage unavailable", str(error), parent=self.root)
            return
        self.workspaces.append(workspace)
        self.cancel_event = threading.Event()
        self.scan_button.configure(state="disabled")
        self.choose_button.configure(state="disabled")
        self.refresh_button.configure(state="disabled")
        self.add_feed_button.configure(state="disabled")
        self.purge_button.configure(state="disabled")
        self.save_button.configure(state="disabled")
        self.cancel_button.configure(state="normal")
        self.status_var.set("Copying the selected backup to temporary storage…")

        def worker() -> None:
            try:
                def copy_progress(done: int, total: int) -> None:
                    interval = max(1, total // 100)
                    if done == total or done % interval == 0:
                        self.events.put(("copy_progress", (done, total)))

                copied = workspace.copy_backup(
                    source,
                    cancel_event=self.cancel_event,
                    progress_callback=copy_progress,
                )
                self.events.put(("progress", "Starting the Amnesty/MVT scan…"))
                scans = [
                    (
                        "Amnesty / MVT",
                        run_mvt(
                            copied,
                            workspace.path / "results-amnesty",
                            executable=self.mvt_command,
                            cancel_event=self.cancel_event,
                        )
                    )
                ]
                for source_name, feed in self.indicator_results.items():
                    feed_path = feed.get("path")
                    if not source_name.startswith("feed:") or not feed_path:
                        continue
                    if self.cancel_event.is_set():
                        raise ScanCancelled("Scan cancelled.")
                    self.events.put(("progress", f"Scanning with {source_name[5:]}…"))
                    scans.append(
                        (
                            source_name[5:],
                            run_mvt(
                                copied,
                                workspace.path / ("results-" + str(len(scans))),
                                iocs_path=Path(feed_path),
                                executable=self.mvt_command,
                                cancel_event=self.cancel_event,
                            ),
                        )
                    )
                self.events.put(("scan", {"scans": scans, "workspace": workspace}))
            except ScanCancelled:
                self.events.put(("scan_cancelled", workspace))
            except (DeviceError, OSError, ValueError, WorkspaceError) as error:
                if self.cancel_event.is_set():
                    self.events.put(("scan_cancelled", workspace))
                else:
                    self.events.put(("scan_error", {"error": str(error), "workspace": workspace}))

        self.scan_thread = threading.Thread(
            target=worker, name="ghostprint-backup-scan", daemon=True
        )
        self.scan_thread.start()

    def _cancel_scan(self) -> None:
        if self.cancel_event:
            self.cancel_event.set()
            self.cancel_button.configure(state="disabled")
            self.status_var.set("Cancelling scan and cleaning up temporary working data…")

    def _purge_now(self) -> None:
        if self.scan_thread and self.scan_thread.is_alive():
            return
        failures = []
        remaining = []
        for workspace in self.workspaces:
            try:
                workspace.cleanup()
            except WorkspaceError as error:
                failures.append(str(error))
                remaining.append(workspace)
        self.workspaces = remaining
        if failures:
            self.status_var.set("Some temporary data could not be removed.")
            self._append("Temporary cleanup incomplete:\n" + "\n".join(failures))
        else:
            self.status_var.set("Temporary backup and scan data removed.")
            self._append("Temporary backup and scan data were purged.")

    def _save_summary(self) -> None:
        if not self.last_summary:
            return
        destination = filedialog.asksaveasfilename(
            title="Save a privacy-conscious scan summary",
            defaultextension=".txt",
            filetypes=[("Text summary", "*.txt")],
            initialfile="ghostprint-scan-summary.txt",
        )
        if not destination:
            return
        try:
            Path(destination).write_text(self.last_summary, encoding="utf-8")
        except OSError as error:
            messagebox.showerror("Could not save summary", str(error), parent=self.root)
            return
        self.status_var.set("Aggregate summary saved; it contains no backup path or raw findings.")

    def _scan_host(self) -> None:
        if self.host_button:
            self.host_button.configure(state="disabled")

        def worker() -> None:
            try:
                result = scan_windows_host()
                self.events.put(("host", result))
            except (OSError, RuntimeError) as error:
                self.events.put(("host_error", str(error)))

        threading.Thread(target=worker, name="ghostprint-host-inventory", daemon=True).start()

    def _poll_events(self) -> None:
        if self._closing:
            return
        while True:
            try:
                event, payload = self.events.get_nowait()
            except queue.Empty:
                break
            if event == "indicators":
                self.indicator_results = payload
                self.indicator_ready = True
                self.refresh_button.configure(state="normal")
                self.add_feed_button.configure(state="normal")
                for source, result in payload.items():
                    freshness = "updated" if result["ok"] else "not updated"
                    if not result["ok"] and result.get("path"):
                        freshness += "; using the previously cached feed"
                    details = [result["message"]]
                    if result.get("indicator_count") is not None:
                        details.append(f"{result['indicator_count']} indicators")
                    if result.get("last_updated"):
                        details.append(f"last success: {result['last_updated']}")
                    self._append(f"{source.title()}: {freshness}. " + " ".join(details))
                    if result.get("source_url"):
                        self._append(f"Feed source: {result['source_url']}")
                if not any(key.startswith("feed:") for key in payload):
                    self._append(
                        "Additional feeds: none configured. Add trusted HTTPS STIX2 feeds "
                        "to broaden the indicator set; MVT's updater does not report its count."
                    )
                self.status_var.set("Indicator refresh finished.")
                self._update_scan_state()
            elif event == "indicator_error":
                self.indicator_ready = True
                self.refresh_button.configure(state="normal")
                self.add_feed_button.configure(state="normal")
                self.status_var.set("Indicator refresh failed.")
                self._append(str(payload))
                self._update_scan_state()
            elif event == "progress":
                self.status_var.set(payload)
            elif event == "copy_progress":
                done, total = payload
                self.status_var.set(f"Copying backup to temporary storage… {done} of {total} files")
            elif event == "scan":
                self.choose_button.configure(state="normal")
                self.refresh_button.configure(state="normal")
                self.add_feed_button.configure(state="normal")
                self.purge_button.configure(state="normal")
                self.cancel_button.configure(state="disabled")
                lines = []
                for source, result in payload["scans"]:
                    count = len(result.get("findings", []))
                    state = "completed" if result.get("success") else "reported an error"
                    lines.append(f"{source}: {state}; {count} potential match(es).")
                    for index, finding in enumerate(result.get("findings", [])[:10], start=1):
                        evidence = json.dumps(finding, ensure_ascii=True, default=str)
                        self._append(
                            f"{source} potential match {index} (evidence; review manually): "
                            f"{evidence[:700]}"
                        )
                    if not result.get("success"):
                        detail = (result.get("stderr") or result.get("stdout") or "").strip()
                        if detail:
                            self._append(f"{source} scanner detail: {detail[:1200]}")
                        if result.get("parse_errors"):
                            self._append(
                                f"{source} result parsing: "
                                + "; ".join(result["parse_errors"])[:1200]
                            )
                summary = "\n".join(lines)
                total_matches = sum(
                    len(result.get("findings", [])) for _source, result in payload["scans"]
                )
                self.last_summary = (
                    "GhostPrint iPhone/iPad backup scan summary\n"
                    f"Generated (UTC): {datetime.now(timezone.utc).isoformat()}\n\n"
                    + summary
                    + f"\n\nPotential matches across sources: {total_matches}\n"
                    "Interpretation: a match needs human review and is not proof of "
                    "infection. No matches do not prove a device is clean. GhostPrint "
                    "does not infer a confidence score not supplied by the scanner.\n\n"
                    "Limitations: analysis depends on the selected backup, MVT modules, "
                    "indicator freshness, and feed quality; new or unlisted threats may "
                    "not be detected. Do not remove a profile or alter a device based "
                    "only on this summary.\n\n"
                    "Privacy: the source backup was not modified. The working copy and "
                    "detailed scan output are temporary and are removed on app close "
                    "or with the Purge temporary data control. This is not guaranteed "
                    "secure erasure."
                )
                self._append(self.last_summary)
                self.save_button.configure(state="normal")
                self.status_var.set("Scan finished. Temporary working data remains until exit or purge.")
                self._update_scan_state()
            elif event == "scan_error":
                self.choose_button.configure(state="normal")
                self.refresh_button.configure(state="normal")
                self.add_feed_button.configure(state="normal")
                self.purge_button.configure(state="normal")
                self.cancel_button.configure(state="disabled")
                self.status_var.set("The scan could not be completed.")
                self._append(payload["error"])
                self._update_scan_state()
            elif event == "scan_cancelled":
                self.choose_button.configure(state="normal")
                self.refresh_button.configure(state="normal")
                self.add_feed_button.configure(state="normal")
                self.purge_button.configure(state="normal")
                self.cancel_button.configure(state="disabled")
                self.status_var.set("Scan cancelled. Temporary data can now be purged.")
                self._append("Scan cancelled. Temporary data was retained until exit or purge.")
                self._update_scan_state()
            elif event == "host":
                self._append(
                    "This PC (read-only inventory; not an antivirus verdict)\n"
                    f"Microsoft Defender real-time protection: "
                    f"{payload['defender_realtime_protection']}\n"
                    f"Startup entries found: {len(payload['startup_entries'])}"
                )
                for entry in payload["startup_entries"]:
                    self._append(
                        f"{entry['location']} — {entry['name']}: {entry['command']}"
                    )
                self.host_button.configure(state="normal")
            elif event == "host_error":
                self._append(str(payload))
                self.host_button.configure(state="normal")
        self.root.after(150, self._poll_events)

    def _close(self) -> None:
        if self.close_pending:
            return
        if self.scan_thread and self.scan_thread.is_alive():
            self.close_pending = True
            self._cancel_scan()
            self.status_var.set("Cancelling scan before closing and removing temporary data…")
            self.root.after(150, self._wait_for_scan_and_close)
            return
        self._finish_close()

    def _wait_for_scan_and_close(self) -> None:
        if self.scan_thread and self.scan_thread.is_alive():
            self.root.after(150, self._wait_for_scan_and_close)
            return
        self._finish_close()

    def _finish_close(self) -> None:
        failures = []
        for workspace in self.workspaces:
            try:
                workspace.cleanup()
            except WorkspaceError as error:
                failures.append(str(error))
        if failures:
            messagebox.showwarning(
                "Temporary cleanup incomplete",
                "GhostPrint could not remove all temporary backup data. "
                "It will retry on the next launch.\n\n" + "\n".join(failures),
                parent=self.root,
            )
        self._closing = True
        self.root.destroy()


def main() -> None:
    root = tk.Tk()
    GhostPrintApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
