"""Dependency-free, offline HTML and Markdown presentation of preflight results.

The renderers accept the public report dictionary; absent or null fields are
displayed as unavailable. They never read media, fetch resources, or write files.
"""

from __future__ import annotations

from collections.abc import Mapping
from html import escape
import json
import math
import re
from typing import Any

__all__ = ["render_html", "render_markdown"]

_WORDS = {
    "en": {
        "title": "Video preflight report", "eyebrow": "BEFORE DELIVERY",
        "subtitle": "A technical review of the recorded checks and detected events.",
        "pass": "Passed", "warn": "Review", "fail": "Failed", "info": "Info",
        "state_pass": "Recorded checks passed", "state_warn": "Review recommended",
        "state_fail": "Issues require attention", "state_info": "Result unavailable",
        "summary": "Overview", "checks": "Checks", "video": "Video",
        "audio": "Audio", "events": "Detected events", "subtitles": "Subtitles",
        "analysis": "Analysis notes", "profile": "Profile", "source": "Source",
        "generated": "Generated", "duration": "Duration", "size": "File size",
        "scope": "Scan scope", "full_scan": "Full scan", "partial_scan": "Metadata only / incomplete",
        "unknown": "Not specified", "unavailable": "Not available",
        "human_title": "Human review is still required",
        "human_text": "Black frames, silence and frozen frames are heuristic detections. They may be intentional. Review the marked moments before making an editorial decision; this report is not a creative or delivery approval.",
        "check_name": "Check", "status": "Status", "detail": "Finding", "value": "Value",
        "no_checks": "No checks were included in this report.",
        "no_video": "No video stream details were provided.",
        "no_audio": "No audio stream details were provided.",
        "codec": "Codec", "resolution": "Display dimensions", "encoded_size": "Encoded dimensions",
        "fps": "Frame rate", "pixel_format": "Pixel format", "rotation": "Rotation",
        "sample_rate": "Sample rate", "channels": "Channels", "lufs": "Integrated loudness",
        "peak": "True peak", "lra": "Loudness range", "target_aspect": "Target aspect ratio",
        "target_lufs": "Loudness target", "tolerance": "Loudness tolerance",
        "black": "Black frames", "silence": "Silence", "freeze": "Frozen frames",
        "event_type": "Event", "start": "Start", "end": "End",
        "no_events": "No events were recorded. Check the scan scope and limitations below.",
        "events_missing": "Event data was not provided.",
        "events_hint": "Timestamps are hours:minutes:seconds.milliseconds from the start of the media.",
        "file": "File", "cues": "Cues", "cue": "Cue", "issues": "Issues",
        "no_subtitles": "No subtitle report was provided.",
        "no_subtitle_issues": "No subtitle issues were recorded.",
        "warnings": "Warnings", "limitations": "Limitations", "engines": "Analysis engines",
        "no_notes": "No additional analysis notes were provided.",
        "fingerprint": "Source SHA-256", "schema": "Report schema",
        "yes": "Yes", "no": "No", "heuristic": "Heuristic analysis",
        "all_pass": "No warnings or failures were recorded in the checks.",
        "more": "Additional entries are available in the HTML or JSON report.",
        "check_totals": "Check totals", "missing": "—",
    },
    "ar": {
        "title": "تقرير فحص الفيديو", "eyebrow": "قبل التسليم",
        "subtitle": "مراجعة تقنية لنتائج الفحوص والأحداث التي رصدها التحليل.",
        "pass": "اجتاز", "warn": "مراجعة", "fail": "لم يجتز", "info": "معلومة",
        "state_pass": "اجتاز الفحوص المسجلة", "state_warn": "يحتاج إلى مراجعة",
        "state_fail": "توجد مشكلات تتطلب المعالجة", "state_info": "النتيجة غير متاحة",
        "summary": "نظرة عامة", "checks": "الفحوص", "video": "الفيديو",
        "audio": "الصوت", "events": "الأحداث المرصودة", "subtitles": "الترجمة النصية",
        "analysis": "ملاحظات التحليل", "profile": "ملف الإعدادات", "source": "الملف المصدر",
        "generated": "وقت الإنشاء", "duration": "المدة", "size": "حجم الملف",
        "scope": "نطاق الفحص", "full_scan": "فحص كامل", "partial_scan": "بيانات أساسية / فحص غير كامل",
        "unknown": "غير محدد", "unavailable": "غير متاح",
        "human_title": "تظل المراجعة البشرية ضرورية",
        "human_text": "رصد الإطارات السوداء والصمت وثبات الصورة يعتمد على مؤشرات آلية، وقد تكون هذه المقاطع مقصودة. راجع التوقيتات المحددة قبل اتخاذ قرار تحريري؛ هذا التقرير لا يمثل اعتمادًا إبداعيًا أو موافقة على التسليم.",
        "check_name": "الفحص", "status": "الحالة", "detail": "النتيجة", "value": "القيمة",
        "no_checks": "لم تُدرج أي فحوص في هذا التقرير.",
        "no_video": "لم تُرفق تفاصيل مسار الفيديو.",
        "no_audio": "لم تُرفق تفاصيل مسار الصوت.",
        "codec": "الترميز", "resolution": "أبعاد العرض", "encoded_size": "الأبعاد المخزنة",
        "fps": "معدل الإطارات", "pixel_format": "تنسيق البكسل", "rotation": "الدوران",
        "sample_rate": "معدل أخذ العينات", "channels": "القنوات", "lufs": "جهارة الصوت المتكاملة",
        "peak": "الذروة الحقيقية", "lra": "نطاق الجهارة", "target_aspect": "نسبة الأبعاد المستهدفة",
        "target_lufs": "الجهارة المستهدفة", "tolerance": "هامش الجهارة",
        "black": "إطارات سوداء", "silence": "صمت", "freeze": "ثبات الصورة",
        "event_type": "الحدث", "start": "البداية", "end": "النهاية",
        "no_events": "لا توجد أحداث مسجلة. راجع نطاق الفحص وحدود التحليل أدناه.",
        "events_missing": "لم تُرفق بيانات الأحداث.",
        "events_hint": "التوقيتات بصيغة ساعات:دقائق:ثوانٍ.أجزاء من الثانية، محسوبة من بداية الملف.",
        "file": "الملف", "cues": "المقاطع النصية", "cue": "المقطع", "issues": "الملاحظات",
        "no_subtitles": "لم يُرفق تقرير للترجمة النصية.",
        "no_subtitle_issues": "لم تُسجل ملاحظات على الترجمة النصية.",
        "warnings": "تنبيهات", "limitations": "حدود التحليل", "engines": "محركات التحليل",
        "no_notes": "لم تُرفق ملاحظات إضافية للتحليل.",
        "fingerprint": "بصمة الملف SHA-256", "schema": "إصدار صيغة التقرير",
        "yes": "نعم", "no": "لا", "heuristic": "التحليل الاستدلالي",
        "all_pass": "لم تُسجل تنبيهات أو حالات إخفاق ضمن الفحوص.",
        "more": "بقية العناصر متاحة في تقرير HTML أو JSON.",
        "check_totals": "إجمالي الفحوص", "missing": "—",
    },
}

