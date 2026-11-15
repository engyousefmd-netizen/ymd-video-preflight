# Development roadmap

These are proposed next steps, not completed features or promised release dates. We record unresolved work in public issues rather than suggesting that planned features or real user testing have already happened.

**Evidence and next steps**

- **Cross-platform CI achieved:** [five-runner GitHub Actions matrix passed](https://github.com/engyousefmd-netizen/ymd-video-preflight/actions/runs/43711109502), tracked in [#2](https://github.com/engyousefmd-netizen/ymd-video-preflight/issues/2). This is test coverage, not proof of real-world adoption.
- **Independent usage remains open:** [#1 — Consent-based field feedback](https://github.com/engyousefmd-netizen/ymd-video-preflight/issues/1). Three authentic reproducible editor reports would be a useful initial goal, not a result achieved so far.

1. Run the tool on real, authorized Studio YMD deliveries and record false positives and missed issues without exposing client files.
2. Invite a small number of consenting editors to try it; collect reproducible feedback instead of collecting artificial stars or downloads.
3. Improve full Arabic localization of diagnostic messages and caption-rate heuristics.
4. Add a batch manifest and folder report only after the single-file workflow has proved useful.
5. Investigate better stream selection, per-channel silence, VFR checks and optional thumbnail review based on real user requests.
6. Maintain a release log, reproducible examples and issue-resolution history.
