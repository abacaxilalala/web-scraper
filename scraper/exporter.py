"""
exporter.py
-----------
Saves scraped results to JSON and CSV formats.

Both formats are generated from the same list of Book objects, ensuring
they always contain identical data. JSON is useful for programmatic
consumption (APIs, databases). CSV is useful for Excel, pandas, and
sending to non-technical clients.
"""

import csv
import json
import os
from datetime import datetime

from .parser import Book
from .exceptions import ExportError


def export_results(
    books: list[Book],
    output_dir: str,
    filename_stem: str = "books",
) -> dict[str, str]:
    """
    Save a list of Book objects to both JSON and CSV files.

    A timestamp is appended to the filename stem so each run produces
    a new file rather than overwriting previous results.

    Parameters
    ----------
    books : list[Book]
        The scraped books to export.
    output_dir : str
        Directory where output files will be saved. Created if it does
        not exist.
    filename_stem : str, optional
        Base name for the output files (default: "books").
        The exporter adds "_YYYYMMDD_HHMMSS.json/.csv" automatically.

    Returns
    -------
    dict[str, str]
        A dictionary with keys "json" and "csv" mapping to the full
        paths of the files that were written.

    Raises
    ------
    ExportError
        If either file cannot be written (e.g. permission error,
        disk full).
    """
    os.makedirs(output_dir, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    base_name = f"{filename_stem}_{timestamp}"

    json_path = os.path.join(output_dir, f"{base_name}.json")
    csv_path = os.path.join(output_dir, f"{base_name}.csv")

    _write_json(books, json_path)
    _write_csv(books, csv_path)

    return {"json": json_path, "csv": csv_path}


# ---------------------------------------------------------------------------
# Private helpers
# ---------------------------------------------------------------------------

def _write_json(books: list[Book], path: str) -> None:
    """
    Write books to a JSON file as a list of objects.

    The file is formatted with indentation so it's human-readable.
    A metadata block is included at the top level with the scrape
    timestamp and book count — useful for auditing later.
    """
    payload = {
        "metadata": {
            "scraped_at": datetime.now().isoformat(),
            "total_books": len(books),
            "source": "https://books.toscrape.com",
        },
        "books": [book.to_dict() for book in books],
    }

    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2, ensure_ascii=False)
        print(f"  JSON saved → {path}")
    except OSError as e:
        raise ExportError(path, reason=str(e))


def _write_csv(books: list[Book], path: str) -> None:
    """
    Write books to a CSV file with a header row.

    The column order is fixed and human-friendly — title first, then
    price, rating, availability, and URL last (least important visually).
    """
    if not books:
        return

    fieldnames = ["title", "price_gbp", "rating", "availability", "url"]

    try:
        with open(path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for book in books:
                writer.writerow(book.to_dict())
        print(f"  CSV saved  → {path}")
    except OSError as e:
        raise ExportError(path, reason=str(e))
