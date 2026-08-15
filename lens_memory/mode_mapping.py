"""Map an aspect ratio to a projector lens-memory mode.

The mapping values are opaque command strings passed straight through to
whatever consumes the MQTT ``mode`` topic (the Home Assistant blueprint sends
them to ``remote.send_command``). This keeps the service projector-agnostic.

The original HA blueprint did exact string equality on the aspect ratio
(``'2.39'`` etc.). We instead match the nearest configured ratio within a
tolerance, so a scanned ``2.40`` still resolves to the ``2.39`` bucket.
"""

from __future__ import annotations

import logging

logger = logging.getLogger(__name__)

# Default mapping mirrors the original blueprint:
#   2.39 -> mode_2, 2.10 -> mode_4, 1.85 -> mode_3, 1.78/1.37/1.33 -> mode_1
DEFAULT_MAPPING: dict[str, str] = {
    "2.39": "mode_2",
    "2.10": "mode_4",
    "1.85": "mode_3",
    "1.78": "mode_1",
    "1.37": "mode_1",
    "1.33": "mode_1",
}


class ModeMapper:
    def __init__(self, mapping: dict[str, str], tolerance: float = 0.05):
        # Pre-parse keys to floats for nearest-match; keep the raw value string.
        self._buckets: list[tuple[float, str]] = []
        for ratio, mode in mapping.items():
            try:
                self._buckets.append((float(ratio), mode))
            except (TypeError, ValueError):
                logger.warning("Ignoring non-numeric mapping key %r", ratio)
        self.tolerance = tolerance

    def resolve(self, aspect_ratio: str | None) -> str | None:
        """Return the mode for ``aspect_ratio`` (e.g. ``"2.39"``) or ``None``."""
        if aspect_ratio is None:
            return None
        try:
            value = float(aspect_ratio)
        except (TypeError, ValueError):
            logger.info("Aspect ratio %r is not numeric; no mode.", aspect_ratio)
            return None

        best_mode: str | None = None
        best_delta = self.tolerance
        for ratio, mode in self._buckets:
            delta = abs(value - ratio)
            if delta <= best_delta:
                best_delta = delta
                best_mode = mode
        if best_mode is None:
            logger.info("No mode within %.3f of aspect ratio %s", self.tolerance, value)
        return best_mode
