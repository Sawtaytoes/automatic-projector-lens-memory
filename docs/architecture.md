# Architecture and MQTT contract

Home Assistant acts as the playback-source adapter and projector-command adapter. The service owns aspect-ratio resolution and mode selection.

```text
media_player → HA blueprint → MQTT event → resolver → MQTT state → HA blueprint → remote command
```

## Playback events

Every source becomes a `PlaybackEvent` with `state`, `player`, `rating_key`, `title`, and `year`. The resolver does not depend on the original player integration.

The Home Assistant blueprint is the current source because Home Assistant already normalizes many playback devices. A future direct source can emit the same event shape without changing resolution or publishing.

## Resolution order

For a playing event, the service tries these sources in order:

1. Plex resolves a rating key to the media file path.
2. The local JSON database maps that path to a measured aspect ratio.
3. The blu-ray.com fallback searches by title and year.

The fallback is best-effort. A failed lookup produces `unknown` and no projector command.

For an idle event, the service publishes `LENS_MODE_IDLE`.

## Mode selection

The selected aspect ratio is compared with each key in `LENS_MODE_MAPPING`. The nearest key wins when its difference is no greater than `LENS_MODE_TOLERANCE`.

The mapped value is an opaque remote command. Projector-specific behavior remains in configuration and the Home Assistant control blueprint.

## MQTT topics

The table uses the default `lens-memory` prefix.

| Topic | Direction | Retained | Payload |
| --- | --- | --- | --- |
| `lens-memory/event` | Subscribe | No | `{"state","player","rating_key","title","year"}`. |
| `lens-memory/status` | Publish | Yes | `online` or the last-will value `offline`. |
| `lens-memory/aspect-ratio/state` | Publish | Yes | A ratio such as `2.39`, or `unknown`. |
| `lens-memory/mode/state` | Publish | Yes | A configured command such as `mode_2`. |
| `lens-memory/attributes` | Publish | Yes | Source, media file path, and title metadata. |

MQTT discovery creates the Home Assistant sensors. Retained state restores their last values without a separate `input_text` helper.

See the [decision index](decisions/README.md) for the integration and resolution rationale.
