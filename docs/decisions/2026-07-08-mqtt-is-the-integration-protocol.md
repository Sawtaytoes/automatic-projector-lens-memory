# MQTT is the integration protocol

- **Status:** Accepted
- **Date:** 2026-07-08
- **Type:** Architecture / integration
- **Supersedes:** Direct shell-command coupling
- **Superseded by:** None

## Decision

The service exchanges playback events, availability, aspect ratio, and target mode through MQTT. It does not add a REST bridge or shell integration.

## Context

Home Assistant already has an MQTT integration and broker in the target deployment. Other playback sources and observers can also use the protocol.

## Why

MQTT keeps the resolver independent of Home Assistant internals. Discovery creates the sensor entities, retained state restores their values, and a Last Will reports service availability.

## Evidence

Commit `7424c56` recorded MQTT as the service boundary. The blueprints, `lens_memory/mqtt_service.py`, and the published topic contract implement it.
