# YMD Video Preflight

[![Tests](https://github.com/engyousefmd-netizen/ymd-video-preflight/actions/workflows/tests.yml/badge.svg)](https://github.com/engyousefmd-netizen/ymd-video-preflight/actions/workflows/tests.yml)

**Local video delivery checks with Arabic and English reports.**

[دليل عربي](README.ar.md) · [How the checks work](docs/CHECKS.md) · [Beta testing guide](docs/FIELD_TESTING.md) · [Contributing](CONTRIBUTING.md)

An early-stage, MIT-licensed command-line tool for small video-editing teams. It turns FFmpeg measurements and SRT checks into a timestamped review report, without uploading footage or changing the source file.

Version **0.1.0** is an initial implementation. The supplied demonstration uses synthetic media; real-world feedback and maintainer review are welcome.

## What it does

- Reads the selected video/audio streams, display orientation, dimensions, frame rate, and codecs.
- Scans for black segments, silence, and static/frozen segments, with start/end timestamps.
- Measures integrated audio loudness and true peak from FFmpeg's input statistics.
- Checks optional UTF-8 SRT captions for malformed timing, overlaps, captions beyond the video, long lines, and fast reading.
- Writes self-contained **HTML**, **JSON**, and **Markdown** reports, with Arabic/RTL or English layouts.
- Supports editable house profiles and useful exit codes for automation.

Detections are review cues. A still frame, fade or pause can be intentional. The tool does not judge editing quality, transcribe speech, verify caption meaning, measure lip-sync, or certify a file for a social platform.

## Requirements

- Python **3.10+**.
- FFmpeg and ffprobe available on `PATH`, including `blackdetect`, `freezedetect`, `silencedetect`, and `loudnorm` filters.
- A local, self-contained media file. Network protocols are disabled for analysis.

There are no third-party Python runtime dependencies. The demonstration generator also requires the FFmpeg `libx264` encoder; scanning does not require this encoder.

Get FFmpeg from [the official download page](https://ffmpeg.org/download.html). Get Python from [python.org](https://www.python.org/downloads/). Installation and updates of these tools are separate from this project.

## Quick start

From the extracted project directory, no package installation is necessary:

```bash
python3 -m ymd_preflight "final-video.mp4" --profile vertical-social --srt "captions.srt" --output reports/first-review --language ar
```

On Windows, use `py -m ymd_preflight` if your Python launcher is `py`.

Open `reports/first-review/report.html` in a browser. This report has no external scripts, fonts or services. To install a command:

```bash
python3 -m pip install .
ymd-preflight "final-video.mp4" --output reports/review --language en
```

Available built-in profiles: `general`, `vertical-social`, `landscape`, `square`.
These are **house preferences**, not official YouTube, Instagram, TikTok or broadcast specifications. For example, the vertical profile expects a 9:16 display ratio; the default audio target is -16 LUFS ±2 LU with a -1 dBTP ceiling. Override them for the actual delivery brief:

```bash
python3 -m ymd_preflight "clip.mov" --profile-json examples/custom-profile.json --output reports/custom
```

## Try the reproducible demonstration

The package includes an example report under `examples/demo-report`. Its source is explicitly synthetic: eight seconds of generated test pictures and tone, with a deliberate black interval near 2 seconds, an audio pause, static frames, and caption problems.

Regenerate fresh media and a fresh report:

```bash
python3 scripts/make_demo.py examples/new-media
python3 -m ymd_preflight examples/new-media/synthetic-review.mp4 --profile vertical-social --srt examples/new-media/captions.srt --output reports/demo --fail-on never
```

The deliberately low 360×640 fixture also triggers the default 720-pixel short-edge preference. An alert in this demonstration is expected; it is not a claim about any client's work.

## Help validate it with real-world edits

**Independent editor feedback is welcome.** Please try the tool only on media that you own or are authorized to test. Start with the [8-second synthetic sample](examples/media/synthetic-review.mp4) and its [example report](examples/demo-report/report.html), then follow the [short field-testing checklist](docs/FIELD_TESTING.md). If something is misleading or broken, [open a field-feedback issue](https://github.com/engyousefmd-netizen/ymd-video-preflight/issues/new/choose). You can share timestamps, versions and a synthetic reproducer without sharing customer footage.

The current release is **early-stage**. The original validation used synthetic fixtures on Linux. A later [GitHub Actions run passed on Linux, Windows and macOS](https://github.com/engyousefmd-netizen/ymd-video-preflight/actions/runs/43711109502), although independent real-editor testing remains outstanding. **No independent usage, downloads, or production reliability are claimed.** Track real [beta-testing feedback](https://github.com/engyousefmd-netizen/ymd-video-preflight/issues/1) and [cross-platform validation](https://github.com/engyousefmd-netizen/ymd-video-preflight/issues/2).

## Automation and exit codes

| Exit | Meaning |
| --- | --- |
| `0` | Reports written; no finding meets `--fail-on` threshold |
| `1` | Reports written; at least one finding meets the threshold |
| `2` | Operational failure, such as unreadable input, missing tool, timeout, or incomplete full scan |

`--fail-on fail` is the default. Use `--fail-on warn` for a stricter review gate, or `--fail-on never` to report findings without returning 1. Operational errors still return 2. A full-scan failure after readable metadata can produce an explicitly failed report.

`--metadata-only` intentionally skips events, loudness and full decoding; it marks the report incomplete. The default full-scan timeout is 300 seconds. For long material, set `--timeout 1800`, for example.

Reports are not overwritten unless `--overwrite` is supplied. Source media, subtitle files, and profile files are protected from report-output collisions. A source SHA-256 is included to identify the reviewed bytes. JSON carries the input filename, not its parent directories.

## Development and verification

```bash
python3 -m unittest discover -s tests -v
```

The suite includes real FFmpeg-generated fixtures plus parser, subtitle and report checks. Integration tests skip when FFmpeg is unavailable. See [the validation record](docs/VALIDATION.md) for what was actually run on this release; the initial Linux GitHub Actions run is documented with an actual link; other platforms must be evaluated separately.

## Scope and project status

This tool provides a focused delivery-report workflow. It does not replace comprehensive audiovisual preservation tools such as [QCTools](https://mediaarea.net/QCTools) or [MediaConch](https://mediaarea.net/MediaConch), nor the underlying [FFmpeg](https://ffmpeg.org/) project. There is no affiliation with these projects or OpenAI.

The initial implementation was prepared with AI assistance and checked with reproducible fixtures. Future maintainers remain responsible for reviewing changes and investigating failures. See [CONTRIBUTING.md](CONTRIBUTING.md), [the roadmap](docs/ROADMAP.md), and [CHANGELOG.md](CHANGELOG.md).

License: [MIT](LICENSE). FFmpeg is a separately installed project under its own license; no FFmpeg binary is distributed here.
