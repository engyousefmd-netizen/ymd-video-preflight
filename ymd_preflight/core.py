"""Read-only ffprobe/FFmpeg analysis. No media upload or source mutation."""
from __future__ import annotations

from collections import Counter
from datetime import datetime, timezone
from fractions import Fraction
import hashlib
import json
import math
import os
from pathlib import Path
import re
import shutil
import subprocess
import tempfile

from . import __version__
from .profiles import Profile, validate_profile


class AnalysisError(RuntimeError):
    """A required operation could not be completed."""


def finite_float(value, default=None):
    try:
        result = float(value)
        return result if math.isfinite(result) else default
    except (TypeError, ValueError, OverflowError):
        return default


def rational(value, default=None):
    try:
        result = float(Fraction(str(value)))
        return result if math.isfinite(result) else default
    except (TypeError, ValueError, ZeroDivisionError, OverflowError):
        return default


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _run(args: list[str], timeout: float, max_output: int = 8_000_000):
    """Avoid shell interpolation; keep FFmpeg logs off stdout and bound reads."""
    env = os.environ.copy()
    env["LC_ALL"] = "C"
    try:
        with tempfile.TemporaryFile(mode="w+b") as out, tempfile.TemporaryFile(mode="w+b") as err:
            process = subprocess.run(args, stdin=subprocess.DEVNULL, stdout=out, stderr=err,
                                     timeout=timeout, check=False, env=env)
            out.seek(0)
            err.seek(0)
            raw_out, raw_err = out.read(max_output + 1), err.read(max_output + 1)
        if len(raw_out) > max_output or len(raw_err) > max_output:
            raise AnalysisError("Analysis output exceeded the safety limit; no complete result is available.")
        return process.returncode, raw_out.decode("utf-8", "replace"), raw_err.decode("utf-8", "replace")
    except subprocess.TimeoutExpired as exc:
        raise AnalysisError(f"Analysis exceeded its {timeout:g}-second timeout.") from exc
    except OSError as exc:
        raise AnalysisError(f"Could not run {Path(args[0]).name}: {exc.strerror or 'OS error'}") from exc


def _binary(name: str) -> str:
    binary = shutil.which(name)
    if not binary:
        raise AnalysisError(f"{name} was not found. Install FFmpeg and make ffmpeg/ffprobe available on PATH.")
    return binary


def _version(binary: str) -> str:
    rc, out, _ = _run([binary, "-version"], timeout=10)
    return out.splitlines()[0] if rc == 0 and out else "unavailable"


def probe_media(path: Path, timeout: float = 30) -> dict:
    binary = _binary("ffprobe")
    rc, out, _ = _run([binary, "-v", "error", "-protocol_whitelist", "file,pipe",
                      "-show_format", "-show_streams", "-of", "json", str(path)], timeout)
    if rc:
        raise AnalysisError("ffprobe could not read the local media file; it may be unsupported or damaged.")
    try:
        data = json.loads(out)
    except json.JSONDecodeError as exc:
        raise AnalysisError("ffprobe returned invalid metadata.") from exc
    if not isinstance(data, dict) or not isinstance(data.get("streams", []), list):
        raise AnalysisError("Unexpected ffprobe response.")
    return data


def choose_stream(streams: list[dict], kind: str):
    matches = [s for s in streams if s.get("codec_type") == kind
               and not (kind == "video" and s.get("disposition", {}).get("attached_pic"))]
    return next((s for s in matches if s.get("disposition", {}).get("default")), matches[0] if matches else None)


def summarize_video(stream: dict | None) -> dict | None:
    if stream is None:
        return None
    rotation = finite_float(stream.get("tags", {}).get("rotate"), 0.0)
    for side in stream.get("side_data_list", []):
        if "rotation" in side:
            rotation = finite_float(side["rotation"], rotation)
    rotation %= 360
    width, height = int(stream.get("width") or 0), int(stream.get("height") or 0)
    sar = rational(str(stream.get("sample_aspect_ratio", "1:1")).replace(":", "/"), 1.0)
    sar = sar if sar and sar > 0 else 1.0
    display_width, display_height = width * sar, float(height)
    if abs(rotation - 90) < 1 or abs(rotation - 270) < 1:
        display_width, display_height = display_height, display_width
    return {"codec": stream.get("codec_name", "unknown"), "width": width, "height": height,
            "display_width": round(display_width, 3), "display_height": round(display_height, 3),
            "fps": rational(stream.get("avg_frame_rate"), rational(stream.get("r_frame_rate"))),
            "pixel_format": stream.get("pix_fmt"), "rotation_degrees": rotation,
            "sample_aspect_ratio": sar, "stream_index": stream.get("index"),
            "duration_seconds": finite_float(stream.get("duration"))}


