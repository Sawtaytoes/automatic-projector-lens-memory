"""Plex metadata lookup: rating key -> on-disk media file path.

Ported from the original ``get_plex_media_file_path.py`` HA shell script.
Changes from the original:
  * TLS verification is configurable (was hard-coded ``verify=False``).
  * A request timeout is enforced so a hung Plex never wedges the resolver.
  * Network/parse failures return ``None`` instead of raising.
"""

from __future__ import annotations

import logging
from xml.etree import ElementTree

import requests
import urllib3

logger = logging.getLogger(__name__)


class PlexClient:
    def __init__(
        self,
        base_url: str | None,
        token: str | None,
        verify_tls: bool = True,
        timeout: float = 10.0,
    ):
        # base_url like "https://plex.example.com:32400" (no trailing slash).
        self.base_url = base_url.rstrip("/") if base_url else None
        self.token = token
        self.verify_tls = verify_tls
        self.timeout = timeout
        if not verify_tls:
            # The user opted out of verification (self-signed Plex cert); silence
            # the resulting per-request warning spam.
            urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

    @property
    def enabled(self) -> bool:
        return bool(self.base_url and self.token)

    def get_media_file_path(self, rating_key: str) -> str | None:
        """Return the file path of the first Part for ``rating_key`` or ``None``."""
        if not self.enabled or not rating_key:
            return None

        url = f"{self.base_url}/library/metadata/{rating_key}"
        try:
            response = requests.get(
                url,
                params={"X-Plex-Token": self.token},
                verify=self.verify_tls,
                timeout=self.timeout,
            )
            response.raise_for_status()
        except requests.RequestException as error:
            logger.warning("Plex request for rating_key=%s failed: %s", rating_key, error)
            return None

        try:
            root = ElementTree.fromstring(response.text)
        except ElementTree.ParseError as error:
            logger.warning("Plex returned unparseable XML for rating_key=%s: %s", rating_key, error)
            return None

        part = root.find(".//Part")
        if part is None or "file" not in part.attrib:
            logger.info("No media Part/file found for rating_key=%s", rating_key)
            return None
        return part.attrib["file"]
