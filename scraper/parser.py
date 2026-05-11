"""
parser.py
---------
Parses HTML pages from books.toscrape.com into structured Python objects.

This module has zero knowledge of HTTP — it only works with HTML strings.
That separation makes it trivially testable: pass in a string, get back
a list of Book objects. No network required.

Target site structure (books.toscrape.com):
  - Each book is in an <article class="product_pod">
  - Title is in the <a> tag inside <h3> (full title in the 'title' attribute)
  - Price is in <p class="price_color">
  - Rating is in <p class="star-rating {One|Two|Three|Four|Five}">
  - Availability is in <p class="instock availability"> or similar
  - Next page link is in <li class="next"><a href="...">
"""

import logging
from dataclasses import dataclass, field, asdict

from bs4 import BeautifulSoup

from .exceptions import ParseError

# Module-level logger. Uses the module's own name as the logger name
# so log output clearly shows which file the message came from.
logger = logging.getLogger(__name__)


# Maps the word-based rating class to an integer (1–5).
RATING_MAP = {
    "one": 1,
    "two": 2,
    "three": 3,
    "four": 4,
    "five": 5,
}


@dataclass
class Book:
    """
    Represents a single book scraped from books.toscrape.com.

    Using a dataclass gives us __repr__, __eq__, and easy dict/JSON
    conversion for free, without writing any boilerplate.

    Attributes
    ----------
    title : str
        Full book title.
    price_gbp : float
        Price in GBP (the site uses £).
    rating : int
        Star rating from 1 to 5.
    availability : str
        Stock status, e.g. "In stock".
    url : str
        Absolute URL to the book's detail page.
    """
    title: str
    price_gbp: float
    rating: int
    availability: str
    url: str = ""

    def to_dict(self) -> dict:
        """Return the book as a plain dictionary (for JSON export)."""
        return asdict(self)


def parse_books(html: str, base_url: str, page_url: str = "") -> list[Book]:
    """
    Parse all books from a single listing page's HTML.

    Parameters
    ----------
    html : str
        Raw HTML content of a books.toscrape.com catalogue page.
    base_url : str
        The root URL of the site (e.g. "https://books.toscrape.com"),
        used to build absolute URLs for each book.
    page_url : str, optional
        The URL this HTML came from, used for error messages.

    Returns
    -------
    list[Book]
        A list of Book objects parsed from the page. If a field cannot
        be extracted for a particular book, a safe default is used
        rather than crashing — partial data is better than no data.

    Raises
    ------
    ParseError
        If the page HTML contains no recognisable book articles at all,
        which suggests the site structure has changed.
    """
    soup = BeautifulSoup(html, "html.parser")
    articles = soup.select("article.product_pod")

    if not articles:
        raise ParseError(page_url, "No <article class='product_pod'> elements found")

    books = []

    for article in articles:
        try:
            title = _extract_title(article)
            price = _extract_price(article)
            rating = _extract_rating(article)
            availability = _extract_availability(article)
            url = _extract_url(article, base_url)

            books.append(Book(
                title=title,
                price_gbp=price,
                rating=rating,
                availability=availability,
                url=url,
            ))

        except Exception as e:
            # Skip a single broken article rather than crashing the whole page.
            # Log the exception so we know what was skipped and why —
            # silent failures are harder to debug than logged ones.
            logger.warning(
                "Skipped one article on page '%s' — %s: %s",
                page_url,
                type(e).__name__,
                e,
            )
            continue

    return books


def parse_next_page_url(html: str, current_url: str, base_url: str) -> str | None:
    """
    Find the URL of the next page, or return None if on the last page.

    Parameters
    ----------
    html : str
        Raw HTML of the current page.
    current_url : str
        The URL of the current page (used to resolve relative links).
    base_url : str
        Root URL of the site.

    Returns
    -------
    str or None
        Absolute URL of the next page, or None if there isn't one.
    """
    soup = BeautifulSoup(html, "html.parser")
    next_li = soup.select_one("li.next")

    if not next_li:
        return None

    next_a = next_li.select_one("a")
    if not next_a or not next_a.get("href"):
        return None

    # The href is relative — resolve it against the current page URL.
    # e.g. current = "https://books.toscrape.com/catalogue/page-2.html"
    #      href    = "page-3.html"
    #      result  = "https://books.toscrape.com/catalogue/page-3.html"
    href = next_a["href"]

    if href.startswith("http"):
        return href

    # Strip the current page filename and append the new one.
    base_path = current_url.rsplit("/", 1)[0]
    return f"{base_path}/{href}"


# ---------------------------------------------------------------------------
# Private extraction helpers
# ---------------------------------------------------------------------------

def _extract_title(article) -> str:
    """Extract the full book title from the article element."""
    h3 = article.select_one("h3 a")
    if h3:
        # The visible text is truncated; the full title is in the 'title' attr.
        return h3.get("title") or h3.get_text(strip=True)
    return "Unknown Title"


def _extract_price(article) -> float:
    """Extract the price as a float, stripping the £ symbol."""
    price_tag = article.select_one("p.price_color")
    if price_tag:
        raw = price_tag.get_text(strip=True)
        # Remove currency symbol and any whitespace.
        cleaned = raw.replace("£", "").replace("Â", "").strip()
        try:
            return float(cleaned)
        except ValueError:
            return 0.0
    return 0.0


def _extract_rating(article) -> int:
    """Extract the star rating as an integer (1–5)."""
    rating_tag = article.select_one("p.star-rating")
    if rating_tag:
        classes = rating_tag.get("class", [])
        for cls in classes:
            if cls.lower() in RATING_MAP:
                return RATING_MAP[cls.lower()]
    return 0


def _extract_availability(article) -> str:
    """Extract the availability status string."""
    avail_tag = article.select_one("p.availability")
    if avail_tag:
        return avail_tag.get_text(strip=True)
    return "Unknown"


def _extract_url(article, base_url: str) -> str:
    """Build the absolute URL for the book's detail page."""
    link = article.select_one("h3 a")
    if link and link.get("href"):
        href = link["href"]
        # href looks like "../../../soumission_10/index.html"
        # We normalise it to a catalogue URL.
        clean = href.replace("../", "")
        return f"{base_url}/catalogue/{clean}"
    return ""
