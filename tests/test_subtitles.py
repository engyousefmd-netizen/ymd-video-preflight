"""Small real-file checks for the SRT auditor; only the standard library."""

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from ymd_preflight.subtitles import MAX_FILE_BYTES, audit_srt


class SubtitleAuditTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.directory = Path(self.temp.name)

    def write_srt(self, content, name="ترجمة_الفيديو.srt", encoding="utf-8"):
        path = self.directory / name
        path.write_text(content, encoding=encoding)
        return path

    @staticmethod
    def codes(report):
        return [issue["code"] for issue in report["issues"]]

    def test_ملف_عربي_سليم_مع_BOM_يبقى_كما_هو(self):
        path = self.write_srt(
            "1\r\n00:00:00,000 --> 00:00:01,000\r\nمرحبا\r\n\r\n"
            "2\r\n00:00:01,000 --> 00:00:02,000\r\nأهلا\r\n",
            encoding="utf-8-sig",
        )
        original = path.read_bytes()
        report = audit_srt(path, 2.0)
        self.assertEqual(report, {"file": path.name, "cue_count": 2, "issues": []})
        self.assertEqual(path.read_bytes(), original)

    def test_وسوم_HTML_لا_تدخل_في_عدد_الحروف(self):
        path = self.write_srt("1\n00:00:00,000 --> 00:00:01,000\n<i>مرحبا</i>\n")
        report = audit_srt(path, None, max_chars_per_line=5, max_cps=5)
        self.assertEqual(report["issues"], [])
        path = self.write_srt("1\n00:00:00,000 --> 00:00:01,000\n<b>&amp;</b>\n")
        self.assertEqual(audit_srt(path, None, 1, 1)["issues"], [])

    def test_فترة_صفرية_او_سالبة_لا_تسبب_قسمة_على_صفر(self):
        path = self.write_srt(
            "1\n00:00:01,000 --> 00:00:01,000\nأول\n\n"
            "2\n00:00:03,000 --> 00:00:02,000\nثان\n"
        )
        report = audit_srt(path, None)
        self.assertEqual(self.codes(report).count("srt_invalid_interval"), 2)
        self.assertNotIn("srt_high_cps", self.codes(report))
        self.assertTrue(all(item["severity"] == "fail" for item in report["issues"]))

    def test_توقيت_مفقود_او_غير_صالح(self):
        path = self.write_srt(
            "1\n00:00:60,000 --> 00:01:01,000\nأول\n\n"
            "2\nالنص بلا توقيت\n\n3\n"
        )
        report = audit_srt(path, None)
        self.assertEqual(report["cue_count"], 3)
        self.assertIn("srt_malformed_timestamp", self.codes(report))
        self.assertEqual(self.codes(report).count("srt_missing_timestamp"), 2)

    def test_ترتيب_خاطئ_لا_يعني_تداخلا(self):
        path = self.write_srt(
            "1\n00:00:04,000 --> 00:00:05,000\nأول\n\n"
            "2\n00:00:01,000 --> 00:00:02,000\nثان\n"
        )
        codes = self.codes(audit_srt(path, None))
        self.assertIn("srt_out_of_order", codes)
        self.assertNotIn("srt_overlap", codes)

    def test_تداخل_متداخل_مع_مقطع_طويل(self):
        path = self.write_srt(
            "1\n00:00:00,000 --> 00:00:10,000\nطويل\n\n"
            "2\n00:00:01,000 --> 00:00:02,000\nأول\n\n"
            "3\n00:00:03,000 --> 00:00:04,000\nثان\n"
        )
        report = audit_srt(path, 10)
        overlaps = [item for item in report["issues"] if item["code"] == "srt_overlap"]
        self.assertEqual([item["cue"] for item in overlaps], [2, 3])

    def test_تجاوز_مدة_الفيديو_وحدود_القراءة(self):
        path = self.write_srt(
            "1\n00:00:00,000 --> 00:00:01,000\n" + "أ" * 43 + "\nثان\nثالث\n"
        )
        codes = self.codes(audit_srt(path, 0.5))
        self.assertTrue(
            {"srt_beyond_video", "srt_line_too_long", "srt_too_many_lines", "srt_high_cps"}
            .issubset(codes)
        )

    def test_مقطع_بلا_رقم_يظل_قابلا_للفحص(self):
        path = self.write_srt("00:00:00,000 --> 00:00:01,000\nمرحبا\n")
        report = audit_srt(path, None)
        self.assertEqual(self.codes(report), ["srt_missing_index"])
        self.assertEqual(report["issues"][0]["cue"], 1)

    def test_ترميز_غير_صالح_يرجع_خطأ_واضحا(self):
        path = self.directory / "ترميز_غير_صالح.srt"
        path.write_bytes(b"\xff\xfeinvalid")
        report = audit_srt(path, None)
        self.assertEqual(report["cue_count"], 0)
        self.assertEqual(self.codes(report), ["srt_encoding"])
        self.assertEqual(report["issues"][0]["severity"], "fail")

    def test_ملف_مفقود_او_غير_قابل_للقراءة(self):
        path = self.directory / "غير_موجود.srt"
        self.assertEqual(self.codes(audit_srt(path, None)), ["srt_file_missing"])
        path = self.write_srt("1\n00:00:00,000 --> 00:00:01,000\nمرحبا\n")
        with patch.object(Path, "open", side_effect=PermissionError("not readable")):
            report = audit_srt(path, None)
        self.assertEqual(self.codes(report), ["srt_read_error"])
        self.assertEqual(report["issues"][0]["severity"], "fail")
        self.assertEqual(self.codes(audit_srt(self.directory, None)), ["srt_read_error"])

    def test_ملف_اكبر_من_الحد_يرفض(self):
        path = self.directory / "ملف_كبير.srt"
        with path.open("wb") as target:
            target.truncate(MAX_FILE_BYTES + 1)
        report = audit_srt(path, None)
        self.assertEqual(report["cue_count"], 0)
        self.assertEqual(self.codes(report), ["srt_too_large"])

    def test_ملف_فارغ_او_BOM_فقط(self):
        for content in ("", "\ufeff", " \n\n "):
            with self.subTest(content=repr(content)):
                path = self.write_srt(content)
                self.assertEqual(self.codes(audit_srt(path, None)), ["srt_empty"])


if __name__ == "__main__":
    unittest.main()
