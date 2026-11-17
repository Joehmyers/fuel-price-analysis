"""The one place that sets paths and shared settings.

Move the project to another machine by changing only this file (or by setting
the environment variables named below). No other module builds a path by hand.
"""

import os
from pathlib import Path

ROOT = Path(os.environ.get("FUEL_ROOT", Path(__file__).resolve().parent.parent))

# Data folders. Both are ignored by git. Raw files are never edited.
DATA_DIR = Path(os.environ.get("FUEL_DATA_DIR", ROOT / "data"))
RAW_DIR = DATA_DIR / "raw"
CLEAN_DIR = DATA_DIR / "clean"
REPORTS_DIR = ROOT / "reports"

# Small public tables committed with the repo (see datasets/public/README.md), so a
# fresh clone, such as one uploaded to Databricks, can run without any download.
PUBLIC_DIR = Path(os.environ.get("FUEL_PUBLIC_DIR", ROOT / "datasets" / "public"))

# Be polite to public servers: identify ourselves and wait between requests.
USER_AGENT = "fuel-price-analysis/0.1 (research; plain python)"
REQUEST_PAUSE_SECONDS = 2.0
TIMEOUT_SECONDS = 60

# Set in the environment (or a local .env), never in code or git.
# The link in the email from the official Fuel Finder subscription.
FUEL_FINDER_CSV_URL = os.environ.get("FUEL_FINDER_CSV_URL", "")

# All times are kept in UTC. Release times quoted in UK local time are converted.
UK_TZ = "Europe/London"
