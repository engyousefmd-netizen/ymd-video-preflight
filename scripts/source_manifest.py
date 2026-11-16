"""Generate a current SHA-256 inventory of tracked source files, on demand.

The output is intentionally untracked: committing a frozen inventory can silently
make its checksums stale after ordinary source or documentation changes.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]


def build_manifest(root: Path = ROOT) -> str:
    """Return deterministic JSON for Git-tracked files (excluding the output)."""
    try:
        process = subprocess.run(
            ["git", "-C", str(root), "ls-files", "-z"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=True,
        )
    except (OSError, subprocess.CalledProcessError) as exc:
        raise RuntimeError("Git is required to enumerate tracked source files.") from exc

    names = sorted(os.fsdecode(raw) for raw in process.stdout.split(b"\x00") if raw)
    manifest = []
    for name in names:
        if name == "MANIFEST.json":
            continue  # Avoid a self-referential hash.
        path = root / name
        if not path.is_file() or path.is_symlink():
            raise RuntimeError(f"Tracked source is not a regular file: {name}")
        data = path.read_bytes()
        manifest.append({
            "path": Path(name).as_posix(),
            "bytes": len(data),
            "sha256": hashlib.sha256(data).hexdigest(),
        })
    return json.dumps(manifest, ensure_ascii=False, indent=2) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=ROOT / "MANIFEST.json")
    parser.add_argument("--check", action="store_true", help="Verify an existing generated inventory.")
    args = parser.parse_args()
    try:
        text = build_manifest()
        output = args.output
        if args.check:
            if not output.is_file() or output.read_text(encoding="utf-8") != text:
                print(f"Out-of-date or missing manifest: {output}", file=sys.stderr)
                return 1
            print(f"Verified current manifest: {output}")
            return 0
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(text, encoding="utf-8", newline="\n")
        print(f"Wrote fresh manifest: {output}")
        return 0
    except (OSError, RuntimeError) as exc:
        print(f"Manifest error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
