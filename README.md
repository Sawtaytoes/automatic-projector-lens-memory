# Automatic Projector Lens Memory

Automatic Projector Lens Memory recalls a projector lens-memory preset from the aspect ratio of the current media. Home Assistant publishes playback events, the service resolves an aspect ratio, and a second Home Assistant automation sends the matching command to the projector remote.

**[Set up the Docker service and Home Assistant →](docs/setup.md)**

```text
Home Assistant → MQTT → lens-memory service → MQTT discovery → Home Assistant → projector
```

## What it provides

- Playback events from any Home Assistant `media_player` entity.
- Exact Plex and local-database aspect-ratio lookup when available.
- A best-effort blu-ray.com fallback.
- Configurable ratio-to-command mapping with a numeric tolerance.
- MQTT discovery for current aspect ratio and target mode.
- A container deployment with no Plex token in Home Assistant configuration.

## Quick start

```sh
cp .env.example .env
cp docker-compose.example.yaml docker-compose.yaml
# Set MQTT_HOST and any optional Plex values in .env.
docker compose up -d
```

Import and configure both Home Assistant blueprints from the [setup guide](docs/setup.md).

## Documentation

- [Setup and configuration](docs/setup.md)
- [Architecture and MQTT contract](docs/architecture.md)
- [Troubleshooting](docs/troubleshooting.md)
- [Roadmap](docs/roadmap.md)
- [Original Home Assistant implementation](docs/original-home-assistant-implementation.md)
- [Architecture decisions](docs/decisions/README.md)

## Development

```sh
uv venv && . .venv/bin/activate
pip install -e '.[dev]'
pytest
ruff check .
```

## License

MIT.
