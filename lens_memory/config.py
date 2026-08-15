"""Configuration from environment variables (no config file, no secrets in code)."""

from __future__ import annotations

import json
import logging
import os
from dataclasses import dataclass, field

from .mode_mapping import DEFAULT_MAPPING

logger = logging.getLogger(__name__)


def _env_bool(name: str, default: bool) -> bool:
    raw = os.environ.get(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def _env_float(name: str, default: float) -> float:
    raw = os.environ.get(name)
    if raw is None or not raw.strip():
        return default
    try:
        return float(raw)
    except ValueError:
        logger.warning("Invalid float for %s=%r; using %s", name, raw, default)
        return default


def _env_int(name: str, default: int) -> int:
    raw = os.environ.get(name)
    if raw is None or not raw.strip():
        return default
    try:
        return int(raw)
    except ValueError:
        logger.warning("Invalid int for %s=%r; using %s", name, raw, default)
        return default


def _env_mapping(name: str) -> dict[str, str]:
    raw = os.environ.get(name)
    if not raw or not raw.strip():
        return dict(DEFAULT_MAPPING)
    try:
        parsed = json.loads(raw)
        if not isinstance(parsed, dict):
            # TRY004 is suppressed deliberately: the except below catches
            # ValueError to fall back to DEFAULT_MAPPING, and a TypeError
            # would escape it.
            raise ValueError("mapping must be a JSON object")  # noqa: TRY004
        return {str(k): str(v) for k, v in parsed.items()}
    except (json.JSONDecodeError, ValueError) as error:
        logger.warning("Invalid %s (%s); using default mapping", name, error)
        return dict(DEFAULT_MAPPING)


@dataclass
class Config:
    # MQTT
    mqtt_host: str
    mqtt_port: int
    mqtt_username: str | None
    mqtt_password: str | None
    topic_prefix: str
    discovery_prefix: str

    # Plex
    plex_url: str | None
    plex_token: str | None
    plex_verify_tls: bool

    # Aspect-ratio JSON
    aspect_ratios_json_path: str | None
    aspect_ratio_calculation: str

    # blu-ray.com fallback
    bluray_com_fallback: bool

    # Mode mapping
    lens_mode_mapping: dict[str, str] = field(default_factory=lambda: dict(DEFAULT_MAPPING))
    lens_mode_tolerance: float = 0.05
    lens_mode_idle: str = "mode_1"

    log_level: str = "INFO"

    # --- Derived MQTT topics -------------------------------------------------
    @property
    def event_topic(self) -> str:
        return f"{self.topic_prefix}/event"

    @property
    def status_topic(self) -> str:
        return f"{self.topic_prefix}/status"

    @property
    def aspect_ratio_topic(self) -> str:
        return f"{self.topic_prefix}/aspect-ratio/state"

    @property
    def mode_topic(self) -> str:
        return f"{self.topic_prefix}/mode/state"

    @property
    def attributes_topic(self) -> str:
        return f"{self.topic_prefix}/attributes"

    @classmethod
    def from_env(cls) -> Config:
        host = os.environ.get("MQTT_HOST")
        if not host:
            raise SystemExit("MQTT_HOST is required")
        return cls(
            mqtt_host=host,
            mqtt_port=_env_int("MQTT_PORT", 1883),
            mqtt_username=os.environ.get("MQTT_USERNAME") or None,
            mqtt_password=os.environ.get("MQTT_PASSWORD") or None,
            topic_prefix=os.environ.get("MQTT_TOPIC_PREFIX", "lens-memory").rstrip("/"),
            discovery_prefix=os.environ.get("MQTT_DISCOVERY_PREFIX", "homeassistant").rstrip("/"),
            plex_url=os.environ.get("PLEX_URL") or None,
            plex_token=os.environ.get("PLEX_TOKEN") or None,
            plex_verify_tls=_env_bool("PLEX_VERIFY_TLS", True),
            aspect_ratios_json_path=os.environ.get("ASPECT_RATIOS_JSON_PATH") or None,
            aspect_ratio_calculation=os.environ.get(
                "ASPECT_RATIO_CALCULATION", "relativeMedianAspectRadio"
            ),
            bluray_com_fallback=_env_bool("BLURAY_COM_FALLBACK", True),
            lens_mode_mapping=_env_mapping("LENS_MODE_MAPPING"),
            lens_mode_tolerance=_env_float("LENS_MODE_TOLERANCE", 0.05),
            lens_mode_idle=os.environ.get("LENS_MODE_IDLE", "mode_1"),
            log_level=os.environ.get("LOG_LEVEL", "INFO").upper(),
        )
