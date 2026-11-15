# Development roadmap

These are proposed next steps, not completed features or promised release dates. We record unresolved work in public issues rather than suggesting that planned features or real user testing have already happened.

**Active evidence gaps**

- [#1 — Obtain consent-based feedback from independent editors](https://github.com/engyousefmd-netizen/ymd-video-preflight/issues/1). Three independent reproducible reports would be a useful initial goal, not a result achieved so far.
- [#2 — Windows/macOS compatibility checks](https://github.com/engyousefmd-netizen/ymd-video-preflight/issues/2). CI configuration is proposed; verify real run status before claiming success.

1. Run the tool on real, authorized Studio YMD deliveries and record false positives and missed issues without exposing client files.
2. Invite a small number of consenting editors to try it; collect reproducible feedback instead of collecting artificial stars or downloads.
3. Improve full Arabic localization of diagnostic messages and caption-rate heuristics.
4. Add a batch manifest and folder report only after the single-file workflow has proved useful.
5. Investigate better stream selection, per-channel silence, VFR checks and optional thumbnail review based on real user requests.
6. Maintain a release log, reproducible examples and issue-resolution history.
