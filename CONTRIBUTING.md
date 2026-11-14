# Contributing

This is an initial project. Contributions should improve a real, reproducible delivery-checking task.

## Useful reports

Include the command, Python and FFmpeg versions, selected profile, expected result, actual report finding, and a minimal reproducer. Prefer a synthetic FFmpeg-generated example. Do not post private client footage, local directory names or credentials. False positives from intentional pauses/stills are useful to discuss, but do not automatically imply a detector bug.

## Development

1. Use Python 3.10+ and FFmpeg/ffprobe on PATH.
2. Run `python3 -m unittest discover -s tests -v` before a change and after it.
3. For behavior changes, add a test that reproduces a real failure or verifies a measurable output.
4. Keep the core package free of third-party Python runtime dependencies unless a documented need justifies adding one.
5. Keep English and Arabic documentation consistent. Never convert an unknown measurement to a pass.

The initial implementation has AI-assisted contributions. Reviewers should inspect generated changes as carefully as any other change; generated tests do not establish adoption or real-world accuracy.

## Review and release

A maintainer should reproduce reported issues, review changes, update the changelog, rerun relevant checks, and tag a release only after the intended behavior is verified. A proposed workflow file is not evidence of a completed CI run. No guaranteed response time is offered by this new project.

Before a public repository is created, use this package locally; there is no public issue tracker in this release archive. After publication, use that repository's Issues and Pull Requests.
