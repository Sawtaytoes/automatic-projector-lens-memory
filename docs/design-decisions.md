# Design decisions

Why this project is shaped the way it is. See
[`original-home-assistant-implementation.md`](./original-home-assistant-implementation.md)
for the Home-Assistant-only version this replaced.

## 1. A standalone service, not Home Assistant `shell_command`s

The original ran as three `shell_command`s calling Python scripts from inside HA's
`configuration.yaml`, plus a blueprint and an automation. That coupled the logic to HA,
required Python (and `requests`/`lxml`) available in the HA container, and — worst — stored a
**Plex token in plaintext** in `automations.yaml`.

Pulling it into a standalone service makes it: independently deployable (a container anywhere),
testable (unit tests, CI), reusable by people who don't run HA the same way, and free of
secrets in HA config — the Plex token now lives only in the service's environment.

## 2. MQTT as the integration protocol

The service and Home Assistant talk **only over MQTT**:

- HA already has an MQTT broker (Mosquitto) in most setups, and MQTT **discovery** lets the
  service create its own sensor entities with zero YAML on the HA side.
- It's decoupled and language-agnostic — anything that can publish/subscribe MQTT can drive or
  observe this service, not just HA.
- No new HTTP endpoints, REST bridges, or shell-outs to maintain.

The service publishes an availability topic as an MQTT **Last Will** so HA shows it as
unavailable if it dies.

## 3. Home Assistant is the input source (for v1)

HA is the input because it is the **universal integrator**: it already normalizes Apple TV,
Roku, Nvidia Shield, Plex, and many other players into `media_player` entities. Consuming those
events covers the widest range of hardware for the least code.

**Plex is the richest single source** — it exposes a rating key that resolves to an exact,
per-title aspect ratio in the local database. Other players contribute title/year only, which
the (best-effort) blu-ray.com fallback uses.

Direct **Plex** and **Kodi** sources — which would let the service run *without* Home Assistant
for those players — are intentionally deferred (see [roadmap](../README.md#roadmap)).

## 4. Source-agnostic pipeline (`PlaybackEvent`)

The resolver never knows where an event came from. Every input source converts its native
notification into a normalized [`PlaybackEvent`](../lens_memory/events.py)
(`state`, `player`, `rating_key`, `title`, `year`) and hands it to the resolver. Adding a Plex
or Kodi source later is a new file that emits `PlaybackEvent`s — the resolution/publish pipeline
doesn't change.

## 5. MQTT discovery sensors instead of an `input_text` helper

The old design stored the current aspect ratio in an `input_text` helper and used it as a
"don't re-send the same mode" gate. The service instead publishes **retained** MQTT-discovery
sensors (`sensor.lens_memory_aspect_ratio`, `sensor.lens_memory_target_mode`). HA doesn't fire a
state-change trigger when a retained value restores unchanged, and the control blueprint ignores
unchanged/unknown transitions — together replicating the old dedup gate with no helper to
hand-create.

## 6. Aspect ratio → mode mapping is nearest-match and user-configurable

The old blueprint did exact string equality (`'2.39'`, `'1.85'`, …). The service maps to the
**nearest configured ratio within a tolerance** (default 0.05), so a scanned `2.40` still lands
in the `2.39` bucket. The mapping is a JSON env var (`LENS_MODE_MAPPING`) whose values are opaque
remote-command strings, so it works with any projector/remote, not just a JVC's `mode_1..mode_4`.

## 7. blu-ray.com fallback is best-effort

blu-ray.com actively resists scraping, and its search page doesn't expose the technical-details
markup the original XPath expected — so this fallback frequently returns nothing. The port
**fixes the crash** the original had when a year was supplied (an undefined-variable `NameError`)
and fails gracefully to `unknown`, but the reliable path is Plex + the local JSON database.
Improving the fallback (follow the first result to its detail page, or use a non-scraping
metadata source) is future work.

## 8. Not run by its author

This was built for a friend with a lens-memory projector; the author's own projector has none.
It's therefore developed as a generic, well-documented OSS package rather than tuned to one
specific setup — placeholder examples, configurable everything, and no assumptions about a
particular Plex host, share path, or remote.
