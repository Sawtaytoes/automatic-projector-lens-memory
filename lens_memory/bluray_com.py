"""Blu-ray.com aspect-ratio fallback scraper.

Used when the local aspect-ratio JSON has no entry for the playing media. Given
a title (and optional year) it searches blu-ray.com and extracts the aspect
ratio from the "Technical details" row.

Ported from the original ``get_bluraycom_aspect_ratio.py`` HA shell script.
Changes from the original:
  * Fixes the ``NameError``: the original referenced ``query`` before it was
    defined when a year was supplied. Year is now folded into the search term.
  * Adds a request timeout and treats every failure as a soft miss (``None``)
    so brittle/bot-blocked scraping never crashes the service. The original
    returned the sentinel string ``"NO_MATCH"``.
"""

from __future__ import annotations

import logging
import urllib.parse
from typing import Optional

import requests
from lxml import html

logger = logging.getLogger(__name__)

_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36"
)
_ASPECT_XPATH = (
    '//tr[td[@class="specmenu" and contains(text(), "Technical details")]]'
    '/td[@class="specitem"]/text()'
)


class BlurayComClient:
    def __init__(self, enabled: bool = True, timeout: float = 10.0):
        self.enabled = enabled
        self.timeout = timeout

    def get_aspect_ratio(self, title: Optional[str], year: Optional[int] = None) -> Optional[str]:
        """Return e.g. ``"2.39"`` for ``title`` (+ optional ``year``), or ``None``."""
        if not self.enabled or not title:
            return None

        search_term = f"{title} {year}" if year else title
        url = (
            "https://www.blu-ray.com/search/"
            f"?quicksearch=1&quicksearch_keyword={urllib.parse.quote(search_term)}"
            "&section=theatrical"
        )
        try:
            response = requests.get(
                url,
                headers={"User-Agent": _USER_AGENT},
                timeout=self.timeout,
            )
            response.raise_for_status()
        except requests.RequestException as error:
            logger.warning("blu-ray.com search for %r failed: %s", search_term, error)
            return None

        try:
            document = html.fromstring(response.content)
            matches = document.xpath(_ASPECT_XPATH)
        except (ValueError, TypeError) as error:
            logger.warning("Could not parse blu-ray.com response for %r: %s", search_term, error)
            return None

        if not matches:
            logger.info("No aspect ratio on blu-ray.com for %r", search_term)
            return None
        return matches[0].strip().replace(":1", "")