_CSS = """
:root{--ink:#182c35;--muted:#5f6e74;--line:#dce4e3;--paper:#fff;--bg:#f2f5f3;
--green:#155c4b;--green-bg:#e8f4ed;--amber:#7c480c;--amber-bg:#fff3d9;
--red:#9e313b;--red-bg:#fff0f0;--blue:#355d80;--blue-bg:#edf3fa}
*{box-sizing:border-box}html{scroll-behavior:smooth}body{margin:0;background:var(--bg);color:var(--ink);
font-family:system-ui,-apple-system,"Segoe UI",Tahoma,Arial,sans-serif;font-size:15px;line-height:1.65}
a{color:inherit}a:focus-visible{outline:3px solid #d6b359;outline-offset:5px}
.shell{max-width:1180px;margin:auto;padding:30px 28px 44px}.brandbar{display:flex;justify-content:space-between;
align-items:center;gap:18px;margin-bottom:22px}.brand{display:flex;align-items:center;gap:12px;font-weight:750;
letter-spacing:.02em}.mark{display:grid;place-items:center;width:48px;height:40px;background:var(--ink);
border-radius:10px;color:#d8ecc8;font-size:13px;letter-spacing:.12em}.brand small{display:block;font-size:11px;
font-weight:500;color:var(--muted);letter-spacing:.12em}.edition{font-size:12px;color:var(--muted)}
.hero{background:#17352f;color:#f4faf5;border-radius:22px;padding:34px 36px;position:relative;overflow:hidden}
.eyebrow{font-size:11px;font-weight:750;letter-spacing:.16em;color:#bfd8c6;margin:0 0 10px}
h1{font-size:clamp(27px,4vw,40px);line-height:1.3;margin:0 0 10px;font-weight:750;letter-spacing:-.025em}
.subtitle{margin:0;color:#c7d9d0;max-width:720px}.hero-bottom{display:flex;align-items:flex-end;justify-content:space-between;
gap:24px;margin-top:30px;padding-top:22px;border-top:1px solid #426056}.filename{font-weight:650;font-size:17px;
overflow-wrap:anywhere;word-break:break-word;margin:0 0 5px}.hero-meta{font-size:12px;color:#c7d9d0;overflow-wrap:anywhere}
.verdict{border:1px solid #587166;border-radius:12px;padding:11px 16px;max-width:100%;font-weight:650;
background:#29483f;flex-shrink:0}.verdict .dot{background:#cae5ba}.verdict.warn{background:#533d18;color:#ffe3a5;border-color:#86672d}
.verdict.warn .dot{background:#f4c365}.verdict.fail{background:#583035;color:#ffd1d5;border-color:#8b4a54}
.verdict.fail .dot{background:#f5a3ad}.verdict.info{background:#304651;color:#dcebf5;border-color:#5b7380}
.dot{display:inline-block;width:7px;height:7px;border-radius:50%;margin-inline-end:8px;vertical-align:middle}
.section-nav{display:flex;gap:7px;flex-wrap:wrap;padding:17px 0 23px}.section-nav a{text-decoration:none;
font-size:12px;padding:6px 12px;border:1px solid var(--line);background:#fff;border-radius:30px}
.section-nav a:hover{background:#e6eee7}.summary-grid{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:12px}
.stat{background:#fff;border:1px solid var(--line);border-radius:14px;padding:18px 20px;border-top:3px solid var(--line)}
.stat.pass{border-top-color:#368069}.stat.warn{border-top-color:#b87924}.stat.fail{border-top-color:#bb5262}
.stat.info{border-top-color:#6687a5}.stat strong{font-size:31px;line-height:1.25;display:block;font-variant-numeric:tabular-nums}
.stat span{color:var(--muted);font-size:12px}.review-banner{display:flex;gap:14px;align-items:flex-start;background:var(--amber-bg);
border:1px solid #ecd8a9;border-radius:14px;padding:18px 21px;margin:20px 0 26px}.review-icon{border:1.5px solid #926324;
color:#7c480c;min-width:25px;height:25px;border-radius:50%;text-align:center;font-weight:800;line-height:22px;margin-top:3px}
.review-banner h2{font-size:14px;color:#71430d;margin:0 0 4px}.review-banner p{font-size:13px;color:#785624;margin:0;max-width:940px}
section{scroll-margin-top:20px}.section-heading{display:flex;align-items:baseline;justify-content:space-between;gap:16px;
margin:26px 0 12px}.section-heading h2{font-size:19px;margin:0;letter-spacing:-.015em}.section-heading small{font-size:11px;
font-weight:600;letter-spacing:.08em;color:var(--muted);direction:ltr;unicode-bidi:isolate}.panel{background:var(--paper);
border:1px solid var(--line);border-radius:16px;overflow:hidden}.panel-pad{padding:23px}.facts{display:grid;
grid-template-columns:repeat(4,minmax(0,1fr));margin:0;gap:0}.fact{padding:17px 20px;min-width:0}
.fact dt{font-size:12px;color:var(--muted);margin-bottom:4px}.fact dd{margin:0;font-size:15px;font-weight:600;overflow-wrap:anywhere}
.facts.compact{grid-template-columns:repeat(2,minmax(0,1fr))}.facts.compact .fact{padding:15px 20px;border-bottom:1px solid #edf1ef}
.columns{display:grid;grid-template-columns:1fr 1fr;gap:22px}.table-wrap{overflow-x:auto}table{border-collapse:collapse;width:100%;
text-align:start;font-size:13px}th{background:#f7f9f7;color:#63716f;font-size:11px;font-weight:650;padding:12px 18px;
text-align:start;border-bottom:1px solid var(--line)}td{padding:15px 18px;border-bottom:1px solid #e8eeea;vertical-align:top;
overflow-wrap:anywhere}tr:last-child td{border-bottom:0}.check-title{font-weight:650;margin-bottom:3px}.check-id{font-size:10px;
color:#6d7c78;overflow-wrap:anywhere}.check-detail{min-width:180px;max-width:520px;white-space:pre-wrap;unicode-bidi:plaintext}
.badge{display:inline-flex;align-items:center;font-size:11px;font-weight:700;border-radius:6px;padding:4px 9px;white-space:nowrap;
background:var(--blue-bg);color:var(--blue)}.badge.pass{background:var(--green-bg);color:var(--green)}
.badge.warn{background:var(--amber-bg);color:var(--amber)}.badge.fail{background:var(--red-bg);color:var(--red)}
.badge.info{background:var(--blue-bg);color:var(--blue)}.mono{font-family:ui-monospace,SFMono-Regular,Consolas,"Liberation Mono",monospace;
font-variant-numeric:tabular-nums;font-size:.92em;overflow-wrap:anywhere}.technical{direction:ltr;unicode-bidi:isolate;display:inline-block;
max-width:100%;overflow-wrap:anywhere}.value{max-width:260px;white-space:pre-wrap;unicode-bidi:plaintext}
.empty{padding:25px;color:var(--muted);font-size:13px;margin:0}.event-summary{display:flex;gap:10px;flex-wrap:wrap;padding:18px 20px;
border-bottom:1px solid var(--line)}.event-chip{display:flex;align-items:center;gap:9px;background:#f1f5f2;border-radius:8px;
padding:7px 12px;font-size:12px}.event-chip strong{font-size:16px;line-height:1.3}.event-chip.black{background:#edf0f1;color:#35474e}
.event-chip.silence{background:#eaf3f4;color:#2b6772}.event-chip.freeze{background:#f3eef8;color:#684a85}
.hint{padding:0 20px 15px;margin:0;color:var(--muted);font-size:11px}.notes{display:grid;grid-template-columns:1fr 1fr;gap:22px}
.note-block h3{font-size:13px;margin:0 0 8px}.note-block ul{margin:0;padding-inline-start:20px;color:var(--muted);font-size:13px}
.note-block li+li{margin-top:6px}.provenance{display:flex;flex-wrap:wrap;gap:10px 26px;padding-top:20px;margin-top:20px;
border-top:1px solid var(--line);font-size:11px;color:var(--muted)}.provenance>div{max-width:100%;overflow-wrap:anywhere}
.hash{margin-top:16px;padding-top:14px;border-top:1px solid var(--line);font-size:11px;color:var(--muted)}
.hash code{display:block;margin-top:4px;word-break:break-all}.footer{margin-top:24px;display:flex;justify-content:space-between;gap:18px;
color:#708078;font-size:11px}.sr-only{position:absolute;width:1px;height:1px;padding:0;margin:-1px;overflow:hidden;clip:rect(0,0,0,0);
white-space:nowrap;border:0}
@media(max-width:760px){.shell{padding:18px 16px 30px}.hero{padding:26px 23px}.hero-bottom{align-items:flex-start;flex-direction:column;
gap:16px}.verdict{flex-shrink:1}.summary-grid{grid-template-columns:repeat(2,minmax(0,1fr))}.facts{grid-template-columns:repeat(2,minmax(0,1fr))}
.columns,.notes{grid-template-columns:1fr;gap:0}.brandbar{align-items:flex-start}.edition{max-width:120px;text-align:end}
th,td{padding:12px}.section-heading small{font-size:9px}.check-detail{min-width:150px}.footer{flex-wrap:wrap}}
@media print{@page{size:A4;margin:14mm}html{scroll-behavior:auto}body{background:#fff;font-size:10pt;color:#182c35}
.shell{max-width:none;padding:0}.brandbar{margin-bottom:12px}.hero{padding:20px;border:1px solid #9ead9f;background:#fff!important;
color:#182c35;border-radius:10px}.hero .subtitle,.hero-meta,.eyebrow{color:#536258}.hero-bottom{border-color:#dce4e3;margin-top:16px;
padding-top:14px}.verdict,.verdict.warn,.verdict.fail,.verdict.info{color:#182c35;background:#fff;border-color:#7d8a80}
.section-nav{display:none}.summary-grid{margin-top:18px;gap:8px}.stat{padding:12px;border-radius:8px}.stat strong{font-size:23px}
.review-banner{margin:16px 0;padding:12px}.section-heading{margin-top:20px;break-after:avoid}.section-heading h2{font-size:14pt}
.panel{border-radius:7px;overflow:visible}.table-wrap{overflow:visible}table{font-size:9pt;table-layout:fixed}thead{display:table-header-group}
th,td{padding:8px;word-break:break-word}.check-detail{min-width:0}.badge{white-space:normal;font-size:8pt}.event-summary{padding:12px}
.fact{padding:12px}.facts.compact .fact{padding:10px}.facts dd{font-size:11pt}.columns{gap:16px}.review-banner,.stat,tr,.fact,.note-block{
break-inside:avoid}h1{font-size:25pt}.panel-pad{padding:16px}.footer{font-size:8pt}a{text-decoration:none}.hint{font-size:8pt}
*{-webkit-print-color-adjust:exact;print-color-adjust:exact}}
"""


