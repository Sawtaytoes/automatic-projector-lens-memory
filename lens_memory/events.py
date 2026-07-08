"""Normalized, source-agnostic playback event.

Every input source (today: Home Assistant over MQTT; later: Plex sessions,
Kodi JSON-RPC) converts its native notification into a ``PlaybackEvent`` and
hands it to the resolver. The resolver never knows which source produced it.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any, Optional

# Plex media_content_id can arrive as a bare rating key ("12345") or as a full
# library key path ("/library/metadata/12345"). Pull the trailing digits.
_RATING_KEY_DIGITS = re.compile(r"(\d+)\s*$")


def _clean_str(value: Any) -> Optional[str]:
    if value is None:
        return None
    text = str(value).strip()
    if not text or text.lower() in {"none", "null", "unknown", "unavailable"}:
        return None
    return text


def _extract_rating_key(value: Any) -> Optional[str]:
    text = _clean_str(value)
    if text is None:
        return None
    match = _RATING_KEY_DIGITS.search(text)
    return match.group(1) if match else None


def _coerce_year(value: Any) -> Optional[int]:
    text = _clean_str(value)
    if text is None:
        return None
    match = re.search(r"\d{4}", text)
    return int(match.group(0)) if match else None


@dataclass(frozen=True)
class PlaybackEvent:
    """A snapshot of what a player is doing, normalized across sources."""

    state: str  # "playing" or "idle"
    player: Optional[str] = None
    rating_key: Optional[str] = None
    title: Optional[str] = None
    year: Optional[int] = None

    @property
    def is_playing(self) -> bool:
        return self.state == "playing"

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "PlaybackEvent":
        """Build an event from a loosely-typed MQTT/JSON payload.

        Tolerates missing keys and Home Assistant's ``None``/``"unknown"``
        attribute values, which vary widely by player integration.
        """
        raw_state = _clean_str(payload.get("state")) or "idle"
        state = "playing" if raw_state.lower() == "playing" else "idle"
        return cls(
            state=state,
            player=_clean_str(payload.get("player")),
            rating_key=_extract_rating_key(payload.get("rating_key")),
            title=_clean_str(payload.get("title")),
            year=_coerce_year(payload.get("year")),
        )
