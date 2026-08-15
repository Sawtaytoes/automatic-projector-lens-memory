# Automatic-Projector-Lens-Memory

Automatically recall your projector's **lens-memory** preset based on the aspect
ratio of whatever's playing — so 2.39:1 films fill your scope screen and 1.85:1
content zooms to fit, with no manual button-pushing.

It's a small MQTT service. Home Assistant tells it what's playing; it figures
out the aspect ratio (from Plex + a local database, falling back to blu-ray.com)
and publishes the matching lens-memory mode back to Home Assistant, which fires
the command at your projector's remote.

```
Home Assistant (blueprint #1)         this service (Docker)                 Home Assistant (blueprint #2)
media_player → playing/idle           MQTT subscriber                       MQTT-discovery sensor
   └─ mqtt.publish ───────▶ lens-memory/event ──▶ resolve aspect ratio:     sensor.lens_memory_target_mode
                                        1. Plex API → file path                 └─ state change
                                        2. aspectRatioCalculations.json             └─ remote.send_command
                                        3. blu-ray.com fallback                          (mode_1 … mode_4)
                                        └─ aspect ratio → mode → MQTT
```

## Why route through Home Assistant?

Home Assistant already integrates with nearly every streaming box — Apple TV,
Roku, Nvidia Shield, Plex, and more — and normalizes them into `media_player`
entities. Rather than re-implement each integration, this service consumes those
events over MQTT. **Plex is the richest source**: it exposes a rating key that
maps to an exact, per-title aspect ratio in your local database. Other players
fall back to a title/year lookup on blu-ray.com.

