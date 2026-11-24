import hashlib
import json
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest import mock
from urllib.error import URLError

from modules.indicators import (
    refresh_indicator_sets,
    register_indicator_source,
)


SAMPLE_BUNDLE = {
    "type": "bundle",
    "id": "bundle--00000000-0000-4000-8000-000000000001",
    "objects": [
        {
            "type": "indicator",
            "spec_version": "2.1",
            "id": "indicator--00000000-0000-4000-8000-000000000002",
            "created": "2026-01-01T00:00:00Z",
            "modified": "2026-01-01T00:00:00Z",
            "name": "Example",
            "pattern": "[domain-name:value = 'example.invalid']",
            "pattern_type": "stix",
            "valid_from": "2026-01-01T00:00:00Z",
        }
    ],
}


class IndicatorFeedTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.cache = Path(self.temporary.name) / "indicators"

    def tearDown(self):
        self.temporary.cleanup()

    @staticmethod
    def response_for(url, payload=SAMPLE_BUNDLE):
        response = mock.MagicMock()
        response.__enter__.return_value = response
        response.geturl.return_value = url
        response.read.return_value = json.dumps(payload).encode("utf-8")
        return response

    def test_requires_https_and_rejects_credentials(self):
        with self.assertRaises(ValueError):
            register_indicator_source(self.cache, "http://example.test/feed.json")
        with self.assertRaises(ValueError):
            register_indicator_source(self.cache, "https://user:pass@example.test/feed.json")

    def test_refreshes_mvt_and_a_configured_stix_feed(self):
        register_indicator_source(self.cache, "https://feeds.example.test/mobile.json")
        completed = subprocess.CompletedProcess([], 0, "", "")
        with mock.patch("modules.indicators.subprocess.run", return_value=completed) as run:
            with mock.patch(
                "modules.indicators.urlopen",
                return_value=self.response_for("https://feeds.example.test/mobile.json"),
            ):
                result = refresh_indicator_sets(
                    self.cache, timeout=1, mvt_command="mvt-ios"
                )

        run.assert_called_once_with(
            ["mvt-ios", "download-iocs"],
            capture_output=True,
            text=True,
            timeout=240,
            check=False,
        )
        self.assertTrue(result["amnesty"]["ok"])
        feed = result["feed:feeds.example.test"]
        self.assertTrue(feed["ok"])
        self.assertEqual(feed["indicator_count"], 1)
        self.assertTrue(Path(feed["path"]).is_file())
        self.assertIsNotNone(feed["last_updated"])

    def test_failed_refresh_keeps_the_previous_feed_available(self):
        register_indicator_source(self.cache, "https://feeds.example.test/mobile.json")
        old_feed = self.cache / "cached-feed.stix.json"
        old_feed.write_text(json.dumps(SAMPLE_BUNDLE), encoding="utf-8")
        source = json.loads((self.cache / "sources.json").read_text())
        cache_path = self.cache / (hashlib.sha256(source[0]["url"].encode()).hexdigest() + ".stix.json")
        old_feed.rename(cache_path)
        with mock.patch("modules.indicators.subprocess.run", side_effect=FileNotFoundError):
            with mock.patch("modules.indicators.urlopen", side_effect=URLError("offline")):
                result = refresh_indicator_sets(self.cache, mvt_command="mvt-ios")

        feed = result["feed:feeds.example.test"]
        self.assertFalse(feed["ok"])
        self.assertTrue(Path(feed["path"]).is_file())
        self.assertIn("offline", feed["message"])

    def test_https_feed_cannot_redirect_to_plain_http(self):
        register_indicator_source(self.cache, "https://feeds.example.test/mobile.json")
        completed = subprocess.CompletedProcess([], 0, "", "")
        with mock.patch("modules.indicators.subprocess.run", return_value=completed):
            with mock.patch(
                "modules.indicators.urlopen",
                return_value=self.response_for("http://feeds.example.test/mobile.json"),
            ):
                result = refresh_indicator_sets(self.cache, mvt_command="mvt-ios")

        feed = result["feed:feeds.example.test"]
        self.assertFalse(feed["ok"])
        self.assertIn("redirected away from HTTPS", feed["message"])
        self.assertIsNone(feed["path"])


if __name__ == "__main__":
    unittest.main()
