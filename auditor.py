#!/usr/bin/env python3
"""
Ghostprint – independent offline USB iOS security auditor.

Usage examples:
  python auditor.py info
  python auditor.py scan --output ./reports
  python auditor.py apps
  python auditor.py profiles --backup-dir ./backups
"""

import sys
from pathlib import Path
from typing import Optional

import click
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

from modules.device import (
    check_tools,
    list_devices,
    get_basic_summary,
    DeviceError,
)
from modules.backup import create_backup
from modules.mvt_runner import run_mvt, check_mvt
from modules.profiles import find_profiles_in_backup, assess_profile_risk
from modules.apps import list_installed_apps, flag_suspicious_apps
from modules.report import generate_report

console = Console()


def ensure_device() -> Optional[str]:
    devices = list_devices()
    if not devices:
        console.print("[red]No iOS device detected. Connect via USB and unlock + trust.[/red]")
        sys.exit(1)
    if len(devices) > 1:
        console.print(f"[yellow]Multiple devices found: {devices}. Using first.[/yellow]")
    return devices[0]


@click.group()
def cli():
    """Ghostprint – independent iOS security auditing tool (USB + MVT)."""
    pass


@cli.command()
def info():
    """Show basic device information."""
    tools = check_tools()
    missing = [t for t, ok in tools.items() if not ok]
    if missing:
        console.print(f"[red]Missing tools: {', '.join(missing)}[/red]")
        console.print("Install libimobiledevice-utils and usbmuxd.")
        sys.exit(1)

    udid = ensure_device()
    try:
        summary = get_basic_summary(udid)
    except DeviceError as e:
        console.print(f"[red]{e}[/red]")
        sys.exit(1)

    table = Table(title="iOS Device Summary")
    table.add_column("Field", style="cyan")
    table.add_column("Value")
    for k, v in summary.items():
        table.add_row(k, v)
    console.print(table)


@cli.command()
@click.option("--output", "-o", default="reports", help="Report output directory")
@click.option("--backup-dir", default="backups", help="Where to store/create backups")
@click.option("--encrypted", is_flag=True, help="Request encrypted backup (password may be required interactively)")
@click.option("--password", default=None, help="Backup password if already set / known")
@click.option("--skip-mvt", is_flag=True, help="Skip MVT spyware scan")
@click.option("--skip-backup", is_flag=True, help="Reuse existing backup in backup-dir if present")
def scan(output, backup_dir, encrypted, password, skip_mvt, skip_backup):
    """Full audit: device info + backup + MVT + profiles + apps."""
    tools = check_tools()
    missing = [t for t, ok in tools.items() if not ok]
    if missing:
        console.print(f"[red]Missing tools: {', '.join(missing)}[/red]")
        sys.exit(1)

    udid = ensure_device()
    console.print(Panel(f"Starting audit for UDID: {udid}", style="bold blue"))

    # Device info
    try:
        device_info = get_basic_summary(udid)
    except DeviceError as e:
        console.print(f"[red]Device info failed: {e}[/red]")
        sys.exit(1)

    console.print("[green]✓ Device info collected[/green]")

    # Apps
    apps = []
    suspicious = []
    try:
        apps = list_installed_apps(udid)
        suspicious = flag_suspicious_apps(apps)
        console.print(f"[green]✓ Apps listed ({len(apps)} total, {len(suspicious)} flagged)[/green]")
    except DeviceError as e:
        console.print(f"[yellow]App listing failed: {e}[/yellow]")

    # Backup
    backup_path = None
    backup_root = Path(backup_dir)
    if not skip_backup:
        console.print("[cyan]Creating backup (this can take a long time)...[/cyan]")
        try:
            backup_path = create_backup(
                destination=backup_root,
                udid=udid,
                full=True,
                password=password,
            )
            console.print(f"[green]✓ Backup created at {backup_path}[/green]")
        except DeviceError as e:
            console.print(f"[red]Backup failed: {e}[/red]")
            console.print("Continuing without backup-dependent modules.")
    else:
        # Try to find an existing one
        existing = list(backup_root.glob("*"))
        if existing:
            backup_path = existing[0]
            console.print(f"[yellow]Using existing backup: {backup_path}[/yellow]")

    # Profiles
    profiles = []
    if backup_path:
        profiles = find_profiles_in_backup(backup_path)
        for p in profiles:
            p["risk"] = assess_profile_risk(p)
        console.print(f"[green]✓ Profiles scanned ({len(profiles)} found)[/green]")

    # MVT
    mvt_result = None
    if not skip_mvt and backup_path:
        if not check_mvt():
            console.print("[yellow]mvt-ios not found – skipping MVT. Install with: pip install mvt[/yellow]")
        else:
            console.print("[cyan]Running MVT spyware IOC scan...[/cyan]")
            mvt_out = Path(output) / "mvt"
            try:
                mvt_result = run_mvt(
                    backup_path=backup_path,
                    output_dir=mvt_out,
                    password=password,
                )
                if mvt_result.get("detected_iocs"):
                    console.print("[bold red]⚠ MVT detected potential Indicators of Compromise![/bold red]")
                else:
                    console.print("[green]✓ MVT completed – no known IOCs reported[/green]")
            except DeviceError as e:
                console.print(f"[red]MVT failed: {e}[/red]")

    # Report
    paths = generate_report(
        device_info=device_info,
        mvt_result=mvt_result,
        profiles=profiles,
        apps=apps,
        suspicious_apps=suspicious,
        output_dir=Path(output),
    )
    console.print(Panel(
        f"Report written:\n  Markdown: {paths['markdown']}\n  JSON:     {paths['json']}",
        title="Audit Complete",
        style="bold green",
    ))


@cli.command()
def apps():
    """List installed apps and flag obvious suspicious ones."""
    udid = ensure_device()
    try:
        app_list = list_installed_apps(udid)
        sus = flag_suspicious_apps(app_list)
    except DeviceError as e:
        console.print(f"[red]{e}[/red]")
        sys.exit(1)

    table = Table(title=f"Installed Apps ({len(app_list)})")
    table.add_column("Identifier")
    table.add_column("Name")
    table.add_column("Version")
    for a in app_list[:100]:  # limit display
        table.add_row(a.get("identifier", ""), a.get("name", ""), a.get("version", ""))
    console.print(table)

    if sus:
        console.print("\n[bold red]Potentially suspicious:[/bold red]")
        for s in sus:
            console.print(f"  • {s.get('identifier')} – {s.get('reason')}")


@cli.command()
@click.option("--backup-dir", default="backups", help="Backup root to search")
def profiles(backup_dir):
    """Search for configuration profiles inside existing backups."""
    root = Path(backup_dir)
    if not root.exists():
        console.print(f"[red]No backup directory at {root}[/red]")
        sys.exit(1)

    found = []
    for d in root.iterdir():
        if d.is_dir():
            found.extend(find_profiles_in_backup(d))

    if not found:
        console.print("[yellow]No profiles found in the given backups.[/yellow]")
        return

    for p in found:
        risk = assess_profile_risk(p)
        console.print(f"[{'red' if risk == 'HIGH' else 'yellow' if risk == 'MEDIUM' else 'green'}]"
                      f"{p.get('payload_display_name', 'Unknown')} (risk={risk})[/]")
        console.print(f"  ID: {p.get('payload_identifier')}")
        console.print(f"  Path: {p.get('path')}\n")


if __name__ == "__main__":
    cli()
