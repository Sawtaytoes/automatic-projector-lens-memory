# Lens-mode mapping is configurable and tolerant

- **Status:** Accepted
- **Date:** 2026-07-08
- **Type:** Product / configuration
- **Supersedes:** Exact string comparison in the original blueprint
- **Superseded by:** None

## Decision

`LENS_MODE_MAPPING` is a JSON object whose keys are aspect ratios and whose values are opaque remote commands. The nearest configured ratio wins when it is within `LENS_MODE_TOLERANCE`.

## Context

Measured ratios can differ slightly from nominal values. Projectors and remote integrations also use different command names.

## Why

Tolerance maps values such as `2.40` to a configured `2.39` bucket. Opaque command values keep the service independent of a projector brand and preset naming scheme.

## Evidence

Commit `7424c56` recorded the configurable nearest-match policy. `lens_memory/mode_mapping.py` implements it.
