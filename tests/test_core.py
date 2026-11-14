"""Behavioral checks with synthetic metadata/logs; no FFmpeg process is run."""
from __future__ import annotations

import contextlib
from dataclasses import replace
import hashlib
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from ymd_preflight import cli, core
from ymd_preflight.profiles import BUILTINS, Profile, load_profile, validate_profile


class VideoMetadataTests(unittest.TestCase):
    def test_rotation_and_anamorphic_pixels_determine_display_geometry(self):
        video = core.summarize_video({
            "index": 3, "codec_name": "h264", "width": 720, "height": 576,
            "sample_aspect_ratio": "16:15", "avg_frame_rate": "25/1",
            "tags": {"rotate": "0"}, "side_data_list": [{"rotation": -90}],
        })
        self.assertEqual((video["width"], video["height"]), (720, 576))
        self.assertEqual((video["display_width"], video["display_height"]), (576, 768))
        self.assertEqual(video["rotation_degrees"], 270)
        self.assertAlmostEqual(video["display_width"] / video["display_height"], 3 / 4)

    def test_display_matrix_rotation_takes_precedence_over_legacy_tag(self):
        video = core.summarize_video({
            "width": 1920, "height": 1080, "sample_aspect_ratio": "1:1",
            "tags": {"rotate": "90"}, "side_data_list": [{"rotation": 180}],
        })
        self.assertEqual(video["rotation_degrees"], 180)
        self.assertEqual((video["display_width"], video["display_height"]), (1920, 1080))

    def test_unknown_sample_aspect_ratio_defaults_to_square_pixels(self):
        for sar in ("N/A", "0:1", "-1:1", "0:0"):
            with self.subTest(sar=sar):
                video = core.summarize_video({"width": 640, "height": 480,
                                              "sample_aspect_ratio": sar})
                self.assertEqual(video["sample_aspect_ratio"], 1.0)
                self.assertEqual(video["display_width"], 640)

    def test_invalid_average_frame_rate_falls_back_to_rational_stream_rate(self):
        video = core.summarize_video({"width": 1920, "height": 1080,
                                      "avg_frame_rate": "0/0", "r_frame_rate": "30000/1001"})
        self.assertAlmostEqual(video["fps"], 30000 / 1001)

    def test_cover_art_is_ignored_and_default_playable_video_is_selected(self):
        streams = [
            {"index": 0, "codec_type": "video", "disposition": {"attached_pic": 1, "default": 1}},
            {"index": 1, "codec_type": "video", "disposition": {}},
            {"index": 2, "codec_type": "video", "disposition": {"default": 1}},
        ]
        self.assertEqual(core.choose_stream(streams, "video")["index"], 2)
        self.assertIsNone(core.choose_stream(streams[:1], "video"))


class EventParserTests(unittest.TestCase):
    def setUp(self):
        self.profile = Profile()

    def test_leading_and_trailing_silence_are_separate_intervals(self):
        log = """
        [silencedetect] silence_start: 0
        [silencedetect] silence_end: 1.25 | silence_duration: 1.25
        [silencedetect] silence_start: 8.5
        """
        events = core.parse_events(log, 10.0, self.profile)
        self.assertEqual(events["silence"], [
            {"start": 0.0, "end": 1.25, "duration": 1.25},
            {"start": 8.5, "end": 10.0, "duration": 1.5, "open_at_end": True},
        ])

    def test_freeze_parser_accepts_metadata_syntax_and_closes_at_known_end(self):
        log = """
        lavfi.freezedetect.freeze_start=2.5
        lavfi.freezedetect.freeze_duration=1.5
        lavfi.freezedetect.freeze_end=4
        [freezedetect] freeze_start: 8
        """
        self.assertEqual(core.parse_events(log, 10.0, self.profile)["freeze"], [
            {"start": 2.5, "end": 4.0, "duration": 1.5},
            {"start": 8.0, "end": 10.0, "duration": 2.0, "open_at_end": True},
        ])

    def test_unknown_duration_does_not_invent_an_end_for_open_events(self):
        events = core.parse_events("silence_start: 4\nfreeze_start: 5", None, self.profile)
        self.assertEqual(events["silence"], [])
        self.assertEqual(events["freeze"], [])

    def test_closed_event_cannot_extend_past_media_duration(self):
        events = core.parse_events("silence_start: 8\nsilence_end: 12", 10, self.profile)
        self.assertEqual(events["silence"], [{"start": 8.0, "end": 10.0, "duration": 2.0}])

    def test_short_pauses_and_orphan_ends_do_not_become_warnings(self):
        log = """
        silence_end: 3
        silence_start: 4
        silence_end: 4.2
        freeze_end: 5
        freeze_start: 6
        freeze_end: 6.5
        black_start:0 black_end:0.2 black_duration:0.2
        """
        self.assertEqual(core.parse_events(log, 10, self.profile),
                         {"black": [], "silence": [], "freeze": []})

    def test_black_parser_handles_ffmpeg_scientific_timestamps(self):
        log = "[blackdetect] black_start:1e-2 black_end:5.1e-1 black_duration:5e-1"
        self.assertEqual(core.parse_events(log, 1, self.profile)["black"],
                         [{"start": 0.01, "end": 0.51, "duration": 0.5}])


