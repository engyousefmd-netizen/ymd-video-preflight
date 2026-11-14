"""Read-only, dependency-free checks for UTF-8 SubRip subtitle files."""

from __future__ import annotations

import html
import re
import stat
from pathlib import Path


MAX_FILE_BYTES = 10 * 1024 * 1024

_TIMING = re.compile(
    r"^\s*(\d{2}):([0-5]\d):([0-5]\d),(\d{3})\s*-->\s*"
    r"(\d{2}):([0-5]\d):([0-5]\d),(\d{3})\s*$",
    re.ASCII,
)
_HTML_TAG = re.compile(r"</?[A-Za-z][^>]*>")
_BLOCK_BREAK = re.compile(r"\n[ \t]*\n(?:[ \t]*\n)*")


def _milliseconds(parts: tuple[str, ...]) -> int:
    hours, minutes, seconds, milliseconds = map(int, parts)
    return ((hours * 60 + minutes) * 60 + seconds) * 1000 + milliseconds


def audit_srt(
    path: Path,
    duration_seconds: float | None,
    max_chars_per_line: int = 42,
    max_cps: float = 20,
    max_lines: int = 2,
) -> dict:
    """Audit a subtitle file without changing it.

    ``cue_count`` counts nonempty subtitle blocks, including malformed ones.
    Issue cue numbers use the file's cue index, or the block's position when
    that index is absent/invalid. Character counts are approximate Unicode
    code-point counts after removing HTML tags and decoding HTML entities;
    CPS includes spaces within lines but excludes line breaks and padding.
    File, decoding and syntax errors are returned as ``fail`` issues.
    Readability, ordering and timeline checks are advisory ``warn`` issues.
    """
    path = Path(path)
    result = {"file": path.name, "cue_count": 0, "issues": []}

    def issue(code: str, severity: str, cue: int | None, message: str) -> None:
        result["issues"].append(
            {"code": code, "severity": severity, "cue": cue, "message": message}
        )

    def too_large() -> dict:
        issue(
            "srt_too_large", "fail", None,
            "Subtitle file exceeds the 10 MiB (10,485,760 bytes) limit.",
        )
        return result

    try:
        file_stat = path.stat()
        if not stat.S_ISREG(file_stat.st_mode):
            issue("srt_read_error", "fail", None, "Subtitle path is not a regular file.")
            return result
        if file_stat.st_size > MAX_FILE_BYTES:
            return too_large()
        # A bounded read also enforces the limit if the file grows after stat().
        with path.open("rb") as source:
            raw = source.read(MAX_FILE_BYTES + 1)
    except FileNotFoundError:
        issue("srt_file_missing", "fail", None, "Subtitle file was not found.")
        return result
    except OSError as exc:
        issue(
            "srt_read_error", "fail", None,
            f"Could not read subtitle file ({type(exc).__name__}).",
        )
        return result

    if len(raw) > MAX_FILE_BYTES:
        return too_large()
    try:
        text = raw.decode("utf-8-sig")
    except UnicodeDecodeError:
        issue(
            "srt_encoding", "fail", None,
            "Subtitle file is not valid UTF-8; save it as UTF-8 or UTF-8 with BOM.",
        )
        return result

    text = text.replace("\r\n", "\n").replace("\r", "\n")
    if not text.strip():
        issue("srt_empty", "fail", None, "Subtitle file contains no cues.")
        return result

    blocks = [block for block in _BLOCK_BREAK.split(text.strip("\n")) if block.strip()]
    result["cue_count"] = len(blocks)
    intervals: list[tuple[int, int, int, int]] = []
    previous_start: int | None = None
    previous_cue: int | None = None

    for position, block in enumerate(blocks, 1):
        lines = block.split("\n")
        first = lines[0].strip()
        cue = position
        timing_index = 1

        if first.isascii() and first.isdigit():
            try:
                cue = int(first)
            except ValueError:
                issue("srt_invalid_index", "fail", cue, "Cue index is too large to parse.")
            else:
                if cue < 1:
                    issue("srt_invalid_index", "fail", cue, "Cue index must be positive.")
        elif "-->" in first or re.match(r"\d{2}:", first, re.ASCII):
            timing_index = 0
            issue(
                "srt_missing_index", "warn", cue,
                "Cue index is missing; the block position is used for reporting.",
            )
        else:
            issue("srt_invalid_index", "fail", cue, "Cue index is missing or malformed.")

        if timing_index >= len(lines):
            issue("srt_missing_timestamp", "fail", cue, "Cue has no timing line.")
            continue

        timing_line = lines[timing_index].strip()
        timing = _TIMING.fullmatch(timing_line)
        if not timing:
            code = (
                "srt_malformed_timestamp"
                if "-->" in timing_line or ":" in timing_line
                else "srt_missing_timestamp"
            )
            issue(
                code, "fail", cue,
                "Expected a timing line in hh:mm:ss,mmm --> hh:mm:ss,mmm format.",
            )
            continue

        start_ms = _milliseconds(timing.groups()[:4])
        end_ms = _milliseconds(timing.groups()[4:])
        valid_interval = end_ms > start_ms
        if not valid_interval:
            issue(
                "srt_invalid_interval", "fail", cue,
                "Cue end time must be later than its start time.",
            )
        else:
            if previous_start is not None and start_ms < previous_start:
                issue(
                    "srt_out_of_order", "warn", cue,
                    f"Cue starts before the preceding cue {previous_cue}.",
                )
            previous_start, previous_cue = start_ms, cue
            intervals.append((start_ms, end_ms, cue, position))

        if duration_seconds is not None and end_ms / 1000 > duration_seconds + 1e-6:
            issue(
                "srt_beyond_video", "warn", cue,
                f"Cue ends at {end_ms / 1000:.3f}s, beyond the video duration "
                f"of {duration_seconds:.3f}s.",
            )

        visible_lines = [
            html.unescape(_HTML_TAG.sub("", line))
            for line in lines[timing_index + 1:]
        ]
        if not any(line.strip() for line in visible_lines):
            issue("srt_empty_text", "warn", cue, "Cue has no visible subtitle text.")
        if len(visible_lines) > max_lines:
            issue(
                "srt_too_many_lines", "warn", cue,
                f"Cue has {len(visible_lines)} lines; the configured limit is {max_lines}.",
            )
        for line_number, line in enumerate(visible_lines, 1):
            if len(line) > max_chars_per_line:
                issue(
                    "srt_line_too_long", "warn", cue,
                    f"Text line {line_number} has approximately {len(line)} characters; "
                    f"the configured limit is {max_chars_per_line}.",
                )

        if valid_interval:
            characters = sum(len(line.strip()) for line in visible_lines)
            cps = characters * 1000 / (end_ms - start_ms)
            if cps > max_cps:
                issue(
                    "srt_high_cps", "warn", cue,
                    f"Reading speed is approximately {cps:.1f} characters/second; "
                    f"the configured limit is {max_cps:g}.",
                )

    # Sort chronologically to avoid treating merely out-of-order, disjoint cues
    # as overlaps. Tracking the latest end also catches nested intervals.
    active_end = -1
    active_cue: int | None = None
    for start_ms, end_ms, cue, position in sorted(intervals, key=lambda item: (item[0], item[3])):
        if start_ms < active_end:
            issue("srt_overlap", "warn", cue, f"Cue overlaps cue {active_cue}.")
        if end_ms > active_end:
            active_end, active_cue = end_ms, cue

    return result