def summarize_audio(stream: dict | None) -> dict | None:
    if stream is None:
        return None
    return {"codec": stream.get("codec_name", "unknown"),
            "sample_rate": finite_float(stream.get("sample_rate")), "channels": stream.get("channels"),
            "integrated_lufs": None, "true_peak_dbfs": None, "loudness_range_lu": None,
            "stream_index": stream.get("index"), "duration_seconds": finite_float(stream.get("duration"))}


_NUMBER = r"[-+]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][-+]?\d+)?"


def parse_events(log: str, duration: float | None, profile: Profile) -> dict:
    events = {"black": [], "silence": [], "freeze": []}
    for match in re.finditer(rf"black_start:({_NUMBER})\s+black_end:({_NUMBER})\s+black_duration:({_NUMBER})", log):
        start, end, length = map(float, match.groups())
        if length + 0.001 >= profile.black_min_seconds:
            events["black"].append({"start": max(0, start), "end": end, "duration": length})
    for kind, prefix, min_duration in [
        ("silence", "silence", profile.silence_min_seconds),
        ("freeze", "freeze", profile.freeze_min_seconds),
    ]:
        start = None
        for match in re.finditer(rf"\b{prefix}_(start|end)\s*[:=]\s*({_NUMBER})", log):
            event, value = match.group(1), float(match.group(2))
            if event == "start":
                start = max(0.0, value)
            elif start is not None:
                end = min(value, duration) if duration is not None else value
                if end - start + 0.001 >= min_duration:
                    events[kind].append({"start": start, "end": end, "duration": end - start})
                start = None
        if start is not None and duration is not None and duration - start + 0.001 >= min_duration:
            events[kind].append({"start": start, "end": duration, "duration": duration - start,
                                 "open_at_end": True})
    for spans in events.values():
        for event in spans:
            for key in ("start", "end", "duration"):
                event[key] = round(event[key], 4)
    return events


def parse_loudness(log: str) -> dict:
    for match in reversed(list(re.finditer(r"\{[^{}]*\"input_i\"[^{}]*\}", log, re.DOTALL))):
        try:
            raw = json.loads(match.group(0))
            return {"integrated_lufs": finite_float(raw.get("input_i")),
                    "true_peak_dbfs": finite_float(raw.get("input_tp")),
                    "loudness_range_lu": finite_float(raw.get("input_lra")),
                    "integrated_lufs_raw": raw.get("input_i")}
        except json.JSONDecodeError:
            continue
    return {}


def scan_media(path: Path, video: dict | None, audio: dict | None, profile: Profile, timeout: float):
    binary = _binary("ffmpeg")
    args = [binary, "-hide_banner", "-nostdin", "-nostats", "-loglevel", "info",
            "-protocol_whitelist", "file,pipe", "-i", str(path)]
    if video:
        args += ["-map", f"0:{video['stream_index']}", "-vf",
                 f"blackdetect=d={profile.black_min_seconds}:pic_th={profile.black_picture_ratio}:pix_th={profile.black_pixel_threshold},"
                 f"freezedetect=n={profile.freeze_noise_ratio}:d={profile.freeze_min_seconds}"]
    else:
        args += ["-vn"]
    if audio:
        args += ["-map", f"0:{audio['stream_index']}", "-af",
                 f"silencedetect=n={profile.silence_noise_db}dB:d={profile.silence_min_seconds},"
                 f"loudnorm=I={profile.target_lufs}:TP={profile.max_true_peak_dbfs}:LRA=11:print_format=json"]
    else:
        args += ["-an"]
    args += ["-sn", "-dn", "-f", "null", "-"]
    rc, _, log = _run(args, timeout)
    if rc:
        raise AnalysisError("FFmpeg could not complete the full scan. Check the decoder/filter support or media integrity.")
    return log, _version(binary)