def _language(language: str) -> str:
    return "ar" if str(language).lower().replace("_", "-").split("-")[0] == "ar" else "en"


def _mapping(value: Any) -> Mapping:
    return value if isinstance(value, Mapping) else {}


def _records(value: Any) -> list[Mapping]:
    return [item for item in value if isinstance(item, Mapping)] if isinstance(value, (list, tuple)) else []


def _number(value: Any) -> float | None:
    if isinstance(value, bool) or value is None:
        return None
    try:
        result = float(value)
    except (ValueError, TypeError, OverflowError):
        return None
    return result if math.isfinite(result) else None


def _plain(value: Any, words: dict[str, str]) -> str:
    if value is None:
        return words["missing"]
    if isinstance(value, bool):
        return words["yes"] if value else words["no"]
    if isinstance(value, float):
        if not math.isfinite(value):
            return words["missing"]
        return f"{value:.4f}".rstrip("0").rstrip(".")
    if isinstance(value, (dict, list, tuple)):
        return json.dumps(value, ensure_ascii=False, default=str)
    return str(value)


def _html(value: Any, words: dict[str, str]) -> str:
    return escape(_plain(value, words), quote=True)


def _md(value: Any, words: dict[str, str]) -> str:
    text = escape(_plain(value, words), quote=False).replace("\r", " ").replace("\n", " · ")
    return re.sub(r"([\\`*_{}\[\]|])", r"\\\1", text)


