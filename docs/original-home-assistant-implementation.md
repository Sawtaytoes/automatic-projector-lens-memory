# Original Home Assistant implementation (archived)

This service replaces an earlier implementation that lived **entirely inside Home Assistant**
as `shell_command`s, Python scripts, a blueprint, and one automation. That approach is
preserved here for reference and to show how each piece maps onto the new MQTT service.

It was removed from Home Assistant on 2026-07-08 (the `shell_command` block held a **plaintext
Plex token**). Everything below is the *old* design — you do **not** need any of it to run this
service; import the two blueprints in [`../blueprints/`](../blueprints/) instead.

## How it worked

1. A single automation (from the blueprint below) triggered on `media_player` → `playing` /
   `idle` / `unavailable`.
2. On `playing`, for a Plex player it called `shell_command.get_plex_media_file_path` (Plex
   HTTP API, rating key → file path), then `shell_command.get_aspect_ratio` (look the path up
   in a local JSON database).
3. If that returned `NONE` and the media had a title, it called
   `shell_command.get_bluraycom_aspect_ratio` (scrape blu-ray.com).
4. A `choose:` mapped the aspect-ratio string to a `remote.send_command` (`mode_1`..`mode_4`)
   and stored the current value in an `input_text` helper (used as a dedup gate).
5. On `idle`/`unavailable` it reset the helper to `NONE` and sent `mode_1`.

## Old → new mapping

| Old (in Home Assistant) | New (in this repo) |
| --- | --- |
| `shell_command.get_plex_media_file_path` + `/config/scripts/get_plex_media_file_path.py` | [`lens_memory/plex.py`](../lens_memory/plex.py) (TLS now configurable, timeouts, soft-fail) |
| `shell_command.get_aspect_ratio` + `/config/scripts/get_aspect_ratio.py` | [`lens_memory/aspect_ratios.py`](../lens_memory/aspect_ratios.py) |
| `shell_command.get_bluraycom_aspect_ratio` + `/config/scripts/get_bluraycom_aspect_ratio.py` | [`lens_memory/bluray_com.py`](../lens_memory/bluray_com.py) (`query` NameError fixed; best-effort) |
| `choose:` aspect-ratio → remote command, in the blueprint | [`lens_memory/mode_mapping.py`](../lens_memory/mode_mapping.py) (nearest-match within tolerance) |
| `input_text` current-aspect-ratio helper + dedup gate | MQTT-discovery sensors + retained state (no helper) |
| The one big blueprint (sensing **and** control) | Split into [`lens_memory_playback_events.yaml`](../blueprints/lens_memory_playback_events.yaml) + [`lens_memory_projector_control.yaml`](../blueprints/lens_memory_projector_control.yaml) |
| Plex token as a **plaintext blueprint input** in `automations.yaml` | `PLEX_TOKEN` env var, only in the service |

---

## Archived source

### `configuration.yaml` — `shell_command:` block (lens entries only)

```yaml
shell_command:
  # Plex Hookup for Projector Lens Memory
  get_aspect_ratio: >
    python3 /config/scripts/get_aspect_ratio.py --aspect_ratio_calculations_file_path "{{ aspect_ratio_calculations_file_path }}" --aspect_ratio_calculation_type {{ aspect_ratio_calculation_type }} --plex_media_file_path "{{ plex_media_file_path }}"

  # Generic Hookup for Projector Lens Memory
  get_bluraycom_aspect_ratio: >
    python3 /config/scripts/get_bluraycom_aspect_ratio.py --title "{{ title }}" --year "{{ year }}"

  # Plex Hookup for Projector Lens Memory
  get_plex_media_file_path: >
    python3 /config/scripts/get_plex_media_file_path.py --plex_server_domain "{{ plex_server_domain }}" --plex_server_port "{{ plex_server_port }}" --plex_token "{{ plex_token }}" --rating_key "{{ rating_key }}"
```

### `/config/scripts/get_aspect_ratio.py`

```python
import argparse
import json

parser = argparse.ArgumentParser()

parser.add_argument('--aspect_ratio_calculations_file_path', required=True)
parser.add_argument('--aspect_ratio_calculation_type', required=True)
parser.add_argument('--plex_media_file_path', required=True)

args = parser.parse_args()

with open(args.aspect_ratio_calculations_file_path) as file:
    aspect_ratio_calculations = json.load(file)

aspect_ratio = aspect_ratio_calculations.get(args.plex_media_file_path, {}).get(args.aspect_ratio_calculation_type, "NONE")
print(aspect_ratio)
```

### `/config/scripts/get_plex_media_file_path.py`

