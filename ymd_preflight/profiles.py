"""Editable house preferences, not platform certification rules."""
from __future__ import annotations

from dataclasses import asdict, dataclass, fields, replace
import json
import math
from pathlib import Path


@dataclass(frozen=True)
class Profile:
    name: str = "general"
    expected_aspect_ratio: float | None = None
    aspect_tolerance: float = 0.025
    min_short_edge: int = 720
    min_fps: float = 23.0
    max_fps: float = 61.0
    target_lufs: float = -16.0
    loudness_tolerance_lu: float = 2.0
    max_true_peak_dbfs: float = -1.0
    black_min_seconds: float = 0.5
    black_pixel_threshold: float = 0.10
    black_picture_ratio: float = 0.98
    silence_min_seconds: float = 0.8
    silence_noise_db: float = -45.0
    freeze_min_seconds: float = 1.0
    freeze_noise_ratio: float = 0.001
    max_subtitle_chars_per_line: int = 42
    max_subtitle_lines: int = 2
    max_subtitle_cps: float = 20.0

    def to_dict(self) -> dict:
        return asdict(self)


BUILTINS = {
    "general": Profile(),
    "vertical-social": Profile(name="vertical-social", expected_aspect_ratio=9 / 16),
    "landscape": Profile(name="landscape", expected_aspect_ratio=16 / 9),
    "square": Profile(name="square", expected_aspect_ratio=1.0),
}


def validate_profile(profile: Profile) -> Profile:
    if not isinstance(profile.name, str) or not profile.name.strip():
        raise ValueError("Profile name must be a non-empty string.")
    values = profile.to_dict()
    for key, value in values.items():
        if key == "name" or (key == "expected_aspect_ratio" and value is None):
            continue
        if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
            raise ValueError(f"{key} must be a finite number.")
    for key in ["min_short_edge", "max_subtitle_chars_per_line", "max_subtitle_lines"]:
        if not isinstance(values[key], int) or values[key] < 1:
            raise ValueError(f"{key} must be a positive integer.")
    for key in ["min_fps", "max_fps", "black_min_seconds", "silence_min_seconds", "freeze_min_seconds", "max_subtitle_cps"]:
        if values[key] <= 0:
            raise ValueError(f"{key} must be positive.")
    if profile.expected_aspect_ratio is not None and profile.expected_aspect_ratio <= 0:
        raise ValueError("expected_aspect_ratio must be positive or null.")
    if profile.min_fps > profile.max_fps:
        raise ValueError("min_fps cannot exceed max_fps.")
    for key in ["aspect_tolerance", "black_pixel_threshold", "black_picture_ratio", "freeze_noise_ratio"]:
        if not 0 <= values[key] <= 1:
            raise ValueError(f"{key} must be between 0 and 1.")
    if not -70 <= profile.target_lufs <= -5:
        raise ValueError("target_lufs must be between -70 and -5.")
    if not -9 <= profile.max_true_peak_dbfs <= 0:
        raise ValueError("max_true_peak_dbfs must be between -9 and 0.")
    if profile.loudness_tolerance_lu < 0 or not -120 <= profile.silence_noise_db <= 0:
        raise ValueError("Invalid loudness tolerance or silence noise threshold.")
    return profile


def load_profile(name: str = "general", path: Path | None = None) -> Profile:
    if name not in BUILTINS:
        raise ValueError(f"Unknown profile: {name}")
    base = BUILTINS[name]
    if path is None:
        return base
    if path.stat().st_size > 100_000:
        raise ValueError("Profile JSON is too large.")
    overrides = json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(overrides, dict):
        raise ValueError("Profile JSON must be an object.")
    unknown = set(overrides) - {f.name for f in fields(Profile)}
    if unknown:
        raise ValueError("Unknown profile fields: " + ", ".join(sorted(unknown)))
    return validate_profile(replace(base, **overrides))
