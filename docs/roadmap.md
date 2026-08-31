# Roadmap

These items are planned or exploratory. They are not supported behavior yet.

- Add a direct Plex session source that does not require Home Assistant for Plex playback.
- Add a Kodi JSON-RPC source that provides file paths directly.
- Bundle an aspect-ratio scanner that can generate `aspectRatioCalculations.json`.
- Add a Home Assistant `select` entity for a manual mode override.

Each direct playback source must emit the existing `PlaybackEvent` contract so it does not fork the resolution and publish pipeline.
