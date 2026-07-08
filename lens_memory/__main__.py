"""Entry point: wire config -> pipeline -> MQTT service and run."""

from __future__ import annotations

import logging

from .aspect_ratios import AspectRatioLookup
from .bluray_com import BlurayComClient
from .config import Config
from .mode_mapping import ModeMapper
from .mqtt_service import MqttService
from .plex import PlexClient
from .resolver import Resolver


def build_service(config: Config) -> MqttService:
    plex = PlexClient(
        base_url=config.plex_url,
        token=config.plex_token,
        verify_tls=config.plex_verify_tls,
    )
    aspect_ratios = AspectRatioLookup(
        json_path=config.aspect_ratios_json_path,
        calculation_type=config.aspect_ratio_calculation,
    )
    bluray_com = BlurayComClient(enabled=config.bluray_com_fallback)
    mode_mapper = ModeMapper(
        mapping=config.lens_mode_mapping,
        tolerance=config.lens_mode_tolerance,
    )
    resolver = Resolver(
        plex=plex,
        aspect_ratios=aspect_ratios,
        bluray_com=bluray_com,
        mode_mapper=mode_mapper,
        idle_mode=config.lens_mode_idle,
    )
    return MqttService(config, resolver)


def run() -> None:
    config = Config.from_env()
    logging.basicConfig(
        level=getattr(logging, config.log_level, logging.INFO),
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
    service = build_service(config)
    service.run()


if __name__ == "__main__":
    run()
