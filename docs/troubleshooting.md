# Troubleshooting

## Sensors do not appear in Home Assistant

Confirm that the Home Assistant MQTT integration is configured and that the service connected to the broker. Check the service log for its connect and discovery messages.

Verify that `MQTT_DISCOVERY_PREFIX` matches the broker integration's discovery prefix.

## The target mode does not change

Inspect the aspect-ratio state:

```sh
mosquitto_sub -t 'lens-memory/#' -v
```

An `unknown` ratio means no configured lookup source found a value. Check the event rating key, Plex access, the exact database file path, and the selected `ASPECT_RATIO_CALCULATION` field.

If a ratio appears but no mode appears, compare it with `LENS_MODE_MAPPING` and `LENS_MODE_TOLERANCE`.

## Plex lookup fails

Confirm that `PLEX_URL` includes its scheme and port and that `PLEX_TOKEN` is valid. Leave `PLEX_VERIFY_TLS=true` for a valid certificate. Disable verification only for a self-signed certificate that you control.

The file path returned by Plex must exactly match a key in the local JSON database.

## blu-ray.com returns no value

The fallback uses scraping and can be rate-limited or blocked. This is a supported no-result state, not a fatal service error. Use Plex and the local JSON database for reliable exact lookup.

## The projector receives no command

Confirm that the target-mode sensor changes and that the Control Projector blueprint automation is enabled. Check its trace for the selected remote, mapped command, and conditions.

The mapping values must match commands that the Home Assistant remote entity accepts.

## Home Assistant restarts with a retained mode

Retained MQTT state restores the sensors. The control blueprint ignores an unchanged restored value, so it does not send the same projector command again only because Home Assistant restarted.
