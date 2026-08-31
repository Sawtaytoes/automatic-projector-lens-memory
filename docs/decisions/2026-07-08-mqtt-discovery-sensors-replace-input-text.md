# MQTT discovery sensors replace the input-text helper

- **Status:** Accepted
- **Date:** 2026-07-08
- **Type:** Home Assistant integration
- **Supersedes:** The manually created aspect-ratio `input_text` helper
- **Superseded by:** None

## Decision

The service publishes retained MQTT discovery sensors for current aspect ratio and target mode. Home Assistant does not need a manually created `input_text` helper.

## Context

The old helper stored the current ratio and also acted as a duplicate-command gate.

## Why

Discovery removes manual helper setup. Retained values restore sensor state, and the control blueprint ignores unchanged or unknown transitions, which preserves duplicate suppression.

## Evidence

Commit `7424c56` recorded the sensor model. `lens_memory/mqtt_service.py` publishes discovery and the control blueprint applies the state-change guard.
