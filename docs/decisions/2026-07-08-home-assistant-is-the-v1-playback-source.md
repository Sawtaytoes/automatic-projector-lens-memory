# Home Assistant is the v1 playback source

- **Status:** Accepted
- **Date:** 2026-07-08
- **Type:** Product / integration scope
- **Supersedes:** None
- **Superseded by:** None

## Decision

The first supported playback source is a Home Assistant blueprint that converts selected `media_player` state into MQTT playback events. Direct Plex and Kodi sources remain future additions.

## Context

Home Assistant already normalizes many streaming devices. Plex can include a rating key for exact lookup, while other players can still provide title and year.

## Why

One adapter covers more player hardware with less source-specific code. The service remains useful with sparse events and improves resolution when richer Plex data is present.

## Evidence

Commit `7424c56` recorded the v1 source boundary. `blueprints/lens_memory_playback_events.yaml` is the supported adapter.
