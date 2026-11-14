#!/usr/bin/env python3
"""Generate a synthetic fixture with known review cues; no client media."""
from pathlib import Path
import argparse
import shutil
import subprocess


def make_demo(destination: Path) -> Path:
    binary = shutil.which("ffmpeg")
    if not binary:
        raise RuntimeError("Install FFmpeg first.")
    destination.mkdir(parents=True, exist_ok=True)
    output = destination / "synthetic-review.mp4"
    if output.exists():
        raise FileExistsError(f"Refusing to overwrite {output}")
    args = [binary, "-hide_banner", "-loglevel", "error", "-nostdin", "-n",
            "-f", "lavfi", "-i", "testsrc2=size=360x640:rate=25:duration=2",
            "-f", "lavfi", "-i", "color=c=black:size=360x640:rate=25:duration=1.2",
            "-f", "lavfi", "-i", "color=c=blue:size=360x640:rate=25:duration=2",
            "-f", "lavfi", "-i", "testsrc2=size=360x640:rate=25:duration=2.8",
            "-f", "lavfi", "-i", "sine=frequency=440:sample_rate=48000:duration=8,volume=0.65,volume=0:enable='between(t,2,3.2)'",
            "-filter_complex", "[0:v][1:v][2:v][3:v]concat=n=4:v=1:a=0[v]",
            "-map", "[v]", "-map", "4:a", "-c:v", "libx264", "-preset", "ultrafast",
            "-crf", "27", "-pix_fmt", "yuv420p", "-threads", "2", "-c:a", "aac", "-b:a", "128k",
            "-movflags", "+faststart", "-shortest", str(output.resolve())]
    subprocess.run(args, check=True, timeout=90)
    (destination / "captions.srt").write_text(
        "1\n00:00:00,200 --> 00:00:01,800\nمثال تجريبي مولّد\n\n"
        "2\n00:00:01,700 --> 00:00:03,000\nThis caption intentionally overlaps the previous cue.\n\n"
        "3\n00:00:07,500 --> 00:00:09,000\nيمتد هذا النص بعد نهاية الفيديو\n", encoding="utf-8")
    return output


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("destination", type=Path, nargs="?", default=Path("examples/media"))
    print(make_demo(p.parse_args().destination))
