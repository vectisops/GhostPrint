import json
import os
import threading
import tempfile
import unittest
from pathlib import Path

from modules.secure_workspace import (
    PrivateWorkspace,
    WorkspaceError,
    cleanup_stale_workspaces,
)


class PrivateWorkspaceTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name) / "ghostprint"

    def tearDown(self):
        self.temporary.cleanup()

    def make_backup(self):
        backup = Path(self.temporary.name) / "source-backup"
        backup.mkdir()
        (backup / "Manifest.db").write_bytes(b"manifest")
        (backup / "record.dat").write_bytes(b"original")
        return backup

    def test_copy_does_not_change_source_and_cleanup_removes_working_copy(self):
        source = self.make_backup()
        workspace = PrivateWorkspace(self.root)

        copied = workspace.copy_backup(source)
        self.assertEqual((copied / "record.dat").read_bytes(), b"original")
        (copied / "record.dat").write_bytes(b"changed")
        self.assertEqual((source / "record.dat").read_bytes(), b"original")

        workspace.cleanup()
        self.assertFalse(workspace.path.exists())
        self.assertEqual((source / "record.dat").read_bytes(), b"original")

    def test_rejects_links_inside_backup(self):
        source = self.make_backup()
        target = Path(self.temporary.name) / "outside.txt"
        target.write_text("outside")
        try:
            (source / "linked.txt").symlink_to(target)
        except OSError as error:
            self.skipTest(f"symlink creation unavailable: {error}")
        workspace = PrivateWorkspace(self.root)
        try:
            with self.assertRaises(WorkspaceError):
                workspace.copy_backup(source)
            self.assertFalse((workspace.path / "backup").exists())
        finally:
            workspace.cleanup()

    def test_cancellation_stops_copy_and_removes_partial_copy(self):
        source = self.make_backup()
        workspace = PrivateWorkspace(self.root)
        cancel_event = threading.Event()
        cancel_event.set()
        try:
            with self.assertRaisesRegex(WorkspaceError, "cancelled"):
                workspace.copy_backup(source, cancel_event=cancel_event)
            self.assertFalse((workspace.path / "backup").exists())
        finally:
            workspace.cleanup()

    def test_stale_cleanup_only_removes_dead_marked_sessions(self):
        stale = self.root / "session-stale"
        stale.mkdir(parents=True)
        (stale / ".ghostprint-session").write_text(
            json.dumps({"app": "GhostPrint", "version": 1, "pid": 999999999})
        )
        (stale / "backup.dat").write_text("temporary")
        foreign = self.root / "unmarked"
        foreign.mkdir()
        (foreign / "keep.txt").write_text("keep")

        result = cleanup_stale_workspaces(self.root)

        self.assertEqual(result["removed"], ["session-stale"])
        self.assertFalse(stale.exists())
        self.assertTrue((foreign / "keep.txt").exists())

    def test_stale_cleanup_preserves_active_session(self):
        active = PrivateWorkspace(self.root)

        cleanup_stale_workspaces(self.root)

        self.assertTrue(active.path.exists())
        active.cleanup()


if __name__ == "__main__":
    unittest.main()
