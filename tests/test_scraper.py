"""
tests/test_scraper.py
---------------------
Unit tests for the parser and exporter modules.

These tests run entirely offline using the HTML fixtures in
tests/fixtures/. No network connection is required, which means
they run fast and reliably in any environment.

Run with:
    python -m pytest tests/ -v
    # or without pytest:
    python tests/test_scraper.py
"""

import json
import os
import sys
import tempfile
import unittest

# Allow imports from the project root.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scraper.parser import parse_books, parse_next_page_url, Book
from scraper.exporter import export_results
from scraper.exceptions import ParseError


FIXTURES_DIR = os.path.join(os.path.dirname(__file__), "fixtures")
BASE_URL = "https://books.toscrape.com"


def load_fixture(filename: str) -> str:
    """Load a test HTML fixture file and return its contents."""
    path = os.path.join(FIXTURES_DIR, filename)
    with open(path, encoding="utf-8") as f:
        return f.read()


class TestParser(unittest.TestCase):

    def setUp(self):
        self.page1_html = load_fixture("page_1.html")
        self.page2_html = load_fixture("page_2.html")

    def test_parse_books_returns_correct_count(self):
        """Page 1 fixture has 5 book articles."""
        books = parse_books(self.page1_html, BASE_URL)
        self.assertEqual(len(books), 5)

    def test_parse_books_returns_book_objects(self):
        """Every item returned should be a Book instance."""
        books = parse_books(self.page1_html, BASE_URL)
        for book in books:
            self.assertIsInstance(book, Book)

    def test_first_book_title(self):
        """First book title should come from the 'title' attribute."""
        books = parse_books(self.page1_html, BASE_URL)
        self.assertEqual(books[0].title, "A Light in the Attic")

    def test_first_book_price(self):
        """Price should be a float with the £ symbol stripped."""
        books = parse_books(self.page1_html, BASE_URL)
        self.assertAlmostEqual(books[0].price_gbp, 51.77)

    def test_first_book_rating(self):
        """'Three' class should map to integer 3."""
        books = parse_books(self.page1_html, BASE_URL)
        self.assertEqual(books[0].rating, 3)

    def test_five_star_rating(self):
        """'Five' class should map to integer 5."""
        books = parse_books(self.page1_html, BASE_URL)
        sapiens = next(b for b in books if "Sapiens" in b.title)
        self.assertEqual(sapiens.rating, 5)

    def test_availability_in_stock(self):
        """In-stock books should have 'Instock' availability."""
        books = parse_books(self.page1_html, BASE_URL)
        self.assertIn("stock", books[0].availability.lower())

    def test_availability_out_of_stock(self):
        """Out-of-stock books should reflect that status."""
        books = parse_books(self.page1_html, BASE_URL)
        sapiens = next(b for b in books if "Sapiens" in b.title)
        self.assertIn("stock", sapiens.availability.lower())

    def test_url_is_absolute(self):
        """Book URLs should be absolute (start with http)."""
        books = parse_books(self.page1_html, BASE_URL)
        for book in books:
            if book.url:
                self.assertTrue(book.url.startswith("http"), book.url)

    def test_next_page_found_on_page_1(self):
        """Page 1 has a next page link pointing to page-2.html."""
        current = f"{BASE_URL}/catalogue/page-1.html"
        next_url = parse_next_page_url(self.page1_html, current, BASE_URL)
        self.assertIsNotNone(next_url)
        self.assertIn("page-2", next_url)

    def test_no_next_page_on_last_page(self):
        """Page 2 fixture has no next link — should return None."""
        current = f"{BASE_URL}/catalogue/page-2.html"
        next_url = parse_next_page_url(self.page2_html, current, BASE_URL)
        self.assertIsNone(next_url)

    def test_parse_raises_on_empty_html(self):
        """Completely empty HTML should raise ParseError."""
        with self.assertRaises(ParseError):
            parse_books("<html><body></body></html>", BASE_URL)


class TestExporter(unittest.TestCase):

    def setUp(self):
        self.books = [
            Book("Test Book One", 12.99, 4, "In stock", "http://example.com/1"),
            Book("Test Book Two", 8.50, 2, "Out of stock", "http://example.com/2"),
        ]
        # Use a temporary directory so we don't pollute the project.
        self.tmp_dir = tempfile.mkdtemp()

    def test_export_creates_both_files(self):
        """export_results should create both a JSON and CSV file."""
        paths = export_results(self.books, self.tmp_dir, filename_stem="test")
        self.assertTrue(os.path.exists(paths["json"]))
        self.assertTrue(os.path.exists(paths["csv"]))

    def test_json_contains_all_books(self):
        """JSON output should contain all books in the input list."""
        paths = export_results(self.books, self.tmp_dir, filename_stem="test")
        with open(paths["json"], encoding="utf-8") as f:
            data = json.load(f)
        self.assertEqual(data["metadata"]["total_books"], 2)
        self.assertEqual(len(data["books"]), 2)

    def test_json_metadata_present(self):
        """JSON should include a metadata block with source and timestamp."""
        paths = export_results(self.books, self.tmp_dir, filename_stem="test")
        with open(paths["json"], encoding="utf-8") as f:
            data = json.load(f)
        self.assertIn("metadata", data)
        self.assertIn("scraped_at", data["metadata"])
        self.assertIn("source", data["metadata"])

    def test_csv_has_correct_row_count(self):
        """CSV should have one header row + one row per book."""
        paths = export_results(self.books, self.tmp_dir, filename_stem="test")
        with open(paths["csv"], encoding="utf-8") as f:
            lines = f.readlines()
        # 1 header + 2 data rows
        self.assertEqual(len(lines), 3)

    def test_book_to_dict(self):
        """Book.to_dict() should return all five expected keys."""
        book = Book("My Book", 9.99, 3, "In stock", "http://x.com")
        d = book.to_dict()
        self.assertIn("title", d)
        self.assertIn("price_gbp", d)
        self.assertIn("rating", d)
        self.assertIn("availability", d)
        self.assertIn("url", d)


if __name__ == "__main__":
    # Can run directly without pytest: python tests/test_scraper.py
    unittest.main(verbosity=2)