class LoudnessParserTests(unittest.TestCase):
    def test_silent_audio_is_unmeasurable_not_a_finite_loudness_pass(self):
        data = core.parse_loudness('noise\n{"input_i":"-inf","input_tp":"-inf","input_lra":"0.00"}')
        self.assertIsNone(data["integrated_lufs"])
        self.assertIsNone(data["true_peak_dbfs"])
        self.assertEqual(data["integrated_lufs_raw"], "-inf")
        self.assertEqual(data["loudness_range_lu"], 0.0)
        json.dumps(data, allow_nan=False)

    def test_last_valid_measurement_is_used_despite_trailing_malformed_json(self):
        log = """
        {"input_i":"-30.0","input_tp":"-6.0","input_lra":"1.0"}
        {"input_i":"-16.2","input_tp":"-1.4","input_lra":"3.8"}
        {"input_i":invalid}
        """
        data = core.parse_loudness(log)
        self.assertEqual(data["integrated_lufs"], -16.2)
        self.assertEqual(data["true_peak_dbfs"], -1.4)
        self.assertEqual(data["loudness_range_lu"], 3.8)

    def test_missing_measurement_remains_missing(self):
        self.assertEqual(core.parse_loudness("[decoder] no loudness output"), {})


class ProfileValidationTests(unittest.TestCase):
    def test_all_builtin_profiles_are_valid(self):
        for name, profile in BUILTINS.items():
            with self.subTest(name=name):
                self.assertEqual(validate_profile(profile), profile)

    def test_boolean_nonfinite_and_invalid_ranges_are_rejected(self):
        invalid = [
            {"name": " "}, {"min_short_edge": True}, {"min_short_edge": 720.5},
            {"max_subtitle_lines": 0}, {"expected_aspect_ratio": 0},
            {"expected_aspect_ratio": float("nan")}, {"target_lufs": float("inf")},
            {"black_min_seconds": 0}, {"silence_min_seconds": -1},
            {"freeze_min_seconds": 0}, {"min_fps": 60, "max_fps": 24},
            {"aspect_tolerance": -0.1}, {"black_picture_ratio": 1.1},
            {"target_lufs": -4}, {"max_true_peak_dbfs": 1},
            {"loudness_tolerance_lu": -1}, {"silence_noise_db": -121},
        ]
        for overrides in invalid:
            with self.subTest(overrides=overrides), self.assertRaises(ValueError):
                validate_profile(replace(Profile(), **overrides))

    def test_profile_overrides_preserve_selected_house_profile(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "house.json"
            path.write_text('{"min_short_edge":1080,"name":"فريق التحرير"}', encoding="utf-8-sig")
            profile = load_profile("vertical-social", path)
        self.assertEqual(profile.min_short_edge, 1080)
        self.assertEqual(profile.name, "فريق التحرير")
        self.assertEqual(profile.expected_aspect_ratio, 9 / 16)

    def test_unknown_fields_and_nonobject_json_fail_instead_of_being_ignored(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "house.json"
            for content in ('{"min_fpss":24}', '[]', '{"max_fps":NaN}'):
                with self.subTest(content=content):
                    path.write_text(content, encoding="utf-8")
                    with self.assertRaises(ValueError):
                        load_profile(path=path)


class AnalysisStatusTests(unittest.TestCase):
    """Exercise report decisions while all external analysis is replaced by fixtures."""

    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.path = Path(temp.name) / "sample.mp4"
        self.source_bytes = b"synthetic fixture; not an encoded video"
        self.path.write_bytes(self.source_bytes)
        self.probe = {
            "format": {"duration": "10"},
            "streams": [
                {"index": 0, "codec_type": "video", "codec_name": "h264",
                 "width": 1920, "height": 1080, "pix_fmt": "yuv420p",
                 "avg_frame_rate": "25/1", "duration": "10"},
                {"index": 1, "codec_type": "audio", "codec_name": "aac",
                 "sample_rate": "48000", "channels": 2, "duration": "10"},
            ],
        }
        replacements = [
            patch.object(core, "probe_media", return_value=self.probe),
            patch.object(core, "_binary", side_effect=lambda name: "/fixture/" + name),
            patch.object(core, "_version", return_value="synthetic engine"),
            patch.object(core, "_run", side_effect=AssertionError("Tests must not run FFmpeg")),
        ]
        for replacement in replacements:
            replacement.start()
            self.addCleanup(replacement.stop)

    def test_failed_full_scan_keeps_metadata_but_never_claims_integrity_pass(self):
        with patch.object(core, "scan_media", side_effect=core.AnalysisError("Scan timed out")):
            report = core.analyze(self.path)
        checks = {check["id"]: check for check in report["checks"]}
        self.assertFalse(report["analysis"]["full_scan"])
        self.assertEqual(report["summary"]["status"], "fail")
        self.assertEqual(checks["scan_complete"]["status"], "fail")
        self.assertEqual(report["video"]["width"], 1920)
        self.assertIn("Scan timed out", report["analysis"]["warnings"])
        for incomplete_check in ("decode_integrity", "black_events", "silence_events", "loudness"):
            self.assertNotIn(incomplete_check, checks)
        self.assertEqual(self.path.read_bytes(), self.source_bytes)
        self.assertEqual(report["source"]["sha256"], hashlib.sha256(self.source_bytes).hexdigest())

    def test_metadata_only_report_stays_incomplete_and_does_not_scan(self):
        with patch.object(core, "scan_media", side_effect=AssertionError("Unexpected full scan")):
            report = core.analyze(self.path, metadata_only=True)
        checks = {check["id"]: check for check in report["checks"]}
        self.assertFalse(report["analysis"]["full_scan"])
        self.assertEqual(checks["scan_complete"]["status"], "warn")
        self.assertEqual(report["summary"]["status"], "warn")
        self.assertNotIn("decode_integrity", checks)

    def test_successful_scan_of_silent_audio_warns_and_serializes_strict_json(self):
        log = '{"input_i":"-inf","input_tp":"-inf","input_lra":"0.0"}'
        with patch.object(core, "scan_media", return_value=(log, "synthetic ffmpeg")):
            report = core.analyze(self.path)
        checks = {check["id"]: check for check in report["checks"]}
        self.assertTrue(report["analysis"]["full_scan"])
        self.assertEqual(checks["loudness"]["status"], "warn")
        self.assertEqual(checks["true_peak"]["status"], "warn")
        self.assertEqual(report["summary"]["status"], "warn")
        json.dumps(report, allow_nan=False)

    def test_finished_decoder_with_corruption_is_a_failure(self):
        log = "[h264] error while decoding MB 1 2\n"
        with patch.object(core, "scan_media", return_value=(log, "synthetic ffmpeg")):
            report = core.analyze(self.path)
        checks = {check["id"]: check for check in report["checks"]}
        self.assertTrue(report["analysis"]["full_scan"])
        self.assertEqual(checks["decode_integrity"]["status"], "fail")
        self.assertEqual(report["summary"]["status"], "fail")

    def test_failed_ffmpeg_exit_discards_partial_detection_log(self):
        partial_log = "[blackdetect] black_start:0 black_end:2 black_duration:2"
        with patch.object(core, "_run", return_value=(1, "", partial_log)):
            with self.assertRaises(core.AnalysisError):
                core.scan_media(self.path, {"stream_index": 0}, None, Profile(), timeout=1)


class ReportOutputSafetyTests(unittest.TestCase):
    def test_existing_report_is_not_overwritten_and_other_reports_are_not_created(self):
        with tempfile.TemporaryDirectory() as folder:
            output = Path(folder)
            existing = output / "report.json"
            existing.write_text("keep this previous report", encoding="utf-8")
            with patch.object(cli, "render_html", side_effect=AssertionError("Must reject before rendering")):
                with self.assertRaises(ValueError):
                    cli.write_reports({}, output, "ar")
            self.assertEqual(existing.read_text(encoding="utf-8"), "keep this previous report")
            self.assertEqual({p.name for p in output.iterdir()}, {"report.json"})

    def test_no_overwrite_preserves_a_report_created_by_a_concurrent_run(self):
        with tempfile.TemporaryDirectory() as folder:
            output = Path(folder)
            concurrent_target = output / "report.json"
            original = "report produced by another run"

            def render_after_concurrent_publish(*args):
                concurrent_target.write_text(original, encoding="utf-8")
                return "<p>new report</p>"

            with patch.object(cli, "render_html", side_effect=render_after_concurrent_publish), \
                    patch.object(cli, "render_markdown", return_value="new report"):
                with self.assertRaises((OSError, ValueError)):
                    cli.write_reports({"new": True}, output, "en", overwrite=False)
            self.assertEqual(concurrent_target.read_text(encoding="utf-8"), original)

    def test_overwrite_flag_cannot_replace_a_protected_input(self):
        with tempfile.TemporaryDirectory() as folder:
            output = Path(folder)
            source = output / "report.html"
            source.write_bytes(b"original media contents")
            with self.assertRaises(ValueError):
                cli.write_reports({}, output, "ar", overwrite=True, protected_paths=(source,))
            self.assertEqual(source.read_bytes(), b"original media contents")

    def test_symlink_report_target_is_rejected_without_touching_destination(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            output = root / "reports"
            output.mkdir()
            destination = root / "valuable.txt"
            destination.write_text("unchanged", encoding="utf-8")
            try:
                (output / "report.md").symlink_to(destination)
            except (OSError, NotImplementedError):
                self.skipTest("Symlink creation is unavailable on this platform")
            with self.assertRaises(ValueError):
                cli.write_reports({}, output, "en", overwrite=True)
            self.assertEqual(destination.read_text(encoding="utf-8"), "unchanged")
            self.assertTrue((output / "report.md").is_symlink())

    def test_report_files_are_utf8_and_staging_files_are_cleaned_up(self):
        with tempfile.TemporaryDirectory() as folder:
            output = Path(folder) / "reports"
            with patch.object(cli, "render_html", return_value="<p>فحص</p>"), \
                    patch.object(cli, "render_markdown", return_value="# فحص"):
                cli.write_reports({"title": "فحص"}, output, "ar")
            self.assertEqual(json.loads((output / "report.json").read_text(encoding="utf-8")), {"title": "فحص"})
            self.assertEqual((output / "report.html").read_text(encoding="utf-8"), "<p>فحص</p>")
            self.assertEqual((output / "report.md").read_text(encoding="utf-8"), "# فحص")
            self.assertEqual({p.name for p in output.iterdir()}, {"report.html", "report.json", "report.md"})

    def test_incomplete_scan_remains_operational_failure_even_with_fail_on_never(self):
        report = {"summary": {"status": "fail", "counts": {"fail": 1}},
                  "checks": [{"id": "scan_complete", "status": "fail"}]}
        with patch.object(cli, "analyze", return_value=report), \
                patch.object(cli, "write_reports") as write, \
                contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            result = cli.main(["fixture.mp4", "--output", "fixture-reports", "--fail-on", "never"])
        self.assertEqual(result, 2)
        write.assert_called_once()


if __name__ == "__main__":
    unittest.main()
