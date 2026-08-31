# A standalone service replaces Home Assistant shell commands

- **Status:** Accepted
- **Date:** 2026-07-08
- **Type:** Architecture / deployment
- **Supersedes:** The Home Assistant-only shell-command implementation
- **Superseded by:** None

## Decision

Aspect-ratio resolution runs as an independently deployed service. Home Assistant sends playback events and applies the selected projector command, but it does not execute the resolver scripts.

## Context

The original implementation used three Home Assistant `shell_command` entries, Python dependencies inside the Home Assistant container, and a Plex token in automation configuration.

## Why

The service has an isolated environment, unit tests, CI, and container deployment. Plex credentials stay in its runtime environment, and the resolver can support callers that do not share the original Home Assistant layout.

## Evidence

The original implementation is preserved in [`docs/original-home-assistant-implementation.md`](../original-home-assistant-implementation.md). Commit `7424c56` recorded this architecture when the service replaced it.