```python
import argparse
import requests
import urllib3
import xml.etree.ElementTree as ElementTree

parser = argparse.ArgumentParser()

parser.add_argument('--plex_server_domain', required=True)
parser.add_argument('--plex_server_port', required=False, default='32400')
parser.add_argument('--plex_token', required=True)
parser.add_argument('--rating_key', required=True)

args = parser.parse_args()

# Disables HTTPS insecure connection warnings.
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

plex_url = f"https://{args.plex_server_domain}:{args.plex_server_port}/library/metadata/{args.rating_key}?X-Plex-Token={args.plex_token}"

xml_response = requests.get(plex_url, verify=False).text

if not xml_response.strip().startswith("<?xml"):
    raise ValueError("Did not receive valid XML:\n" + xml_response)

root = ElementTree.fromstring(xml_response)
file_path = root.find('.//Part').attrib['file']

print(file_path)
```

> Note the `verify=False` (insecure TLS). The port in [`lens_memory/plex.py`](../lens_memory/plex.py)
> makes this a `PLEX_VERIFY_TLS` toggle that defaults to `true`.

### `/config/scripts/get_bluraycom_aspect_ratio.py`

```python
import argparse
import requests
import urllib.parse
from lxml import html

parser = argparse.ArgumentParser()

parser.add_argument('--title', required=True)
parser.add_argument('--year', required=False, default='')

args = parser.parse_args()

def search_title_and_get_aspect_ratio(title, year=None):
    encoded_title = urllib.parse.quote(title)

    if year:
        query += f" ({year})"   # BUG: `query` is undefined here → NameError when a year is passed

    url = f"https://www.blu-ray.com/search/?quicksearch=1&quicksearch_keyword={encoded_title}&section=theatrical"

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.7151.120 Safari/537.36"
    }

    html_response = requests.get(url, headers=headers)
    html_document = html.fromstring(html_response.content)

    aspect_ratio = html_document.xpath(
        '//tr[td[@class="specmenu" and contains(text(), "Technical details")]]/td[@class="specitem"]/text()'
    )

    if aspect_ratio:
        return aspect_ratio[0].strip().replace(":1", "")
    else:
        return "NO_MATCH"

print(search_title_and_get_aspect_ratio(args.title, args.year))
```

> Two problems carried into the rewrite as known limitations: (1) the `query` `NameError` is
> **fixed** in [`lens_memory/bluray_com.py`](../lens_memory/bluray_com.py); (2) the XPath targets
> a movie *detail* page while this URL returns a *search* page, so the fallback is best-effort
> and often returns nothing — the Plex + JSON path is the reliable one.

### Blueprint `Sawtaytoes/control_projector_lens_memory.yaml`

The single old blueprint did both sensing and control and required a Plex token as an input.
Its full source is preserved below.

