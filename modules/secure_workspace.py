"""Private temporary storage for imported device backups."""

import json
import os
import shutil
import stat
import tempfile
import threading
from pathlib import Path
from typing import Callable, Dict, List, Optional


_MARKER_NAME = ".ghostprint-session"
_MARKER_APP = "GhostPrint"


class WorkspaceError(Exception):
    """Raised when a temporary backup workspace cannot be handled safely."""


def _is_link_or_junction(path: Path) -> bool:
    if path.is_symlink():
        return True
    is_junction = getattr(os.path, "isjunction", None)
    if is_junction and is_junction(path):
        return True
    if os.name == "nt":
        try:
            attributes = getattr(path.lstat(), "st_file_attributes", 0)
        except FileNotFoundError:
            return False
        reparse_point = getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400)
        return bool(attributes & reparse_point)
    return False


def _prepare_root(root: Optional[Path] = None) -> Path:
    root = Path(root) if root is not None else Path(tempfile.gettempdir()) / "ghostprint"
    if _is_link_or_junction(root):
        raise WorkspaceError("The GhostPrint temporary-storage path is a link or junction.")
    root.mkdir(mode=0o700, parents=True, exist_ok=True)
    if not root.is_dir():
        raise WorkspaceError("The GhostPrint temporary-storage path is not a directory.")
    if os.name != "nt":
        if root.stat().st_uid != os.getuid():
            raise WorkspaceError("The GhostPrint temporary-storage directory has a different owner.")
        root.chmod(0o700)
    return root


def _read_marker(directory: Path) -> Optional[Dict[str, object]]:
    marker = directory / _MARKER_NAME
    if _is_link_or_junction(marker) or not marker.is_file():
        return None
    try:
        content = json.loads(marker.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    if (
        not isinstance(content, dict)
        or content.get("app") != _MARKER_APP
        or content.get("version") != 1
    ):
        return None
    return content


def _process_is_running(pid: object) -> bool:
    if not isinstance(pid, int) or pid <= 0:
        return False
    try:
        os.kill(pid, 0)
    except OSError:
        return False
    return True


def cleanup_stale_workspaces(root: Optional[Path] = None) -> Dict[str, List[str]]:
    """Remove marked GhostPrint workspaces left by processes that are no longer running."""
    root_path = _prepare_root(root)
    removed: List[str] = []
    errors: List[str] = []
    for entry in root_path.iterdir():
        if _is_link_or_junction(entry) or not entry.is_dir():
            continue
        marker = _read_marker(entry)
        if marker is None or _process_is_running(marker.get("pid")):
            continue
        try:
            shutil.rmtree(entry)
            removed.append(entry.name)
        except OSError as error:
            errors.append(f"{entry.name}: {error}")
    return {"removed": removed, "errors": errors}


class PrivateWorkspace:
    """An app-owned temporary directory removed when the session is closed."""

    def __init__(self, root: Optional[Path] = None) -> None:
        self.root = _prepare_root(root)
        self.path = Path(tempfile.mkdtemp(prefix="session-", dir=str(self.root)))
        if os.name != "nt":
            self.path.chmod(0o700)
        marker = {
            "app": _MARKER_APP,
            "version": 1,
            "pid": os.getpid(),
        }
        marker_path = self.path / _MARKER_NAME
        try:
            with marker_path.open("x", encoding="utf-8") as file:
                json.dump(marker, file)
        except OSError as error:
            shutil.rmtree(self.path, ignore_errors=True)
            raise WorkspaceError(f"Could not mark temporary workspace: {error}") from error
        self._closed = False

    @staticmethod
    def _reject_links(source: Path) -> None:
        for current, directories, filenames in os.walk(source, followlinks=False):
            for name in directories + filenames:
                entry = Path(current) / name
                if _is_link_or_junction(entry):
                    raise WorkspaceError(
                        f"The selected backup contains a link or junction and cannot be copied safely: {entry}"
                    )
                mode = entry.lstat().st_mode
                if not (stat.S_ISDIR(mode) or stat.S_ISREG(mode)):
                    raise WorkspaceError(
                        f"The selected backup contains an unsupported file: {entry}"
                    )

    def copy_backup(
        self,
        backup_path: Path,
        cancel_event: Optional[threading.Event] = None,
        progress_callback: Optional[Callable[[int, int], None]] = None,
    ) -> Path:
        """Copy a valid iOS/iPadOS backup into this workspace without following links."""
        source = Path(backup_path).expanduser()
        if _is_link_or_junction(source) or not source.is_dir():
            raise WorkspaceError("Choose an existing backup folder.")
        if not any((source / name).is_file() for name in ("Manifest.db", "Manifest.plist")):
            raise WorkspaceError(
                "This folder does not look like an iOS/iPadOS backup "
                "(Manifest.db or Manifest.plist was not found)."
            )
        self._reject_links(source)
        destination = self.path / "backup"
        try:
            file_paths = []
            directory_paths = []
            for current, directories, filenames in os.walk(source, followlinks=False):
                current_path = Path(current)
                relative = current_path.relative_to(source)
                directory_paths.extend(relative / name for name in directories)
                file_paths.extend(relative / name for name in filenames)
            destination.mkdir()
            for relative in directory_paths:
                (destination / relative).mkdir(parents=True, exist_ok=True)
            for index, relative in enumerate(file_paths, start=1):
                if cancel_event and cancel_event.is_set():
                    raise WorkspaceError("Backup copy cancelled.")
                target = destination / relative
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(source / relative, target)
                if progress_callback:
                    progress_callback(index, len(file_paths))
        except OSError as error:
            shutil.rmtree(destination, ignore_errors=True)
            raise WorkspaceError(f"Could not copy the backup into temporary storage: {error}") from error
        except WorkspaceError:
            shutil.rmtree(destination, ignore_errors=True)
            raise
        return destination

    def cleanup(self) -> None:
        """Delete this marked workspace; failures are surfaced to the caller."""
        if self._closed:
            return
        if self.path.parent != self.root or _read_marker(self.path) is None:
            raise WorkspaceError("Refusing to remove an unrecognized temporary workspace.")
        try:
            shutil.rmtree(self.path)
        except OSError as error:
            raise WorkspaceError(f"Could not remove temporary backup data: {error}") from error
        self._closed = True