def _name(value: Any, fallback: str) -> str:
    if value is None or not str(value).strip():
        return fallback
    # A report may be shared with a client: never expose its source directory.
    return str(value).replace("\\", "/").rstrip("/").rsplit("/", 1)[-1] or fallback


def _timestamp(value: Any, words: dict[str, str]) -> str:
    seconds = _number(value)
    if seconds is None or seconds < 0:
        return words["missing"]
    milliseconds = round(seconds * 1000) if seconds < 1e12 else None
    if milliseconds is None:
        return words["missing"]
    hours, remainder = divmod(milliseconds, 3_600_000)
    minutes, remainder = divmod(remainder, 60_000)
    seconds_whole, fraction = divmod(remainder, 1000)
    return f"{hours:02d}:{minutes:02d}:{seconds_whole:02d}.{fraction:03d}"


def _size(value: Any, words: dict[str, str]) -> str:
    number = _number(value)
    if number is None or number < 0:
        return words["missing"]
    for unit in ("B", "KiB", "MiB", "GiB", "TiB"):
        if number < 1024 or unit == "TiB":
            return f"{number:,.0f} {unit}" if unit == "B" else f"{number:,.2f} {unit}"
        number /= 1024
    return words["missing"]


def _unit(value: Any, unit: str, words: dict[str, str]) -> str:
    number = _number(value)
    return f"{_plain(number, words)} {unit}" if number is not None else words["missing"]


