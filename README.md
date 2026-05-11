# Web Scraper — books.toscrape.com

A polite, robust Python scraper that extracts book titles, prices, ratings and availability from [books.toscrape.com](https://books.toscrape.com), paginating through the full catalogue and exporting results to both **JSON** and **CSV**.

---

## Features

- **Paginates automatically** — follows "next page" links until the last page (or a limit you set)
- **Exports to JSON and CSV** — JSON for programmatic use, CSV for Excel / pandas
- **Polite by design** — random delay between requests, realistic browser headers, exponential back-off on retries
- **Robust error handling** — network failures, parse errors and export errors each have their own exception type and clear messages
- **Fully tested offline** — 17 unit tests covering the parser and exporter, no network required

---

## Project structure

```
project-02-web-scraper/
├── main.py                  # Entry point — run this
├── requirements.txt
├── scraper/
│   ├── __init__.py
│   ├── fetcher.py           # HTTP requests, retries, polite delays
│   ├── parser.py            # BeautifulSoup parsing → Book dataclass
│   ├── exporter.py          # Saves results to JSON + CSV
│   └── exceptions.py        # NetworkError, ParseError, ExportError
├── tests/
│   ├── test_scraper.py      # 17 unit tests (offline, using fixtures)
│   └── fixtures/            # Sample HTML pages for testing
└── data/
    └── output/              # JSON and CSV files appear here
```

---

## Quickstart

**1. Clone and install dependencies**

```bash
git clone https://github.com/danieldobos/web-scraper.git
cd web-scraper
pip install -r requirements.txt
```

**2. Run the scraper**

```bash
# Scrape all 50 pages (1,000 books)
python main.py

# Scrape only the first 3 pages (60 books) — great for a quick test
python main.py --pages 3
```

**3. Find your results in `data/output/`**

Each run creates two timestamped files:
- `books_20240101_120000.json`
- `books_20240101_120000.csv`

---

## Sample output

**Console:**
```
============================================================
  WEB SCRAPER — books.toscrape.com
============================================================
  Target      : https://books.toscrape.com
  Max pages   : 3

Scraping page 1: https://books.toscrape.com/catalogue/page-1.html
  Found 20 books (total so far: 20)
Scraping page 2: https://books.toscrape.com/catalogue/page-2.html
  Found 20 books (total so far: 40)
Scraping page 3: https://books.toscrape.com/catalogue/page-3.html
  Found 20 books (total so far: 60)

Scraping complete.
  Pages scraped : 3
  Books found   : 60
  Errors        : 0

Exporting results...
  JSON saved → data/output/books_20240101_120000.json
  CSV saved  → data/output/books_20240101_120000.csv
```

**JSON structure:**
```json
{
  "metadata": {
    "scraped_at": "2024-01-01T12:00:00",
    "total_books": 60,
    "source": "https://books.toscrape.com"
  },
  "books": [
    {
      "title": "A Light in the Attic",
      "price_gbp": 51.77,
      "rating": 3,
      "availability": "In stock",
      "url": "https://books.toscrape.com/catalogue/a-light-in-the-attic_1000/index.html"
    }
  ]
}
```

---

## Run the tests

```bash
# With pytest
pip install pytest
pytest tests/ -v

# Without pytest
python tests/test_scraper.py
```

All 17 tests run offline using saved HTML fixtures — no network required.

---

## Tech stack

- **Python 3.10+**
- **requests** — HTTP with sessions, timeouts, retries
- **BeautifulSoup4** — HTML parsing
- **dataclasses** (stdlib) — `Book` data model
- **json / csv** (stdlib) — dual-format export

---

## Skills demonstrated

- **requests + BeautifulSoup** — the standard Python scraping stack
- **Pagination logic** — automatically follows next-page links
- **Polite scraping** — random delays, session reuse, realistic headers, exponential back-off
- **Dataclasses** — clean data model with free dict/JSON serialisation
- **Unit testing** — 17 tests covering parsing, pagination, and export, fully offline
- **Custom exceptions** — distinct types for network, parse, and export failures
- **CLI arguments** — `--pages N` flag via `argparse`

---

## Author

**Daniel Dobos** — Python developer based in Seville, Spain.  
Available for freelance scraping, data extraction, and automation projects.
