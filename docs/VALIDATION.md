# Validation record — 0.1.0 alpha

This document separates verified automated checks from real-world acceptance. It records observations, not claims of production certification.

## Initial local validation — 2026-11-14

- `python3 -m unittest discover -s tests -v`: **49 tests passed**, including eight integration tests using **synthetically generated** FFmpeg media.
- Environment: Python 3.12.14 on Linux; FFmpeg/ffprobe 7.1.5.
- The eight-second synthetic fixture produced black, silence and static-frame review cues around the intentionally inserted intervals. The accompanying SRT fixture produced five findings, including overlap and an out-of-bounds cue.
- Tests checked source SHA-256 preservation, Arabic/shell-special filenames, escaped HTML/Markdown output, a concurrent report-output regression, and isolated package installation.

## GitHub Actions evidence — 2026-11-14 and 2026-11-15

| Observation | Evidence | Interpretation |
| --- | --- | --- |
| Initial Linux CI passed (Python 3.10, 3.12, 3.13) | [2026-11-14 run](https://github.com/engyousefmd-netizen/ymd-video-preflight/actions/runs/43583356067) | Initial published build was testable on Ubuntu |
| Initial Windows CI exposed a test fixture newline problem | [Failure](https://github.com/engyousefmd-netizen/ymd-video-preflight/actions/runs/43711000340), [fix](https://github.com/engyousefmd-netizen/ymd-video-preflight/commit/81b800dc9a0f5c08e70a91f85734ea0380692650) | The test writer unintentionally transformed CRLF into CRCRLF on Windows; fixture corrected |
| Linux / Windows / macOS matrix passed | [Cross-platform run](https://github.com/engyousefmd-netizen/ymd-video-preflight/actions/runs/43711109502) | Five test jobs passed: Ubuntu/Python 3.10, 3.12, 3.13; macOS/Python 3.12; Windows/Python 3.12 |
| The same matrix passed on `main`, followed by successful source-only prerelease job | [Main branch run](https://github.com/engyousefmd-netizen/ymd-video-preflight/actions/runs/43711555916), [v0.1.0 prerelease](https://github.com/engyousefmd-netizen/ymd-video-preflight/releases/tag/v0.1.0) | Successful verification at the latest documented release |

## What these results do **not** show

- **No verified independent editor trials, users, downloads or client deliveries** are established by the test suite. [Issue #1](https://github.com/engyousefmd-netizen/ymd-video-preflight/issues/1) seeks opt-in field reports.
- GitHub-hosted runner success is not proof that arbitrary real exports or all FFmpeg distributions work.
- The generated synthetic media tests known scenarios; the false-positive and false-negative rates on real material remain unmeasured.
- Browser-rendered visual QA of the HTML report was not completed in the initial validation; structural output tests did pass.
- Only the primary selected audio/video streams are scanned, and the tool does not certify a delivery or replace editorial judgment.

See [field-testing instructions](FIELD_TESTING.md) and [maintenance evidence](ADOPTION_EVIDENCE.md).