def _dimensions(width: Any, height: Any, words: dict[str, str]) -> str:
    w, h = _number(width), _number(height)
    if w is None or h is None or w <= 0 or h <= 0:
        return words["missing"]
    return f"{_plain(w, words)} × {_plain(h, words)}"


def _status(value: Any) -> str:
    return value if isinstance(value, str) and value in ("pass", "warn", "fail", "info") else "info"


def _state(report: Mapping, checks: list[Mapping]) -> tuple[str, dict[str, int]]:
    summary = _mapping(report.get("summary"))
    declared = _mapping(summary.get("counts"))
    counts = {key: sum(_status(check.get("status")) == key for check in checks)
              for key in ("pass", "warn", "fail", "info")}
    for key in counts:
        count = _number(declared.get(key))
        if count is not None and count >= 0 and count.is_integer():
            counts[key] = int(count)
    state = summary.get("status")
    if state not in ("pass", "warn", "fail", "info"):
        state = "fail" if counts["fail"] else "warn" if counts["warn"] else "pass" if counts["pass"] else "info"
    return state, counts


def _scope(analysis: Mapping, words: dict[str, str]) -> str:
    full = analysis.get("full_scan")
    return words["full_scan"] if full is True else words["partial_scan"] if full is False else words["unknown"]


def _badge(status: Any, words: dict[str, str]) -> str:
    status = _status(status)
    return f'<span class="badge {status}">{words[status]}</span>'


def _facts(items: list[tuple[str, Any]], words: dict[str, str], compact: bool = False) -> str:
    cells = "".join(
        f'<div class="fact"><dt>{_html(label, words)}</dt>'
        f'<dd><bdi>{_html(value, words)}</bdi></dd></div>' for label, value in items
    )
    return f'<dl class="facts{" compact" if compact else ""}">{cells}</dl>'


def _heading(key: str, words: dict[str, str], language: str) -> str:
    secondary = f'<small lang="en">{_WORDS["en"][key].upper()}</small>' if language == "ar" else ""
    return f'<div class="section-heading"><h2 id="heading-{key}">{words[key]}</h2>{secondary}</div>'


def _table(headers: list[str], rows: list[str], caption: str) -> str:
    head = "".join(f'<th scope="col">{escape(item)}</th>' for item in headers)
    return (f'<div class="table-wrap"><table><caption class="sr-only">{escape(caption)}</caption>'
            f'<thead><tr>{head}</tr></thead><tbody>{"".join(rows)}</tbody></table></div>')


