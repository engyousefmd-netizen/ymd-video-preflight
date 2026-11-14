"""Command-line interface for local, non-destructive reports."""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import sys
import tempfile

from . import __version__
from .core import AnalysisError, analyze
from .profiles import BUILTINS, load_profile
from .report import render_html, render_markdown


def parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="YMD Video Preflight — local video checks with Arabic/English reports.")
    p.add_argument("input", type=Path, help="Local media file; never uploaded or modified.")
    p.add_argument("--output", type=Path, required=True, help="Directory for report.html, report.json and report.md.")
    p.add_argument("--profile", choices=sorted(BUILTINS), default="general")
    p.add_argument("--profile-json", type=Path, help="JSON house-profile overrides.")
    p.add_argument("--srt", type=Path, help="Optional UTF-8 SRT captions.")
    p.add_argument("--language", choices=["ar", "en"], default="ar")
    p.add_argument("--metadata-only", action="store_true", help="Skip full decode, event and loudness checks; report stays incomplete.")
    p.add_argument("--timeout", type=float, default=300, help="Full-scan timeout in seconds (default: 300).")
    p.add_argument("--fail-on", choices=["fail", "warn", "never"], default="fail", help="Exit 1 for matching report findings; operational errors always return 2.")
    p.add_argument("--overwrite", action="store_true", help="Replace existing report files, never input media.")
    p.add_argument("--version", action="version", version=__version__)
    return p


def write_reports(report: dict, output: Path, language: str, overwrite: bool = False,
                  protected_paths: tuple[Path, ...] = ()) -> None:
    output = output.expanduser().resolve()
    targets = [output / name for name in ["report.html", "report.json", "report.md"]]
    protected = {p.expanduser().resolve() for p in protected_paths}
    if any(t.resolve() in protected for t in targets):
        raise ValueError("A report output would replace an input file. Choose a different output directory.")
    if any(t.is_symlink() for t in targets):
        raise ValueError("Report targets must not be symlinks.")
    existing = [t.name for t in targets if t.exists()]
    if existing and not overwrite:
        raise ValueError("Reports already exist: " + ", ".join(existing) + ". Choose another directory or use --overwrite.")
    texts = [render_html(report, language), json.dumps(report, ensure_ascii=False, indent=2, allow_nan=False) + "\n", render_markdown(report, language)]
    output.mkdir(parents=True, exist_ok=True)
    staged = []
    published = []
    try:
        for target, text in zip(targets, texts):
            with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=output, prefix=".ymd-", delete=False) as handle:
                handle.write(text)
                staged.append((Path(handle.name), target))
        for temporary, target in staged:
            if overwrite:
                os.replace(temporary, target)
            else:
                # A check followed by os.replace could overwrite a concurrent
                # run's report. A same-directory hard link creates exclusively.
                try:
                    os.link(temporary, target)
                except FileExistsError as exc:
                    raise ValueError(f"Report appeared during writing: {target.name}. Choose another output directory.") from exc
                published.append((target, temporary.stat()))
    except Exception:
        # Roll back only our new links, never another writer's replacement.
        if not overwrite:
            for target, original in published:
                try:
                    current = target.lstat()
                    if (current.st_dev, current.st_ino) == (original.st_dev, original.st_ino):
                        target.unlink()
                except FileNotFoundError:
                    pass
        raise
    finally:
        for temporary, _ in staged:
            temporary.unlink(missing_ok=True)


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    try:
        profile = load_profile(args.profile, args.profile_json)
        report = analyze(args.input, profile, args.srt, args.metadata_only, args.timeout)
        protected = tuple(p for p in [args.input, args.srt, args.profile_json] if p is not None)
        write_reports(report, args.output, args.language, args.overwrite, protected)
        print(f"{report['summary']['status'].upper()}: {args.output.resolve() / 'report.html'}")
        print(json.dumps(report["summary"]["counts"], ensure_ascii=False))
        if any(c["id"] == "scan_complete" and c["status"] == "fail" for c in report["checks"]):
            return 2
        status = report["summary"]["status"]
        return int(args.fail_on != "never" and (status == "fail" or (args.fail_on == "warn" and status == "warn")))
    except (AnalysisError, OSError, ValueError) as exc:
        print(f"YMD Preflight: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
