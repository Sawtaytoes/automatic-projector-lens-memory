"""Local aspect-ratio lookup.

Reads the ``aspectRatioCalculations.json`` file produced by an external scanner
(e.g. Mux-Magic) and returns the requested calculation for a media file path.

File format::

    {
        "/media/Movies/Interstellar (2014).mkv": {
            "relativeMedianAspectRadio": "2.39",
            "exactMaxHeightAspectRatio": "2.40",
            ...
        }
    }

Ported from the original ``get_aspect_ratio.py`` HA shell script. Missing
entries return ``None`` (the original printed the sentinel string ``"NONE"``).
"""

from __future__ import annotations

import json
import logging

logger = logging.getLogger(__name__)

# The four calculation types emitted by the scanner.
CALCULATION_TYPES = (
    "exactMaxHeightAspectRatio",
    "exactMedianAspectRadio",
    "relativeMaxHeightAspectRatio",
    "relativeMedianAspectRadio",
)


class AspectRatioLookup:
    """Loads the calculations JSON once and indexes lookups by file path."""

    def __init__(self, json_path: str | None, calculation_type: str):
        self.json_path = json_path
        self.calculation_type = calculation_type
        self._data: dict[str, dict[str, str]] = {}
        self._load()

    def _load(self) -> None:
        if not self.json_path:
            logger.info("No aspect-ratio JSON configured; local lookup disabled.")
            return
        try:
            with open(self.json_path, encoding="utf-8") as file:
                self._data = json.load(file)
            logger.info(
                "Loaded %d aspect-ratio entries from %s",
                len(self._data),
                self.json_path,
            )
        except FileNotFoundError:
            logger.warning("Aspect-ratio JSON not found at %s; local lookup disabled.", self.json_path)
        except (json.JSONDecodeError, OSError) as error:
            logger.warning("Could not read aspect-ratio JSON %s: %s", self.json_path, error)

    @property
    def enabled(self) -> bool:
        return bool(self._data)

    def lookup(self, media_file_path: str | None) -> str | None:
        """Return the configured aspect ratio for ``media_file_path`` or ``None``."""
        if not media_file_path:
            return None
        entry = self._data.get(media_file_path)
        if not entry:
            return None
        value = entry.get(self.calculation_type)
        return str(value).strip() if value else None
