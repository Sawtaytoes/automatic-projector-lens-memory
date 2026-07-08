"""Home Assistant MQTT discovery payloads.

Publishing these (retained) makes HA auto-create the sensor entities without
any YAML, replacing the old ``input_text`` helper hack. All sensors share one
device and use the service's availability (status) topic.

Discovery docs: https://www.home-assistant.io/integrations/mqtt/#mqtt-discovery
"""

from __future__ import annotations

from .config import Config

_DEVICE = {
    "identifiers": ["automatic_projector_lens_memory"],
    "name": "Projector Lens Memory",
    "manufacturer": "automatic-projector-lens-memory",
    "model": "MQTT lens-memory resolver",
}


def _sensor(config: Config, object_id: str, name: str, state_topic: str, icon: str) -> tuple[str, dict]:
    topic = f"{config.discovery_prefix}/sensor/automatic_projector_lens_memory/{object_id}/config"
    payload = {
        "name": name,
        "unique_id": f"automatic_projector_lens_memory_{object_id}",
        "state_topic": state_topic,
        "availability_topic": config.status_topic,
        "payload_available": "online",
        "payload_not_available": "offline",
        "json_attributes_topic": config.attributes_topic,
        "icon": icon,
        "device": _DEVICE,
    }
    return topic, payload


def discovery_messages(config: Config) -> list[tuple[str, dict]]:
    """Return (topic, payload) pairs for every discovered entity."""
    return [
        _sensor(
            config,
            "aspect_ratio",
            "Aspect Ratio",
            config.aspect_ratio_topic,
            "mdi:aspect-ratio",
        ),
        _sensor(
            config,
            "target_mode",
            "Lens Memory Target Mode",
            config.mode_topic,
            "mdi:camera-iris",
        ),
    ]


def discovery_topics(config: Config) -> list[str]:
    """Config topics to clear (empty retained payload) when tearing down."""
    return [topic for topic, _ in discovery_messages(config)]
