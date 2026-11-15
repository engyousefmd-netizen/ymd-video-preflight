# YMD Video Preflight v0.1.0 — first source-only alpha

YMD Video Preflight is an early-stage MIT-licensed, offline command-line tool for local video delivery checks. This prerelease provides code and a reproducible demonstration; **it is not a service or a certified video QC product**.

## What is included

- FFmpeg/ffprobe metadata analysis and timestamped black, silence and freeze review cues.
- Loudness and true-peak measurement, editable house profiles, basic UTF-8 SRT auditing.
- Arabic/RTL and English HTML, JSON and Markdown reports.
- Python 3.10+ source, installation instructions, synthetic fixture and example report, automated tests.
- [Successful GitHub Actions tests](https://github.com/engyousefmd-netizen/ymd-video-preflight/actions/runs/43711109502) on Ubuntu with Python 3.10/3.12/3.13, macOS with Python 3.12 and Windows with Python 3.12.

## Getting started

Download the GitHub-generated source ZIP, extract it, install Python 3.10+ and FFmpeg/ffprobe separately, then follow the [README quick start](https://github.com/engyousefmd-netizen/ymd-video-preflight#quick-start). **No FFmpeg executables or bundled third-party tools are distributed in this release.**

For an immediate example, use `examples/media/synthetic-review.mp4` with `examples/media/captions.srt`. The example intentionally contains findings.

## Limitations / beta feedback

This is a **synthetic-test-validated alpha**. There are **no verified independent users or production-delivery validations** at publication. Flags for stills, fades and silence can be intentional. Do not share clients' private video or credentials in GitHub Issues. See the [field-test protocol](https://github.com/engyousefmd-netizen/ymd-video-preflight/blob/main/docs/FIELD_TESTING.md) to provide reproducible, permission-safe feedback.

License: MIT. Source-only prerelease.