def _media_facts(report: Mapping, words: dict[str, str]) -> tuple[list, list]:
    video, audio = _mapping(report.get("video")), _mapping(report.get("audio"))
    display_width = video.get("display_width") if video.get("display_width") is not None else video.get("width")
    display_height = video.get("display_height") if video.get("display_height") is not None else video.get("height")
    video_items = [
        (words["codec"], video.get("codec")),
        (words["resolution"], _dimensions(display_width, display_height, words)),
        (words["encoded_size"], _dimensions(video.get("width"), video.get("height"), words)),
        (words["fps"], _unit(video.get("fps"), "fps", words)),
        (words["pixel_format"], video.get("pixel_format")),
        (words["rotation"], _unit(video.get("rotation_degrees"), "°", words)),
    ]
    audio_items = [
        (words["codec"], audio.get("codec")),
        (words["sample_rate"], _unit(audio.get("sample_rate"), "Hz", words)),
        (words["channels"], audio.get("channels")),
        (words["lufs"], _unit(audio.get("integrated_lufs"), "LUFS", words)),
        (words["peak"], _unit(audio.get("true_peak_dbfs"), "dBFS", words)),
        (words["lra"], _unit(audio.get("loudness_range_lu"), "LU", words)),
    ]
    return video_items, audio_items


def _event_rows(report: Mapping) -> list[tuple[str, Mapping]]:
    events = _mapping(report.get("events"))
    rows = [(kind, event) for kind in ("black", "silence", "freeze") for event in _records(events.get(kind))]
    return sorted(rows, key=lambda item: (_number(item[1].get("start")) is None,
                                         _number(item[1].get("start")) or 0, item[0]))


def _event_duration(event: Mapping) -> Any:
    if event.get("duration") is not None:
        return event.get("duration")
    start, end = _number(event.get("start")), _number(event.get("end"))
    return max(0.0, end - start) if start is not None and end is not None and end >= start else None


def _notes(value: Any) -> list[Any]:
    if value is None:
        return []
    return list(value) if isinstance(value, (tuple, list)) else [value]


