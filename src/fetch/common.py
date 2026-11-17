"""Shared download helpers: polite requests and untouched raw saves."""

import time
from datetime import datetime, timezone
from pathlib import Path

import requests

from src import config


def utc_stamp(now: datetime | None = None) -> str:
    """A file-name-safe UTC time, such as 20261117T093000Z."""
    now = now or datetime.now(timezone.utc)
    return now.strftime("%Y%m%dT%H%M%SZ")


def get(url: str) -> requests.Response:
    """Fetch a URL with our user agent, then pause so we never hammer a server."""
    response = requests.get(
        url, headers={"User-Agent": config.USER_AGENT}, timeout=config.TIMEOUT_SECONDS
    )
    response.raise_for_status()
    time.sleep(config.REQUEST_PAUSE_SECONDS)
    return response


def save_raw(source: str, name: str, content: bytes, fetched_at: datetime | None = None) -> Path:
    """Write bytes untouched to data/raw/<source>/<fetch time>__<name>.

    Never overwrites: an existing file means the same second was used twice.
    """
    fetched_at = fetched_at or datetime.now(timezone.utc)
    folder = config.RAW_DIR / source
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / f"{utc_stamp(fetched_at)}__{name}"
    with open(path, "xb") as handle:
        handle.write(content)
    return path