```yaml
blueprint:
  name: Change Lens Memory Based on Content
  description: |
    Automatically switches JVC projector lens memory based on the aspect ratio
    of the currently playing Plex content, using either file-based or Blu-ray.com data.
  domain: automation
  input:
    media_players:
      name: Media Players
      selector:
        entity:
          multiple: true
          domain: media_player
    projector_remote:
      name: JVC Projector Remote
      selector:
        entity:
          domain: remote
    current_aspect_ratio:
      name: Current Aspect Ratio
      # A text (input_text) helper holding NONE / NO_MATCH / 2.39 / 2.10 / 1.85 / 1.78 / 1.37 / 1.33
      selector:
        entity:
          domain: input_text
    plex_server_domain:
      name: Plex Server Domain
      selector:
        text:
    plex_server_port:
      name: Plex Server Port
      default: 32400
      selector:
        number:
          min: 1
          max: 65535
          mode: box
    plex_token:
      name: Plex Token   # <-- stored in plaintext in automations.yaml; eliminated in the rewrite
      selector:
        text:
    aspect_ratio_calculations_file_path:
      name: Aspect Ratio Calculations File Path
      selector:
        text:

trigger:
  - platform: state
    entity_id: !input media_players
    to: playing
    id: Playing
  - platform: state
    entity_id: !input media_players
    to: idle
    id: Idle
  - platform: state
    entity_id: !input media_players
    to: unavailable
    id: Idle

condition: []

action:
  - alias: Configure Media Players variable
    variables:
      media_players_variable: !input media_players
  - alias: Set aspect ratio from JSON data
    if:
      - condition: template
        value_template: "{{ trigger.to_state.attributes.media_content_id is defined }}"
      - condition: template
        value_template: >
          {{ expand(media_players_variable)
            | selectattr('state', 'equalto', 'playing')
            | selectattr('entity_id', 'match', '^media_player\\.plex')
            | list | count > 0 }}
    then:
      - service: shell_command.get_plex_media_file_path
        data:
          plex_server_domain: !input plex_server_domain
          plex_server_port: !input plex_server_port
          plex_token: !input plex_token
          rating_key: "{{ trigger.to_state.attributes.media_content_id }}"
        response_variable: plex_media_file_path
      - service: shell_command.get_aspect_ratio
        data:
          aspect_ratio_calculations_file_path: !input aspect_ratio_calculations_file_path
          aspect_ratio_calculation_type: relativeMedianAspectRadio
          plex_media_file_path: "{{ plex_media_file_path.stdout }}"
        response_variable: aspect_ratio
  - alias: Set aspect ratio based on Blu-ray.com
    if:
      - condition: template
        value_template: "{{ aspect_ratio is not defined or aspect_ratio is defined and aspect_ratio.stdout == 'NONE' }}"
      - condition: template
        value_template: "{{ trigger.to_state.attributes.media_title is defined }}"
    then:
      - service: shell_command.get_bluraycom_aspect_ratio
        data:
          title: "{{ trigger.to_state.attributes.media_title }}"
          year: "{{ trigger.to_state.attributes.media_year }}"
        response_variable: aspect_ratio
  - alias: Set local aspect ratio value
    variables:
      aspect_ratio_entity: !input current_aspect_ratio
  - alias: Set Lens Memory
    if:
      - condition: template
        value_template: "{{ states(aspect_ratio_entity) == 'NONE' }}"
    then:
      - choose:
          - conditions:
              - condition: template
                value_template: "{{ aspect_ratio is defined and aspect_ratio.stdout == '2.39' }}"
            sequence:
              - service: input_text.set_value
                target: { entity_id: "{{ aspect_ratio_entity }}" }
                data: { value: "2.39" }
              - service: remote.send_command
                target: { entity_id: !input projector_remote }
                data: { num_repeats: 1, delay_secs: 0.4, hold_secs: 0, command: mode_2 }
          - conditions:
              - condition: template
                value_template: "{{ aspect_ratio is defined and aspect_ratio.stdout == '2.10' }}"
            sequence:
              - service: input_text.set_value
                target: { entity_id: "{{ aspect_ratio_entity }}" }
                data: { value: "2.10" }
              - service: remote.send_command
                target: { entity_id: !input projector_remote }
                data: { num_repeats: 1, delay_secs: 0.4, hold_secs: 0, command: mode_4 }
          - conditions:
              - condition: template
                value_template: "{{ aspect_ratio is defined and aspect_ratio.stdout == '1.85' }}"
            sequence:
              - service: input_text.set_value
                target: { entity_id: "{{ aspect_ratio_entity }}" }
                data: { value: "1.85" }
              - service: remote.send_command
                target: { entity_id: !input projector_remote }
                data: { num_repeats: 1, delay_secs: 0.4, hold_secs: 0, command: mode_3 }
          - conditions:
              - condition: template
                value_template: "{{ aspect_ratio is defined and (aspect_ratio.stdout == '1.78' or aspect_ratio.stdout == '1.37' or aspect_ratio.stdout == '1.33') }}"
            sequence:
              - service: input_text.set_value
                target: { entity_id: "{{ aspect_ratio_entity }}" }
                data: { value: "1.85" }
              - service: remote.send_command
                target: { entity_id: !input projector_remote }
                data: { num_repeats: 1, delay_secs: 0.4, hold_secs: 0, command: mode_1 }
  - alias: Reset Lens Memory
    if:
      - condition: trigger
        id: Idle
      - condition: template
        value_template: "{{ states(aspect_ratio_entity) != 'NONE' }}"
    then:
      - service: input_text.set_value
        target: { entity_id: "{{ aspect_ratio_entity }}" }
        data: { value: "NONE" }
      - service: remote.send_command
        target: { entity_id: !input projector_remote }
        data: { num_repeats: 1, delay_secs: 0.4, hold_secs: 0, command: mode_1 }

mode: restart
```

### The aspect-ratio JSON database

Unchanged in shape — the service reads the same file. Keyed by the media **file path** Plex
reports:

```json
{
  "/media/Movies/Interstellar (2014).mkv": {
    "exactMaxHeightAspectRatio": "2.40",
    "exactMedianAspectRadio": "2.39",
    "relativeMaxHeightAspectRatio": "2.40",
    "relativeMedianAspectRadio": "2.39"
  }
}
```

Generating it is the job of a separate scanner (Mux-Magic / `media-tools`); bundling that
generator into this repo is on the [roadmap](../README.md#roadmap).