def render_html(report: dict, language: str = "ar") -> str:
    """Return a complete self-contained, script-free HTML report.

    Arabic uses RTL layout; values use bidirectional isolation. Only basenames
    are shown for the source and subtitle file. Dynamic text is HTML-escaped.
    """
    report = _mapping(report)
    language = _language(language)
    words = _WORDS[language]
    source = _mapping(report.get("source"))
    profile = _mapping(report.get("profile"))
    analysis = _mapping(report.get("analysis"))
    tool = _mapping(report.get("tool"))
    checks = _records(report.get("checks"))
    state, counts = _state(report, checks)
    filename = _name(source.get("name"), words["unknown"])
    tool_name = tool.get("name") or "YMD Video Preflight"
    nav_keys = ("summary", "checks", "video", "audio", "events", "subtitles", "analysis")
    nav = "".join(f'<a href="#{key}">{words[key]}</a>' for key in nav_keys)
    stats = "".join(f'<div class="stat {key}"><strong>{counts[key]}</strong><span>{words[key]}</span></div>'
                    for key in ("pass", "warn", "fail", "info"))
    overview = _facts([
        (words["duration"], _timestamp(source.get("duration_seconds"), words)),
        (words["size"], _size(source.get("size_bytes"), words)),
        (words["profile"], profile.get("name")), (words["scope"], _scope(analysis, words)),
        (words["target_aspect"], profile.get("expected_aspect_ratio")),
        (words["target_lufs"], _unit(profile.get("target_lufs"), "LUFS", words)),
        (words["tolerance"], _unit(profile.get("loudness_tolerance_lu"), "LU", words)),
        (words["heuristic"], analysis.get("heuristic")),
    ], words)

    check_rows = []
    for check in checks:
        check_rows.append(
            f'<tr><td>{_badge(check.get("status"), words)}</td>'
            f'<td><div class="check-title" dir="auto">{_html(check.get("title") or check.get("id"), words)}</div>'
            f'<div class="check-id mono"><bdi>{_html(check.get("id"), words)}</bdi></div></td>'
            f'<td class="check-detail">{_html(check.get("message"), words)}</td>'
            f'<td class="value mono"><bdi>{_html(check.get("value"), words)}</bdi></td></tr>'
        )
    check_content = _table([words["status"], words["check_name"], words["detail"], words["value"]], check_rows, words["checks"]) if check_rows else f'<p class="empty">{words["no_checks"]}</p>'
    media = _media_facts(report, words)
    media_html = ""
    for index, key in enumerate(("video", "audio")):
        content = _facts(media[index], words, compact=True) if _mapping(report.get(key)) else f'<p class="empty">{words["no_" + key]}</p>'
        media_html += f'<section id="{key}" aria-labelledby="heading-{key}">{_heading(key, words, language)}<div class="panel">{content}</div></section>'

    event_data = _mapping(report.get("events"))
    event_counts = "".join(
        f'<div class="event-chip {kind}"><strong>{len(_records(event_data.get(kind))) if isinstance(event_data.get(kind), (list, tuple)) else words["missing"]}</strong><span>{words[kind]}</span></div>'
        for kind in ("black", "silence", "freeze")
    )
    event_rows = []
    for kind, event in _event_rows(report):
        cells = "".join(f'<td><span class="technical mono">{_timestamp(value, words)}</span></td>' for value in (event.get("start"), event.get("end"), _event_duration(event)))
        event_rows.append(f'<tr><td>{words[kind]}</td>{cells}</tr>')
    event_content = _table([words["event_type"], words["start"], words["end"], words["duration"]], event_rows, words["events"]) if event_rows else f'<p class="empty">{words["no_events"] if isinstance(report.get("events"), Mapping) else words["events_missing"]}</p>'

    subtitles = _mapping(report.get("subtitles"))
    if subtitles:
        subtitle_content = _facts([
            (words["file"], _name(subtitles.get("file"), words["unknown"])),
            (words["cues"], subtitles.get("cue_count")),
        ], words, compact=True)
        subtitle_rows = [
            f'<tr><td>{_badge(issue.get("severity"), words)}</td><td><bdi>{_html(issue.get("cue"), words)}</bdi></td>'
            f'<td><div class="check-detail">{_html(issue.get("message"), words)}</div>'
            f'<div class="check-id mono"><bdi>{_html(issue.get("code"), words)}</bdi></div></td></tr>'
            for issue in _records(subtitles.get("issues"))
        ]
        subtitle_content += _table([words["status"], words["cue"], words["detail"]], subtitle_rows, words["subtitles"]) if subtitle_rows else f'<p class="empty">{words["no_subtitle_issues"]}</p>'
    else:
        subtitle_content = f'<p class="empty">{words["no_subtitles"]}</p>'

    notes = ""
    for key in ("warnings", "limitations"):
        items = _notes(analysis.get(key))
        if items:
            entries = "".join(f'<li dir="auto">{_html(item, words)}</li>' for item in items)
            notes += f'<div class="note-block"><h3>{words[key]}</h3><ul>{entries}</ul></div>'
    if not notes:
        notes = f'<p class="empty">{words["no_notes"]}</p>'
    engines = "".join(f'<div><span class="mono"><bdi>{_html(key, words)}</bdi></span>: <bdi>{_html(value, words)}</bdi></div>'
                      for key, value in _mapping(analysis.get("engine_versions")).items())
    provenance = f'<div class="provenance" aria-label="{words["engines"]}">{engines}</div>' if engines else ""
    fingerprint = f'<div class="hash">{words["fingerprint"]}<code class="technical">{_html(source.get("sha256"), words)}</code></div>' if source.get("sha256") else ""
    direction = "rtl" if language == "ar" else "ltr"
    return f'''<!doctype html>
<html lang="{language}" dir="{direction}">
<head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<meta http-equiv="Content-Security-Policy" content="default-src 'none'; style-src 'unsafe-inline'; base-uri 'none'; form-action 'none'">
<meta name="color-scheme" content="light">
<title>{_html(filename, words)} · {_html(tool_name, words)}</title><style>{_CSS}</style></head>
<body><main class="shell">
<header class="brandbar"><div class="brand"><span class="mark" dir="ltr">YMD</span><div><bdi>{_html(tool_name, words)}</bdi><small lang="en" dir="ltr">VIDEO · AUDIO · CAPTIONS</small></div></div><div class="edition"><bdi>{_html(tool.get("version"), words)}</bdi></div></header>
<div class="hero"><p class="eyebrow">{words["eyebrow"]}</p><h1>{words["title"]}</h1><p class="subtitle">{words["subtitle"]}</p>
<div class="hero-bottom"><div><p class="filename"><bdi>{_html(filename, words)}</bdi></p><div class="hero-meta">{words["generated"]}: <bdi>{_html(report.get("generated_at"), words)}</bdi></div></div><div class="verdict {state}"><span class="dot" aria-hidden="true"></span>{words["state_" + state]}</div></div></div>
<nav class="section-nav" aria-label="{words["summary"]}">{nav}</nav>
<section id="summary" aria-labelledby="heading-summary"><h2 class="sr-only" id="heading-summary">{words["summary"]}</h2><div class="summary-grid" aria-label="{words["check_totals"]}">{stats}</div>
<aside class="review-banner"><span class="review-icon" aria-hidden="true">!</span><div><h2>{words["human_title"]}</h2><p>{words["human_text"]}</p></div></aside><div class="panel">{overview}</div></section>
<section id="checks" aria-labelledby="heading-checks">{_heading("checks", words, language)}<div class="panel">{check_content}</div></section>
<div class="columns">{media_html}</div>
<section id="events" aria-labelledby="heading-events">{_heading("events", words, language)}<div class="panel"><div class="event-summary">{event_counts}</div>{event_content}<p class="hint">{words["events_hint"]}</p></div></section>
<section id="subtitles" aria-labelledby="heading-subtitles">{_heading("subtitles", words, language)}<div class="panel">{subtitle_content}</div></section>
<section id="analysis" aria-labelledby="heading-analysis">{_heading("analysis", words, language)}<div class="panel panel-pad"><div class="notes">{notes}</div>{provenance}{fingerprint}</div></section>
<footer class="footer"><span><bdi>{_html(tool_name, words)}</bdi></span><span>{words["schema"]}: <bdi>{_html(report.get("schema_version"), words)}</bdi></span></footer>
</main></body></html>'''


