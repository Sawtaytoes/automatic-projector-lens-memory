# The blu-ray.com fallback is best-effort

- **Status:** Accepted
- **Date:** 2026-07-08
- **Type:** Reliability / metadata
- **Supersedes:** Treating scraper output as a reliable source
- **Superseded by:** None

## Decision

The blu-ray.com lookup is an optional final fallback. A blocked, rate-limited, malformed, or empty response resolves to `unknown` and does not fail the service.

## Context

The site resists scraping, and search results do not always expose the expected technical data. Plex with the local measured database is the reliable path.

## Why

The fallback can improve sparse title-and-year events, but it cannot support a correctness guarantee. A no-result response must not send an unverified projector command.

## Evidence

Commit `7424c56` recorded the best-effort boundary after the port fixed an older year-related crash. `lens_memory/bluray_com.py` implements the non-fatal result.
