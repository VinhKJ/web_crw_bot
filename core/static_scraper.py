"""
static_scraper.py
------------------

Provides a simple interface for scraping static web pages using
Requests and BeautifulSoup. Given a URL and a CSS selector, the
``scrape`` function returns a list of dictionaries containing the
extracted text and, optionally, attribute values. The logic is
encapsulated in a class to facilitate future extensions, such as
handling pagination or additional extraction strategies.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Dict, Optional

import requests
from bs4 import BeautifulSoup


@dataclass
class ScrapedItem:
    """Represents a single extracted item from a web page."""

    text: str
    attrs: Dict[str, str]


class StaticScraper:
    """Utility class for scraping static pages via Requests and BeautifulSoup."""

    @staticmethod
    def scrape(url: str, selector: str, attr: Optional[str] = None) -> List[ScrapedItem]:
        """
        Fetch the given URL, parse it and extract elements matching the CSS
        selector. For each element found, return its text and a dictionary of
        attributes (optionally limited to a single attribute).

        Parameters
        ----------
        url : str
            The full URL of the page to scrape.
        selector : str
            A CSS selector string used to locate elements within the page.
        attr : Optional[str]
            If provided, only this attribute value will be captured for
            each element. Otherwise all attributes of the element are
            returned.

        Returns
        -------
        List[ScrapedItem]
            A list of ScrapedItem instances containing the extracted
            content.
        """
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
        items: List[ScrapedItem] = []
        for element in soup.select(selector):
            text_content = element.get_text(strip=True)
            if attr:
                # Only include the requested attribute if present
                value = element.get(attr)
                attrs = {attr: value} if value is not None else {}
            else:
                attrs = dict(element.attrs)
            items.append(ScrapedItem(text=text_content, attrs=attrs))
        return items