def render_markdown(report: dict, language: str = "ar") -> str:
    """Return a concise Markdown summary; full event/issue detail stays in HTML.

    Raw HTML and Markdown metacharacters from report fields are escaped. Event
    and subtitle lists are limited to twenty entries with an explicit notice.
    """
    report = _mapping(report)
    language = _language(language)
    words = _WORDS[language]
    source = _mapping(report.get("source"))
    profile = _mapping(report.get("profile"))
    analysis = _mapping(report.get("analysis"))
    checks = _records(report.get("checks"))
    state, counts = _state(report, checks)
    md = lambda value: _md(value, words)
    lines = [f'# {words["title"]}', "",
             f'**{md(_name(source.get("name"), words["unknown"]))}** — {words["state_" + state]}', "",
             f'> **{words["human_title"]}.** {words["human_text"]}', "",
             f'## {words["summary"]}', ""]
    overview = [
        (words["generated"], report.get("generated_at")),
        (words["profile"], profile.get("name")),
        (words["duration"], _timestamp(source.get("duration_seconds"), words)),
        (words["size"], _size(source.get("size_bytes"), words)),
        (words["scope"], _scope(analysis, words)),
    ]
    lines.extend(f'- **{label}:** {md(value)}' for label, value in overview)
    lines.extend(["", " · ".join(f'{words[key]}: **{counts[key]}**' for key in ("pass", "warn", "fail", "info")), "",
                  f'## {words["checks"]}', ""])
    findings = [check for check in checks if _status(check.get("status")) != "pass"]
    if findings:
        lines.extend([f'| {words["status"]} | {words["check_name"]} | {words["detail"]} |', '| --- | --- | --- |'])
        for check in findings:
            lines.append(f'| {words[_status(check.get("status"))]} | {md(check.get("title") or check.get("id"))} | {md(check.get("message"))} |')
    else:
        lines.append(words["all_pass"] if checks else words["no_checks"])
    for key, items in zip(("video", "audio"), _media_facts(report, words)):
        lines.extend(["", f'## {words[key]}', ""])
        if _mapping(report.get(key)):
            lines.extend(f'- **{label}:** {md(value)}' for label, value in items)
        else:
            lines.append(words["no_" + key])
    lines.extend(["", f'## {words["events"]}', ""])
    events = _event_rows(report)
    if events:
        lines.extend([f'| {words["event_type"]} | {words["start"]} | {words["end"]} | {words["duration"]} |', '| --- | --- | --- | --- |'])
        for kind, event in events[:20]:
            lines.append(f'| {words[kind]} | {_timestamp(event.get("start"), words)} | {_timestamp(event.get("end"), words)} | {_timestamp(_event_duration(event), words)} |')
        if len(events) > 20:
            lines.extend(["", words["more"]])
    else:
        lines.append(words["no_events"] if isinstance(report.get("events"), Mapping) else words["events_missing"])
    subtitles = _mapping(report.get("subtitles"))
    lines.extend(["", f'## {words["subtitles"]}', ""])
    if subtitles:
        lines.append(f'{words["file"]}: **{md(_name(subtitles.get("file"), words["unknown"]))}** · {words["cues"]}: **{md(subtitles.get("cue_count"))}**')
        issues = _records(subtitles.get("issues"))
        lines.append("")
        if issues:
            lines.extend(f'- **{words[_status(issue.get("severity"))]} · {words["cue"]} {md(issue.get("cue"))}:** {md(issue.get("message"))}' for issue in issues[:20])
            if len(issues) > 20:
                lines.extend(["", words["more"]])
        else:
            lines.append(words["no_subtitle_issues"])
    else:
        lines.append(words["no_subtitles"])
    lines.extend(["", f'## {words["analysis"]}', ""])
    has_notes = False
    for key in ("warnings", "limitations"):
        for note in _notes(analysis.get(key)):
            has_notes = True
            lines.append(f'- **{words[key]}:** {md(note)}')
    if not has_notes:
        lines.append(words["no_notes"])
    return "\n".join(lines).rstrip() + "\n"
