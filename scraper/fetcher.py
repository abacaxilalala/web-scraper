"""
fetcher.py
----------
Handles all HTTP communication for the scraper.

Responsibilities:
  - Fetch a URL and return the raw HTML string.
  - Retry on transient failures (5xx errors, timeouts) with exponential
    back-off so we don't hammer the server.
  - Add a polite delay between requests so we behave like a good citizen.
  - Set a realistic User-Agent header — many sites reject the default
    Python requests UA.

Keeping HTTP logic here means the parser never touches requests and
can be tested with raw HTML strings without any network involved.
"""

import time
import random

import requests

from .exceptions import NetworkError


# How long to wait for a response before giving up (seconds).
REQUEST_TIMEOUT = 10

# How many times to retry a failed request before raising NetworkError.
MAX_RETRIES = 3

# Base wait time between retries — doubles each attempt (exponential back-off).
RETRY_BASE_DELAY = 2.0

# Polite delay range between page requests (seconds).
# A random value in this range is chosen to avoid looking like a bot.
POLITE_DELAY_RANGE = (1.0, 2.5)

# Realistic browser User-Agent so we're not rejected immediately.
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-GB,en;q=0.9",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}


def fetch_page(url: str, session: requests.Session) -> str:
    """
    Fetch the HTML content of a URL, retrying on transient failures.

    Parameters
    ----------
    url : str
        The full URL to fetch.
    session : requests.Session
        A shared session object (keeps connections alive across pages,
        which is faster and more polite than opening a new connection
        each time).

    Returns
    -------
    str
        The raw HTML response body as a string.

    Raises
    ------
    NetworkError
        If the request fails after all retries, or the server returns
        a non-200 status code on the final attempt.
    """
    last_error: Exception | None = None

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            response = session.get(url, headers=HEADERS, timeout=REQUEST_TIMEOUT)

            if response.status_code == 200:
                return response.text

            # 4xx = our fault (bad URL etc.) — don't retry.
            if 400 <= response.status_code < 500:
                raise NetworkError(url, status_code=response.status_code)

            # 5xx = server fault — retry with back-off.
            last_error = NetworkError(url, status_code=response.status_code)

        except requests.exceptions.Timeout:
            last_error = NetworkError(url, reason="request timed out")
        except requests.exceptions.ConnectionError:
            last_error = NetworkError(url, reason="connection error")

        if attempt < MAX_RETRIES:
            wait = RETRY_BASE_DELAY * (2 ** (attempt - 1))
            print(f"  [retry {attempt}/{MAX_RETRIES}] Waiting {wait:.0f}s before retry...")
            time.sleep(wait)

    raise last_error


def polite_delay() -> None:
    """
    Sleep for a random duration to avoid overloading the target server.

    Should be called between page requests. The delay is randomised
    within POLITE_DELAY_RANGE to avoid creating a recognisable pattern.
    """
    delay = random.uniform(*POLITE_DELAY_RANGE)
    time.sleep(delay)


def make_session() -> requests.Session:
    """
    Create and return a configured requests Session.

    Using a session (rather than bare requests.get) reuses the
    underlying TCP connection across multiple requests to the same
    host, which is faster and more efficient.

    Returns
    -------
    requests.Session
        A session with default headers pre-set.
    """
    session = requests.Session()
    session.headers.update(HEADERS)
    return session
