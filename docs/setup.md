# Setup and configuration

## Requirements

- An MQTT broker.
- Home Assistant with its MQTT integration.
- A projector whose lens-memory presets can be called through a Home Assistant `remote` entity.
- Docker and Docker Compose.
- Optional Plex access or a local aspect-ratio database for exact lookups.

## Start the service

```sh
git clone https://github.com/Sawtaytoes/automatic-projector-lens-memory.git
cd automatic-projector-lens-memory
cp .env.example .env
cp docker-compose.example.yaml docker-compose.yaml
```

Set `MQTT_HOST` in `.env`. Add MQTT credentials when the broker requires them. Add Plex values only when you want rating-key lookup.

Start the container:

```sh
docker compose up -d
docker compose logs -f
```

## Import the Home Assistant blueprints

Create one automation from each blueprint:

- **Publish Playback Events** — [![Import Publish Playback Events](https://my.home-assistant.io/badges/blueprint_import.svg)](https://my.home-assistant.io/redirect/blueprint_import/?blueprint_url=https%3A%2F%2Fgithub.com%2FSawtaytoes%2Fautomatic-projector-lens-memory%2Fblob%2Fmain%2Fblueprints%2Flens_memory_playback_events.yaml)
  Select the media players that can drive lens changes. The automation publishes events to `lens-memory/event`.
- **Control Projector** — [![Import Control Projector](https://my.home-assistant.io/badges/blueprint_import.svg)](https://my.home-assistant.io/redirect/blueprint_import/?blueprint_url=https%3A%2F%2Fgithub.com%2FSawtaytoes%2Fautomatic-projector-lens-memory%2Fblob%2Fmain%2Fblueprints%2Flens_memory_projector_control.yaml)
  Select the projector remote and map the target sensor state to its remote command.

The service publishes MQTT discovery for `sensor.lens_memory_aspect_ratio` and `sensor.lens_memory_target_mode`. No helper entity is required.

## Environment variables

The complete example is [`.env.example`](../.env.example).

| Variable | Default | Purpose |
| --- | --- | --- |
| `MQTT_HOST` | required | MQTT broker host. |
| `MQTT_PORT` | `1883` | MQTT broker port. |
| `MQTT_USERNAME` / `MQTT_PASSWORD` | unset | Optional broker credentials. |
| `MQTT_TOPIC_PREFIX` | `lens-memory` | Base topic for commands and state. |
| `MQTT_DISCOVERY_PREFIX` | `homeassistant` | Home Assistant MQTT discovery prefix. |
| `PLEX_URL` | unset | Plex server base URL. |
| `PLEX_TOKEN` | unset | Plex API token. Keep it outside git. |
| `PLEX_VERIFY_TLS` | `true` | Set to `false` only for a self-signed Plex certificate. |
| `ASPECT_RATIOS_JSON_PATH` | `/data/aspectRatioCalculations.json` | Optional local database path. |
| `ASPECT_RATIO_CALCULATION` | `relativeMedianAspectRadio` | Field selected from each database record. |
| `BLURAY_COM_FALLBACK` | `true` | Enables the best-effort metadata fallback. |
| `LENS_MODE_MAPPING` | built-in JVC example | JSON object that maps ratios to remote commands. |
| `LENS_MODE_TOLERANCE` | `0.05` | Maximum difference for a nearest-ratio match. |
| `LENS_MODE_IDLE` | `mode_1` | Command published when playback stops. |
| `LOG_LEVEL` | `INFO` | Application log level. |

## Map aspect ratios to commands

`LENS_MODE_MAPPING` values are opaque command names. Replace them with the names that your Home Assistant remote accepts.

```json
{"2.39":"mode_2","2.10":"mode_4","1.85":"mode_3","1.78":"mode_1","1.37":"mode_1","1.33":"mode_1"}
```

The service selects the nearest configured ratio within `LENS_MODE_TOLERANCE`. A measured ratio of `2.40` can therefore use the `2.39` mapping.

## Add a local aspect-ratio database

Mount the JSON file at the path in `ASPECT_RATIOS_JSON_PATH`. The Compose example mounts `./data` read-only at `/data`.

```json
{
  "/media/Movies/Example (2026).mkv": {
    "relativeMedianAspectRadio": "2.39"
  }
}
```

Plex supplies the media file path for a rating key. That path must match the database key.

The blu-ray.com fallback can return no result or be rate-limited. The service then publishes `unknown` and does not send a projector command.

## Verify

1. Confirm the service connects to MQTT.
2. Confirm both discovered sensors appear in Home Assistant.
3. Start media on one configured player.
4. Confirm `sensor.lens_memory_aspect_ratio` receives a ratio.
5. Confirm `sensor.lens_memory_target_mode` receives the expected command.
6. Confirm the projector automation sends that command to the selected remote.

See [Troubleshooting](troubleshooting.md) when the lookup or command does not complete.
