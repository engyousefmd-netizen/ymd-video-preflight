"""Small real FFmpeg fixtures check detection behavior, not implementation copies."""
from dataclasses import replace
import json
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

from ymd_preflight.core import AnalysisError, analyze, sha256_file
from ymd_preflight.profiles import BUILTINS, Profile
from ymd_preflight.cli import main, write_reports
from scripts.make_demo import make_demo


@unittest.skipUnless(shutil.which("ffmpeg") and shutil.which("ffprobe"), "FFmpeg is not installed")
class MediaIntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory(prefix="ymd-fixtures-")
        cls.root = Path(cls.tmp.name)
        cls.demo = make_demo(cls.root / "demo")
        cls.before = sha256_file(cls.demo)
        cls.result = analyze(cls.demo, BUILTINS["vertical-social"], cls.demo.parent / "captions.srt", timeout=60)

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def test_known_timed_events_are_found(self):
        result = self.result
        self.assertTrue(result["analysis"]["full_scan"])
        self.assertAlmostEqual(result["source"]["duration_seconds"], 8, delta=.1)
        self.assertTrue(any(abs(e["start"] - 2) < .1 and e["duration"] > 1.0 for e in result["events"]["black"]))
        self.assertTrue(any(abs(e["start"] - 2) < .1 and e["duration"] > 1.0 for e in result["events"]["silence"]))
        self.assertTrue(any(e["duration"] > 1.5 for e in result["events"]["freeze"]))
        self.assertIsInstance(result["audio"]["integrated_lufs"], float)
        self.assertIsInstance(result["audio"]["true_peak_dbfs"], float)

    def test_analysis_preserves_input_bytes_and_avoids_absolute_path_in_json(self):
        self.assertEqual(sha256_file(self.demo), self.before)
        self.assertNotIn(str(self.root), json.dumps(self.result, ensure_ascii=False))
        json.dumps(self.result, allow_nan=False)

    def test_subtitle_problems_are_exposed(self):
        issues = self.result["subtitles"]["issues"]
        self.assertGreaterEqual(len(issues), 2)
        self.assertTrue(any("overlap" in i["code"] for i in issues))
        self.assertTrue(any(i["code"] == "srt_beyond_video" and i["cue"] == 3 for i in issues))

    def test_metadata_only_is_explicitly_incomplete(self):
        result = analyze(self.demo, metadata_only=True)
        self.assertFalse(result["analysis"]["full_scan"])
        self.assertEqual(result["audio"]["integrated_lufs"], None)
        self.assertTrue(any(c["id"] == "scan_complete" and c["status"] == "warn" for c in result["checks"]))

    def test_trailing_events_and_absent_audio_do_not_crash(self):
        file = self.root / "silent-black.mp4"
        subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-nostdin", "-n", "-f", "lavfi",
                        "-i", "color=black:size=160x90:rate=25:duration=2", "-an", "-c:v", "libx264",
                        "-threads", "1", str(file)], check=True, timeout=20)
        result = analyze(file, replace(Profile(), min_short_edge=90))
        self.assertIsNone(result["audio"])
        self.assertTrue(result["events"]["black"])
        self.assertTrue(result["events"]["freeze"])
        self.assertAlmostEqual(result["events"]["freeze"][-1]["end"], 2, delta=.1)
        self.assertEqual(next(c["status"] for c in result["checks"] if c["id"] == "audio_present"), "warn")

    def test_local_filename_with_spaces_and_shell_metacharacters(self):
        unusual = self.root / "فيديو & sample $(do-not-run).mp4"
        shutil.copyfile(self.demo, unusual)
        result = analyze(unusual, metadata_only=True)
        self.assertEqual(result["source"]["name"], unusual.name)
        target = self.root / "special-report"
        write_reports(result, target, "ar")
        html = (target / "report.html").read_text(encoding="utf-8")
        self.assertNotIn("& sample", html)
        self.assertIn("&amp; sample", html)

    def test_invalid_file_and_timeout_are_operational_failures(self):
        invalid = self.root / "broken.mp4"
        invalid.write_text("Not media", encoding="utf-8")
        with self.assertRaises(AnalysisError):
            analyze(invalid)
        self.assertEqual(main([str(invalid), "--output", str(self.root / "invalid-report")]), 2)
        with self.assertRaises(AnalysisError):
            analyze(self.demo, timeout=0.000001)

    def test_report_roundtrip_and_no_implicit_overwrite(self):
        output = self.root / "report"
        write_reports(self.result, output, "ar")
        loaded = json.loads((output / "report.json").read_text(encoding="utf-8"))
        self.assertEqual(loaded["summary"], self.result["summary"])
        with self.assertRaises(ValueError):
            write_reports(self.result, output, "ar")


if __name__ == "__main__":
    unittest.main()
