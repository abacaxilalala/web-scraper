"""
exceptions.py
-------------
Custom exception classes for the Web Scraper package.

Using specific exception types lets the orchestrator in main.py react
differently to a network failure (maybe retry) vs a parsing failure
(maybe skip that page and continue).
"""


class ScraperError(Exception):
    """Base exception for all scraper errors."""

    def __init__(self, message: str):
        self.message = message
        super().__init__(message)


class NetworkError(ScraperError):
    """Raised when an HTTP request fails after all retries."""

    def __init__(self, url: str, status_code: int | None = None, reason: str = ""):
        self.url = url
        self.status_code = status_code
        detail = f"status {status_code}" if status_code else reason
        super().__init__(f"Failed to fetch '{url}' — {detail}")


class ParseError(ScraperError):
    """Raised when the HTML structure is unexpected and cannot be parsed."""

    def __init__(self, url: str, detail: str = ""):
        self.url = url
        super().__init__(
            f"Could not parse page '{url}'"
            + (f" — {detail}" if detail else "")
        )


class ExportError(ScraperError):
    """Raised when saving results to disk fails."""

    def __init__(self, file_path: str, reason: str = ""):
        self.file_path = file_path
        super().__init__(
            f"Failed to export results to '{file_path}'"
            + (f" — {reason}" if reason else "")
        )
