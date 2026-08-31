# Playback events normalize all input sources

- **Status:** Accepted
- **Date:** 2026-07-08
- **Type:** Architecture / domain model
- **Supersedes:** Source-specific resolver input
- **Superseded by:** None

## Decision

Every playback adapter emits the shared `PlaybackEvent` shape. The resolver consumes that shape and does not branch on the native source protocol.

## Context

The current adapter receives Home Assistant state, while planned Plex and Kodi adapters have different native payloads.

## Why

A new source adds translation at the edge without duplicating aspect-ratio resolution, mode selection, or MQTT publishing.

## Evidence

Commit `7424c56` recorded the source-agnostic pipeline. `lens_memory/events.py` defines the shared event model used by the resolver.
