# Maintenance, validation and adoption evidence

**Project:** YMD Video Preflight · MIT-licensed public alpha · Python/FFmpeg CLI

This page is an auditable record of **observed maintenance and verification**, separate from plans or aspirations. It does not imply certification, customer adoption or eligibility for any funding program.

## Verified to date (reviewed 2026-11-16)

| Category | Evidence | What can reasonably be claimed |
| --- | --- | --- |
| Public source and license | [Repository](https://github.com/engyousefmd-netizen/ymd-video-preflight), [MIT license](../LICENSE) | Source is publicly inspectable and open-source licensed |
| Implementation and examples | [CLI](../ymd_preflight/cli.py), [synthetic demo](../examples/demo-report/report.html), [checks](CHECKS.md) | A runnable single-file video preflight workflow exists |
| Test validation | [Linux/macOS/Windows CI success](https://github.com/engyousefmd-netizen/ymd-video-preflight/actions/runs/43711555916), [test design](VALIDATION.md) | Automated tests pass on the five documented runner configurations |
| Release management | [v0.1.0 alpha prerelease](https://github.com/engyousefmd-netizen/ymd-video-preflight/releases/tag/v0.1.0) | A source-only prerelease and notes exist |
| Issue triage and maintenance | [Issue #2 (closed)](https://github.com/engyousefmd-netizen/ymd-video-preflight/issues/2), [fix PR #3 (merged)](https://github.com/engyousefmd-netizen/ymd-video-preflight/pull/3) | At least one observed fix/review/release maintenance cycle |
| Independent real-world adoption | [Field-testing issue #1 (open)](https://github.com/engyousefmd-netizen/ymd-video-preflight/issues/1) | **Not yet established**; a request for volunteers is not evidence of users |

## Safe opt-in field test

1. Ask an editor whether they **want** to try the tool; do not add people to a mailing list, upload their media, or publish their identity without consent.
2. Invite them to run the [five-minute test](FIELD_TESTING.md) on the synthetic clip first, then on their own or explicitly authorized footage if they choose.
3. Request a reproducible, permission-safe [field report](https://github.com/engyousefmd-netizen/ymd-video-preflight/issues/new/choose) with OS/Python/FFmpeg versions, command/profile, helpful flags, false alarms and missed issues. **Negative feedback is welcome.**
4. Triage the report publicly, reproduce with a synthetic sample if possible, and link any fix PR and passing CI result.
5. Update this page **only after** verified independent reports exist. Never equate requested testers, CI runs, GitHub stars or synthetic fixtures with actual adoption.

## Practical early milestone — not a current result

- Seek three **independent, consenting** field reports from different editors.
- Record examples of false positives and negatives without publishing client material.
- Resolve at least one genuine user-discovered problem with a reviewable test and change, if a reproducible problem is found.
- Measure useful adoption only when there is independently verifiable evidence. Do not manufacture downloads, stars, testimonials or usage numbers.

## Scope and limitations

The tool does not replace human review, transcribe speech, verify subtitles' meaning or detect every defect. It only processes local files. See [CHECKS.md](CHECKS.md) and [VALIDATION.md](VALIDATION.md) for coverage and limits.
