"""
Web Scraper — a polite, robust product scraper for books.toscrape.com.
Exports results to both JSON and CSV.
"""

from .parser import Book, parse_books, parse_next_page_url
from .fetcher import fetch_page, make_session, polite_delay
from .exporter import export_results
from .exceptions import ScraperError, NetworkError, ParseError, ExportError

__version__ = "1.0.0"
__author__ = "Daniel Dobos"

__all__ = [
    "Book",
    "parse_books",
    "parse_next_page_url",
    "fetch_page",
    "make_session",
    "polite_delay",
    "export_results",
    "ScraperError",
    "NetworkError",
    "ParseError",
    "ExportError",
]
