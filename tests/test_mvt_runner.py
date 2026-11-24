import json
import tempfile
import threading
import unittest
from pathlib import Path
from unittest import mock

from modules.device import DeviceError
from modules.mvt_runner import ScanCancelled, run_mvt


class FakeProcess:
    def __init__(self, returncode=0):
        self.returncode = returncode
        self.terminated = False

    def poll(self):
        return self.returncode

    def communicate(self, timeout=None):
        return "finished", ""

    def terminate(self):
        self.terminated = True
        self.returncode = -15

    def kill(self):
        self.returncode = -9


class MvtRunnerTests(unittest.TestCase):
    def test_parses_mvt_alerts_and_ignores_extracted_metadata(self):
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary) / "results"
            output.mkdir()
            alerts = [{"module": "test", "matched_indicator": {"pattern": "test"}}]
            (output / "alerts.json").write_text(json.dumps(alerts))
            (output / "manifest.json").write_text(json.dumps([{"path": "metadata"}]))
            indicator_file = Path(temporary) / "feed.stix.json"
            indicator_file.write_text("{}")
            process = FakeProcess()
            with mock.patch("modules.mvt_runner.subprocess.Popen", return_value=process) as popen:
                result = run_mvt(
                    Path(temporary),
                    output,
                    iocs_path=indicator_file,
                    executable="mvt-ios",
                )

        self.assertTrue(result["success"])
        self.assertEqual(result["findings"], alerts)
        self.assertTrue(result["detected_iocs"])
        self.assertIn("--iocs", popen.call_args.args[0])

    def test_uses_per_module_alerts_when_aggregate_file_is_absent(self):
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary) / "results"
            output.mkdir()
            alerts = [{"module": "test", "matched_indicator": None}]
            (output / "test_detected.json").write_text(json.dumps(alerts))
            (output / "manifest.json").write_text(json.dumps([{"path": "metadata"}]))
            with mock.patch("modules.mvt_runner.subprocess.Popen", return_value=FakeProcess()):
                result = run_mvt(
                    Path(temporary),
                    output,
                    executable="mvt-ios",
                )

        self.assertTrue(result["success"])
        self.assertEqual(result["findings"], alerts)
        self.assertFalse(result["detected_iocs"])

    def test_missing_custom_indicator_file_is_an_error(self):
        with tempfile.TemporaryDirectory() as temporary:
            with self.assertRaises(DeviceError):
                run_mvt(
                    Path(temporary),
                    Path(temporary) / "results",
                    iocs_path=Path(temporary) / "missing.json",
                    executable="mvt-ios",
                )

    def test_cancels_running_mvt_process(self):
        with tempfile.TemporaryDirectory() as temporary:
            event = threading.Event()
            event.set()
            process = FakeProcess(returncode=None)
            with mock.patch("modules.mvt_runner.subprocess.Popen", return_value=process):
                with self.assertRaises(ScanCancelled):
                    run_mvt(
                        Path(temporary),
                        Path(temporary) / "results",
                        executable="mvt-ios",
                        cancel_event=event,
                    )
        self.assertTrue(process.terminated)


if __name__ == "__main__":
    unittest.main()
