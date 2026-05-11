"""
main.py
-------
Entry point for the Web Scraper pipeline.

Usage:
    python main.py              # Scrape all pages (up to MAX_PAGES)
    python main.py --pages 3    # Scrape only the first 3 pages

Each page on books.toscrape.com contains 20 books.
The full site has 50 pages (1,000 books total).
"""

import argparse
import logging
import sys

import requests

from scraper.fetcher import fetch_page, make_session, polite_delay
from scraper.parser import parse_books, parse_next_page_url
from scraper.exporter import export_results
from scraper.exceptions import ScraperError, NetworkError, ParseError

import os


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

BASE_URL = "https://books.toscrape.com"
START_URL = f"{BASE_URL}/catalogue/page-1.html"
OUTPUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "output")

# Safety cap — avoids accidentally scraping forever.
MAX_PAGES = 50


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Scrape book data from books.toscrape.com"
    )
    parser.add_argument(
        "--pages",
        type=int,
        default=MAX_PAGES,
        metavar="N",
        help=f"Number of pages to scrape (default: all {MAX_PAGES})",
    )
    return parser.parse_args()


def run(max_pages: int) -> None:
    """
    Execute the full scraping pipeline.

    Paginates through the site, parsing books from each page, then
    exports all results to JSON and CSV in the output directory.

    Parameters
    ----------
    max_pages : int
        Maximum number of pages to scrape.
    """
    logging.basicConfig(
        level=logging.WARNING,
        format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
        datefmt="%H:%M:%S",
    )
    print("=" * 60)
    print("  WEB SCRAPER — books.toscrape.com")
    print("=" * 60)
    print(f"  Target      : {BASE_URL}")
    print(f"  Max pages   : {max_pages}")
    print(f"  Output dir  : {OUTPUT_DIR}")
    print()

    session = make_session()
    all_books = []
    current_url = START_URL
    page_num = 0
    errors = 0

    while current_url and page_num < max_pages:
        page_num += 1
        print(f"Scraping page {page_num}: {current_url}")

        # --- Fetch ---
        try:
            html = fetch_page(current_url, session)
        except NetworkError as e:
            print(f"  ERROR (network): {e.message} — skipping page")
            errors += 1
            break

        # --- Parse books ---
        try:
            books = parse_books(html, BASE_URL, page_url=current_url)
            all_books.extend(books)
            print(f"  Found {len(books)} books (total so far: {len(all_books)})")
        except ParseError as e:
            print(f"  ERROR (parse): {e.message} — skipping page")
            errors += 1
            # Don't break — try the next page.

        # --- Find next page ---
        next_url = parse_next_page_url(html, current_url, BASE_URL)

        if next_url and page_num < max_pages:
            polite_delay()  # Be a good citizen.
            current_url = next_url
        else:
            current_url = None

    # --- Export ---
    print(f"\nScraping complete.")
    print(f"  Pages scraped : {page_num}")
    print(f"  Books found   : {len(all_books)}")
    print(f"  Errors        : {errors}")

    if not all_books:
        print("\n  No books to export. Exiting.")
        sys.exit(1)

    print("\nExporting results...")
    try:
        paths = export_results(all_books, OUTPUT_DIR)
    except ScraperError as e:
        print(f"\n  ERROR (export): {e.message}")
        sys.exit(1)

    print("\n" + "=" * 60)
    print("  PIPELINE COMPLETE")
    print("=" * 60)
    print(f"  Books scraped : {len(all_books)}")
    print(f"  JSON output   : {paths['json']}")
    print(f"  CSV output    : {paths['csv']}")
    print("=" * 60)


if __name__ == "__main__":
    args = parse_args()
    run(max_pages=args.pages)