> Direct Plex and Kodi sources (no Home Assistant required) are on the roadmap —
> see [Roadmap](#roadmap).

## Requirements

- An MQTT broker (Home Assistant's Mosquitto add-on is perfect).
- Home Assistant with the MQTT integration.
- A projector whose lens-memory presets can be recalled through a Home Assistant
  `remote` entity (e.g. a JVC via an IR/IP remote such as an Unfolded Circle
  Remote, Harmony, or Broadlink).
- **Optional:** a Plex server + token for exact aspect-ratio lookups.
- **Optional:** an `aspectRatioCalculations.json` database (see
  [Aspect-ratio database](#aspect-ratio-database)).

## Quick start

```bash
git clone https://github.com/Sawtaytoes/automatic-projector-lens-memory.git
cd automatic-projector-lens-memory
cp .env.example .env
# edit .env — at minimum set MQTT_HOST (and Plex if you use it)
cp docker-compose.example.yaml docker-compose.yaml
docker compose up -d
```

Then import the two Home Assistant blueprints below and create an automation
from each.

## Home Assistant setup

Import both blueprints (click, then **Create Automation**):

- **Publish Playback Events** — [![Import](https://my.home-assistant.io/badges/blueprint_import.svg)](https://my.home-assistant.io/redirect/blueprint_import/?blueprint_url=https%3A%2F%2Fgithub.com%2FSawtaytoes%2Fautomatic-projector-lens-memory%2Fblob%2Fmain%2Fblueprints%2Flens_memory_playback_events.yaml)
  Add your media players. Publishes playback to `lens-memory/event`.
- **Control Projector** — [![Import](https://my.home-assistant.io/badges/blueprint_import.svg)](https://my.home-assistant.io/redirect/blueprint_import/?blueprint_url=https%3A%2F%2Fgithub.com%2FSawtaytoes%2Fautomatic-projector-lens-memory%2Fblob%2Fmain%2Fblueprints%2Flens_memory_projector_control.yaml)
  Pick your projector `remote`. Reacts to `sensor.lens_memory_target_mode`.

The service publishes MQTT discovery, so `sensor.lens_memory_aspect_ratio` and
`sensor.lens_memory_target_mode` appear automatically — no helper entities to
create (the old `input_text` approach is gone).

## Configuration

All configuration is via environment variables (see `.env.example`):

| Variable | Default | Description |
| --- | --- | --- |
| `MQTT_HOST` | *(required)* | MQTT broker host |
| `MQTT_PORT` | `1883` | MQTT broker port |
| `MQTT_USERNAME` / `MQTT_PASSWORD` | — | MQTT credentials (if required) |
| `MQTT_TOPIC_PREFIX` | `lens-memory` | Base topic |
| `MQTT_DISCOVERY_PREFIX` | `homeassistant` | HA discovery prefix |
| `PLEX_URL` | — | e.g. `https://plex.example.com:32400` |
| `PLEX_TOKEN` | — | Plex API token |
| `PLEX_VERIFY_TLS` | `true` | Set `false` for a self-signed Plex cert |
| `ASPECT_RATIOS_JSON_PATH` | `/data/aspectRatioCalculations.json` | Local aspect-ratio database (optional) |
| `ASPECT_RATIO_CALCULATION` | `relativeMedianAspectRadio` | Which calc field to read |
| `BLURAY_COM_FALLBACK` | `true` | Enable blu-ray.com fallback |
| `LENS_MODE_MAPPING` | see below | Aspect ratio → remote command (JSON) |
| `LENS_MODE_TOLERANCE` | `0.05` | Nearest-match tolerance |
| `LENS_MODE_IDLE` | `mode_1` | Mode sent when playback stops |
| `LOG_LEVEL` | `INFO` | Log level |

### Mode mapping

`LENS_MODE_MAPPING` maps an aspect ratio to the command name your projector
remote understands. The default matches a JVC lens-memory preset remote:

```json
{"2.39":"mode_2","2.10":"mode_4","1.85":"mode_3","1.78":"mode_1","1.37":"mode_1","1.33":"mode_1"}
```

The values are opaque — set them to whatever command names your remote uses.
Matching is nearest-within-tolerance, so a scanned `2.40` still resolves to the
`2.39` bucket.

## Aspect-ratio database

`aspectRatioCalculations.json` maps a media **file path** (as Plex reports it) to
its measured aspect ratio(s):

```json
{
  "/media/Movies/Interstellar (2014).mkv": {
    "relativeMedianAspectRadio": "2.39"
  }
}
```

Generating this file (scanning your library for actual displayed aspect ratios,
including movies with varying/IMAX ratios) is done by a separate scanner. This
JSON, populated from Plex file paths, is the **reliable** source of aspect
ratios.

> **blu-ray.com fallback is best-effort.** When a title isn't in the JSON, the
> service tries blu-ray.com — but the site actively resists scraping and often
> returns nothing. Treat it as a bonus, not a substitute for the JSON database.
> Failures are logged and resolve to `unknown` (no projector command sent).

## MQTT topics

| Topic | Direction | Retained | Payload |
| --- | --- | --- | --- |
| `lens-memory/event` | in | no | `{"state","player","rating_key","title","year"}` |
| `lens-memory/status` | out | yes | `online` / `offline` (LWT availability) |
| `lens-memory/aspect-ratio/state` | out | yes | e.g. `2.39` or `unknown` |
| `lens-memory/mode/state` | out | yes | e.g. `mode_2` |
| `lens-memory/attributes` | out | yes | `{"source","media_file_path","title"}` |

## Roadmap

- **Plex-direct source** — poll Plex sessions so no Home Assistant is needed for
  Plex playback.
- **Kodi source** — Kodi JSON-RPC notifications (gives file paths directly).
- **Bundled aspect-ratio scanner** — generate `aspectRatioCalculations.json`
  from your library in this same package.
- **Manual override** — a `select` entity to force a mode.

## Documentation

- [Design decisions](docs/design-decisions.md) — why MQTT, why HA is the input source, the
  source-agnostic pipeline, and the blu-ray.com caveat.
- [Original Home Assistant implementation](docs/original-home-assistant-implementation.md) —
  the archived `shell_command` + scripts + blueprint this replaced, with an old→new mapping.

## Development

```bash
uv venv && . .venv/bin/activate    # or python -m venv
pip install -e ".[dev]"
pytest
ruff check .
```

## Troubleshooting

- **Sensors don't appear in HA** — confirm the MQTT integration is set up and the
  service connected (`docker logs`); discovery is published on connect.
- **Mode never changes** — check `lens-memory/aspect-ratio/state`; `unknown`
  means neither Plex/JSON nor blu-ray.com found a ratio. Watch topics with
  `mosquitto_sub -t 'lens-memory/#' -v`.
- **blu-ray.com returns nothing** — scraping is best-effort and can be
  rate-limited; failures are logged and treated as `unknown`, never fatal.
- **Retained mode on HA restart** — the control blueprint ignores a sensor value
  that restores unchanged, so your projector isn't re-commanded on restart.

## License

MIT © 2026 Kevin Ghadyani
