from __future__ import annotations

"""Utility functions to work with built-in reference audio samples.

This module centralises logic for:
1. Loading the ``models/reference_samples.csv`` metadata file.
2. Converting each row to a structured ``ReferenceSample`` dataclass.
3. Convenience helpers to filter and play back samples.

Keeping it separate from the CLI allows programmatic use from Python code as
well as reuse by future web/API front-ends.
"""

from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional
import csv

# Re-use canonical constants so callers can build filter UIs with the same list
from .core.model_config import (
    MODEL_GENDER,
    MODEL_GROUP,
    MODEL_AREA,
    MODEL_EMOTION,
)

__all__ = [
    "ReferenceSample",
    "load_reference_samples",
    "filter_samples",
    "get_sample_path",
    "play_sample",
]


@dataclass(slots=True)
class ReferenceSample:
    """Represents a single reference sample entry."""

    filename: str
    gender: str
    group: str
    area: str
    emotion: str
    text: str

    def matches(
        self,
        gender: Optional[str] = None,
        group: Optional[str] = None,
        area: Optional[str] = None,
        emotion: Optional[str] = None,
    ) -> bool:
        """Return ``True`` if this sample satisfies **all** provided filters."""

        return (
            (gender is None or self.gender == gender)
            and (group is None or self.group == group)
            and (area is None or self.area == area)
            and (emotion is None or self.emotion == emotion)
        )


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _csv_path() -> Path:
    """Return absolute path to ``reference_samples.csv`` bundled with the package."""

    #  <package_root>/models/reference_samples.csv
    return Path(__file__).resolve().parent.parent / "models" / "reference_samples.csv"


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def load_reference_samples() -> List[ReferenceSample]:
    """Load all reference samples from the CSV.

    Returns an empty list if the file cannot be found.
    """

    csv_path = _csv_path()
    if not csv_path.exists():
        # Gracefully degrade – no reference samples shipped.
        return []

    samples: List[ReferenceSample] = []
    with csv_path.open(newline="", encoding="utf-8") as fh:
        reader = csv.reader(fh)
        for row in reader:
            if len(row) < 6:
                continue  # skip malformed rows
            # Normalise categorical fields to lowercase for case-insensitive filtering
            filename, gender, group, area, emotion, text = row[:6]
            samples.append(
                ReferenceSample(
                    filename=filename.strip(),
                    gender=gender.strip().lower(),
                    group=group.strip().lower(),
                    area=area.strip().lower(),
                    emotion=emotion.strip().lower(),
                    text=text.strip(),
                )
            )
    return samples


def filter_samples(
    samples: List[ReferenceSample],
    *,
    gender: Optional[str] = None,
    group: Optional[str] = None,
    area: Optional[str] = None,
    emotion: Optional[str] = None,
) -> List[ReferenceSample]:
    """Return samples that match all specified filters."""

    gender = gender and gender.lower()
    group = group and group.lower()
    area = area and area.lower()
    emotion = emotion and emotion.lower()

    return [s for s in samples if s.matches(gender, group, area, emotion)]


def get_sample_path(sample: ReferenceSample) -> Path:
    """Return absolute path on disk for the given *sample*."""

    # Handle both flat filenames and organized folder paths
    models_dir = Path(__file__).resolve().parent.parent / "models"
    sample_path = models_dir / sample.filename
    
    # If the organized path doesn't exist, try the flat filename in models root
    if not sample_path.exists():
        flat_filename = Path(sample.filename).name  # Just the filename without folders
        fallback_path = models_dir / flat_filename
        if fallback_path.exists():
            return fallback_path
    
    return sample_path


def play_sample(sample: ReferenceSample):
    """Attempt to play *sample* audio in the current process.

    Relies on ``pydub.playback`` which in turn tries *simpleaudio*, *ffplay*, or
    *avplay* under the hood. If playback fails, the exception is caught and the
    user is instructed to open the file manually.
    """

    path = get_sample_path(sample)
    try:
        from pydub import AudioSegment  # type: ignore
        from pydub.playback import play  # type: ignore

        audio = AudioSegment.from_file(path)
        print(f"\n▶️  Playing {path.name} … (Ctrl-C to stop)\n")
        play(audio)
    except Exception as exc:  # pragma: no cover – best-effort
        print(
            f"⚠️  Unable to auto-play audio – {exc}. "
            f"You can open the file manually: {path}"
        ) 