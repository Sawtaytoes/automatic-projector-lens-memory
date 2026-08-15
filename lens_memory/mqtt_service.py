"""MQTT glue: subscribe to playback events, publish resolved lens-memory state.

Threading model: paho runs its own network loop thread. Each inbound event is
handed to a single worker thread so a slow blu-ray.com scrape never blocks the
network loop. A generation counter makes a newer event supersede an in-flight
resolution, mirroring the old blueprint's ``mode: restart``.
"""

from __future__ import annotations

import json
import logging
import threading

import paho.mqtt.client as mqtt

from .config import Config
from .discovery import discovery_messages
from .events import PlaybackEvent
from .resolver import Resolution, Resolver

logger = logging.getLogger(__name__)


class MqttService:
    def __init__(self, config: Config, resolver: Resolver):
        self.config = config
        self.resolver = resolver

        self._client = mqtt.Client(
            callback_api_version=mqtt.CallbackAPIVersion.VERSION2,
            client_id="automatic-projector-lens-memory",
        )
        if config.mqtt_username:
            self._client.username_pw_set(config.mqtt_username, config.mqtt_password)
        # Last will: mark offline if we drop unexpectedly.
        self._client.will_set(config.status_topic, "offline", qos=1, retain=True)
        self._client.on_connect = self._on_connect
        self._client.on_message = self._on_message

        # Generation counter guards against stale in-flight resolutions.
        self._generation = 0
        self._lock = threading.Lock()

    # --- lifecycle -----------------------------------------------------------
    def run(self) -> None:
        self._client.connect(self.config.mqtt_host, self.config.mqtt_port)
        try:
            self._client.loop_forever()
        except KeyboardInterrupt:
            logger.info("Shutting down.")
        finally:
            self._publish(self.config.status_topic, "offline", retain=True)
            self._client.disconnect()

    # --- callbacks -----------------------------------------------------------
    def _on_connect(self, client, userdata, flags, reason_code, properties=None) -> None:
        if reason_code != 0:
            logger.error("MQTT connect failed: %s", reason_code)
            return
        logger.info("Connected to MQTT %s:%s", self.config.mqtt_host, self.config.mqtt_port)
        client.subscribe(self.config.event_topic, qos=1)

        # Announce availability + discovery.
        self._publish(self.config.status_topic, "online", retain=True)
        for topic, payload in discovery_messages(self.config):
            self._publish(topic, json.dumps(payload), retain=True)
        logger.info("Published discovery and subscribed to %s", self.config.event_topic)

    def _on_message(self, client, userdata, message) -> None:
        try:
            payload = json.loads(message.payload.decode("utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError) as error:
            logger.warning("Ignoring malformed event payload: %s", error)
            return
        if not isinstance(payload, dict):
            logger.warning("Ignoring non-object event payload: %r", payload)
            return

        event = PlaybackEvent.from_dict(payload)
        with self._lock:
            self._generation += 1
            generation = self._generation
        threading.Thread(
            target=self._handle_event,
            args=(event, generation),
            daemon=True,
        ).start()

    # --- work ----------------------------------------------------------------
    def _handle_event(self, event: PlaybackEvent, generation: int) -> None:
        resolution = self.resolver.resolve(event)
        # A newer event arrived while we were resolving; drop this stale result.
        with self._lock:
            if generation != self._generation:
                logger.info("Discarding stale resolution (gen %s < %s)", generation, self._generation)
                return
        self._publish_resolution(resolution)

    def _publish_resolution(self, resolution: Resolution) -> None:
        aspect_ratio = resolution.aspect_ratio or "unknown"
        self._publish(self.config.aspect_ratio_topic, aspect_ratio, retain=True)
        if resolution.mode:
            self._publish(self.config.mode_topic, resolution.mode, retain=True)
        attributes = {
            "source": resolution.source,
            "media_file_path": resolution.media_file_path,
            "title": resolution.title,
        }
        self._publish(self.config.attributes_topic, json.dumps(attributes), retain=True)

    # --- helpers -------------------------------------------------------------
    def _publish(self, topic: str, payload: str | None, retain: bool = False) -> None:
        self._client.publish(topic, payload, qos=1, retain=retain)