def analyze(path: Path, profile: Profile | None = None, subtitles: Path | None = None,
            metadata_only: bool = False, timeout: float = 300) -> dict:
    profile = validate_profile(profile or Profile())
    if not math.isfinite(timeout) or timeout <= 0:
        raise AnalysisError("Timeout must be a positive finite number.")
    path = path.expanduser().resolve()
    if not path.is_file():
        raise AnalysisError("Input must be an existing local media file.")
    if path.stat().st_size == 0:
        raise AnalysisError("Input file is empty.")
    before = path.stat()
    fingerprint = sha256_file(path)
    probe = probe_media(path, min(timeout, 30))
    streams = probe.get("streams", [])
    video = summarize_video(choose_stream(streams, "video"))
    audio = summarize_audio(choose_stream(streams, "audio"))
    durations = [finite_float(probe.get("format", {}).get("duration"))]
    durations += [s.get("duration_seconds") for s in [video, audio] if s]
    duration = next((v for v in durations if v is not None and v > 0), None)
    checks = []

    def add(check_id, status, title, message, value=None):
        checks.append({"id": check_id, "status": status, "title": title, "message": message, "value": value})

    add("video_present", "pass" if video else "fail", "Video stream", "Video stream found." if video else "No video stream found.")
    add("audio_present", "pass" if audio else "warn", "Audio stream", "Audio stream found." if audio else "No audio stream; confirm this is intentional.")
    add("duration", "pass" if duration is not None else "warn", "Duration", "Duration is readable." if duration else "Duration is unavailable; end-of-file checks are limited.", duration)
    if video:
        ratio = video["display_width"] / video["display_height"] if video["display_height"] else None
        expected = profile.expected_aspect_ratio
        if expected is not None:
            good = ratio is not None and abs(ratio / expected - 1) <= profile.aspect_tolerance
            add("aspect_ratio", "pass" if good else "warn", "Display aspect ratio",
                f"Display ratio {ratio or 0:.4f}; house target {expected:.4f}. Rotation and sample aspect ratio are included.", ratio)
        short_edge = min(video["width"], video["height"])
        add("resolution", "pass" if short_edge >= profile.min_short_edge else "warn", "Resolution",
            f"Encoded short edge {short_edge}px; house minimum {profile.min_short_edge}px.", short_edge)
        fps = video.get("fps")
        add("frame_rate", "pass" if fps and profile.min_fps <= fps <= profile.max_fps else "warn", "Average frame rate",
            f"Average frame rate {fps}; expected {profile.min_fps:g}–{profile.max_fps:g} fps. This is not a constant-frame-rate test.", fps)
        add("video_codec", "pass" if video["codec"] == "h264" else "info", "Video codec",
            f"Codec: {video['codec']}. H.264 is this tool's general handoff preference; other codecs may be appropriate.", video["codec"])
        if video.get("pixel_format") and "yuv420p" not in video["pixel_format"]:
            add("pixel_format", "info", "Pixel format", "Confirm that the intended player accepts this pixel format.", video["pixel_format"])
        if video["rotation_degrees"] not in (0, 90, 180, 270):
            add("rotation", "warn", "Rotation", "Non-right-angle rotation is present; aspect checks do not model its bounding box.", video["rotation_degrees"])
    if video and audio:
        vdur, adur = video.get("duration_seconds"), audio.get("duration_seconds")
        if vdur is not None and adur is not None:
            delta = abs(vdur - adur)
            add("av_duration", "warn" if delta > 0.25 else "pass", "Audio/video duration difference",
                f"Stream duration difference {delta:.3f}s. This does not measure lip-sync.", round(delta, 4))

    events = {"black": [], "silence": [], "freeze": []}
    warnings = []
    complete_scan = False
    versions = {"ffprobe": _version(_binary("ffprobe"))}
    if metadata_only:
        add("scan_complete", "warn", "Full scan", "Metadata-only mode: picture, silence, loudness and decode checks were not run.")
    elif not (video or audio):
        add("scan_complete", "fail", "Full scan", "No playable audio/video stream to analyze.")
    else:
        try:
            log, versions["ffmpeg"] = scan_media(path, video, audio, profile, timeout)
            events = parse_events(log, duration, profile)
            complete_scan = True
            add("scan_complete", "pass", "Full scan", "FFmpeg finished reading the selected streams.")
            decode_errors = re.findall(r"(?im)^.*(?:error while decoding|invalid data found|corrupt(?:ed)? (?:frame|packet)|decode_slice_header error).*$", log)
            if decode_errors:
                add("decode_integrity", "fail", "Decode integrity", "Decoder reported corrupt or invalid data; review the source.", len(decode_errors))
            else:
                add("decode_integrity", "pass", "Decode integrity", "No recognized decode-error messages were found; this is not a proof of flawless media.")
            for key, label in [("black", "Black segments"), ("silence", "Silence segments"), ("freeze", "Static/frozen segments")]:
                if (key == "silence" and not audio) or (key != "silence" and not video):
                    continue
                count = len(events[key])
                add(key + "_events", "warn" if count else "pass", label,
                    f"{count} interval(s) above the configured threshold. Review intentional pauses, fades and stills." if count else "No intervals above the configured threshold were reported.", count)
            if audio:
                measurements = parse_loudness(log)
                audio.update(measurements)
                loudness, peak = audio.get("integrated_lufs"), audio.get("true_peak_dbfs")
                if loudness is None:
                    add("loudness", "warn", "Integrated loudness", "No finite loudness reading; the audio may be silent or too short.")
                else:
                    good = abs(loudness - profile.target_lufs) <= profile.loudness_tolerance_lu
                    add("loudness", "pass" if good else "warn", "Integrated loudness",
                        f"Measured {loudness:.2f} LUFS; house target {profile.target_lufs:g} ± {profile.loudness_tolerance_lu:g} LU.", loudness)
                if peak is not None:
                    add("true_peak", "warn" if peak > profile.max_true_peak_dbfs else "pass", "True peak",
                        f"Measured {peak:.2f} dBTP; house ceiling {profile.max_true_peak_dbfs:g} dBTP.", peak)
                else:
                    add("true_peak", "warn", "True peak", "No finite true-peak measurement is available.")
        except AnalysisError as exc:
            warnings.append(str(exc))
            add("scan_complete", "fail", "Full scan", str(exc))

    subtitle_result = None
    if subtitles is not None:
        from .subtitles import audit_srt
        subtitle_result = audit_srt(Path(subtitles), duration,
                                    max_chars_per_line=profile.max_subtitle_chars_per_line,
                                    max_cps=profile.max_subtitle_cps, max_lines=profile.max_subtitle_lines)
        issues = subtitle_result.get("issues", [])
        severity = "fail" if any(i.get("severity") == "fail" for i in issues) else "warn" if issues else "pass"
        add("subtitles", severity, "SRT captions", f"{subtitle_result.get('cue_count', 0)} cues; {len(issues)} issue(s).", len(issues))
    after = path.stat()
    if (before.st_size, before.st_mtime_ns) != (after.st_size, after.st_mtime_ns):
        add("source_changed", "fail", "Source changed", "The source changed during analysis; rerun against a stable file.")
    counts = Counter(c["status"] for c in checks)
    status = "fail" if counts["fail"] else "warn" if counts["warn"] else "pass"
    return {
        "schema_version": "1.0", "tool": {"name": "YMD Video Preflight", "version": __version__},
        "generated_at": datetime.now(timezone.utc).isoformat(), "profile": profile.to_dict(),
        "source": {"name": path.name, "size_bytes": before.st_size, "duration_seconds": duration, "sha256": fingerprint},
        "video": video, "audio": audio, "checks": checks, "events": events, "subtitles": subtitle_result,
        "analysis": {"full_scan": complete_scan, "heuristic": True, "engine_versions": versions,
                     "warnings": warnings,
                     "limitations": ["House profiles are editable preferences, not official platform requirements.",
                                     "Black, silence and freeze detections are review cues; intentional stills, fades and pauses can trigger them.",
                                     "Only the selected primary video/audio streams are scanned. Captions are checked from an optional external SRT.",
                                     "No aesthetic, factual, legal, lip-sync, speech-recognition or caption-meaning verification is performed.",
                                     "A pass means configured checks completed without a flag; a person must review the delivery."]},
        "summary": {"status": status, "counts": {s: counts[s] for s in ["pass", "warn", "fail", "info"]}},
    }
