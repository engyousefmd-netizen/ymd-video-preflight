# Validation record — 0.1.0

Checked on 2026-11-14T08:41:24.031190+00:00.

## Executed

- `python3 -m unittest discover -s tests -v`: **49 tests passed**, including eight integration tests with real FFmpeg-generated media.
- Runtime: Python 3.12.14 on Linux; FFmpeg/ffprobe 7.1.5.
- Synthetic eight-second input: a black interval from 2.0–3.2 s, silence near 2.005–3.221 s, and static intervals from 2.0–3.2 and 3.2–5.2 s were detected.
- The optional SRT fixture produced five review findings, including an overlap and a cue extending beyond the clip.
- SHA-256 checks verified the fixture remained unchanged. Arabic filenames and shell metacharacters were handled as data.
- A concurrent-output regression was reproduced and corrected: without `--overwrite`, a report created by another run is preserved.
- HTML/Markdown escaping, RTL structure, null/missing-field handling and standalone resources were checked programmatically.

- An isolated package build/install completed successfully; the installed CLI returned version `0.1.0`. No global Python environment was modified.

## Limits

- No independent users or client deliveries were involved in validation.
- macOS and Windows execution has not been tested in this environment.
- GitHub Actions has not run. The included workflow is prepared configuration only.
- Browser-rendered visual QA was unavailable because the local browser process could not open its required socket. The report has structural checks, not a completed visual-browser review.
- Measurements and threshold checks do not replace human review; see CHECKS.md.
