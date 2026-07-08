"""Resolve a PlaybackEvent into an aspect ratio and lens-memory mode.

Pipeline (playing):
  1. Plex API: rating_key -> media file path
  2. Local JSON: media file path -> aspect ratio
  3. blu-ray.com fallback: title (+ year) -> aspect ratio
  4. Mode mapping: aspect ratio -> lens-memory mode

This module is deliberately independent of MQTT and of the input source. It
takes a ``PlaybackEvent`` and returns a ``Resolution``; the caller decides how
to publish it.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Optional

from .aspect_ratios import AspectRatioLookup
from .bluray_com import BlurayComClient
from .events import PlaybackEvent
from .mode_mapping import ModeMapper
from .plex import PlexClient

logger = logging.getLogger(__name__)


@dataclass
class Resolution:
    aspect_ratio: Optional[str]  # e.g. "2.39", or None when unknown
    mode: Optional[str]          # e.g. "mode_2", or None when unknown
    source: Optional[str] = None  # which stage produced the ratio
    media_file_path: Optional[str] = None
    title: Optional[str] = None


class Resolver:
    def __init__(
        self,
        plex: PlexClient,
        aspect_ratios: AspectRatioLookup,
        bluray_com: BlurayComClient,
        mode_mapper: ModeMapper,
        idle_mode: str,
    ):
        self.plex = plex
        self.aspect_ratios = aspect_ratios
        self.bluray_com = bluray_com
        self.mode_mapper = mode_mapper
        self.idle_mode = idle_mode

    def resolve(self, event: PlaybackEvent) -> Resolution:
        if not event.is_playing:
            # Idle: return the reset mode and clear the aspect ratio.
            return Resolution(aspect_ratio=None, mode=self.idle_mode, source="idle")

        aspect_ratio: Optional[str] = None
        source: Optional[str] = None
        media_file_path: Optional[str] = None

        # 1 + 2: Plex file path -> local JSON lookup
        if event.rating_key and self.plex.enabled:
            media_file_path = self.plex.get_media_file_path(event.rating_key)
            if media_file_path:
                aspect_ratio = self.aspect_ratios.lookup(media_file_path)
                if aspect_ratio:
                    source = "aspect-ratios-json"

        # 3: blu-ray.com fallback
        if aspect_ratio is None and event.title:
            fallback = self.bluray_com.get_aspect_ratio(event.title, event.year)
            if fallback:
                aspect_ratio = fallback
                source = "bluray-com"

        # 4: map to a mode
        mode = self.mode_mapper.resolve(aspect_ratio)
        logger.info(
            "Resolved player=%s title=%r rating_key=%s -> aspect_ratio=%s mode=%s via %s",
            event.player,
            event.title,
            event.rating_key,
            aspect_ratio,
            mode,
            source,
        )
        return Resolution(
            aspect_ratio=aspect_ratio,
            mode=mode,
            source=source,
            media_file_path=media_file_path,
            title=event.title,
        )
