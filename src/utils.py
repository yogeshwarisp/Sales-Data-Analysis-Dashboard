"""Shared paths, constants and helper functions used by every script."""

import re
from pathlib import Path

import pandas as pd

# ----------------------------------------------------------------------
# Paths (all relative to the project root, so the project works anywhere)
# ----------------------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"
REPORTS_DIR = PROJECT_ROOT / "reports"
SQL_DIR = PROJECT_ROOT / "sql"
SQL_RESULTS_DIR = REPORTS_DIR / "sql_results"

RAW_FILE = DATA_DIR / "sales_data.csv"
CLEANED_FILE = DATA_DIR / "cleaned_sales_data.csv"
DB_FILE = DATA_DIR / "sales.db"
SQL_QUERIES_FILE = SQL_DIR / "analysis_queries.sql"

# Name of the table inside sales.db (must match sql/analysis_queries.sql)
DB_TABLE = "sales"

# ----------------------------------------------------------------------
# Column names (after standardising: lower case, underscores)
# ----------------------------------------------------------------------
REQUIRED_COLUMNS = [
    "order_id",
    "order_date",
    "ship_date",
    "product_name",
    "category",
    "sub_category",
    "region",
    "state",
    "sales",
    "quantity",
    "discount",
    "profit",
]

# Discount bands used by Python, SQL and Power BI (keep these identical)
DISCOUNT_BAND_LABELS = ["No Discount", "1-20%", "21-40%", "Over 40%"]


def normalise_column_name(name: str) -> str:
    """Turn Sub-Category into sub_category, and Order ID into order_id."""
    name = str(name).strip().lower()
    name = re.sub(r"[^a-z0-9]+", "_", name)
    return name.strip("_")


def read_csv_safely(path: Path) -> pd.DataFrame:
    """Read a CSV as text, trying common encodings (Superstore is not UTF-8)."""
    last_error = None
    for encoding in ("utf-8-sig", "cp1252", "latin-1"):
        try:
            return pd.read_csv(path, encoding=encoding, dtype=str)
        except UnicodeDecodeError as error:
            last_error = error
    raise last_error  # latin-1 can decode any bytes, so this is a safety net


def load_raw_data() -> pd.DataFrame:
    """Load data/sales_data.csv, with a helpful message if it is missing."""
    if not RAW_FILE.exists():
        raise FileNotFoundError(
            f"Raw dataset not found: {RAW_FILE}\n"
            "Download the Superstore CSV, rename it to sales_data.csv "
            "and place it inside the data folder."
        )
    return read_csv_safely(RAW_FILE)


def load_cleaned_data() -> pd.DataFrame:
    """Load data/cleaned_sales_data.csv (created by clean_sales.py)."""
    if not CLEANED_FILE.exists():
        raise FileNotFoundError(
            f"Cleaned dataset not found: {CLEANED_FILE}\n"
            "Run: python src/clean_sales.py   (first)"
        )
    return pd.read_csv(CLEANED_FILE, parse_dates=["order_date", "ship_date"])


def ensure_folders() -> None:
    """Create output folders if they do not exist yet."""
    for folder in (DATA_DIR, REPORTS_DIR, SQL_RESULTS_DIR):
        folder.mkdir(parents=True, exist_ok=True)


def format_money(value: float) -> str:
    """Format as dollars, putting the minus sign first: -$1,234.50"""
    sign = "-" if value < 0 else ""
    return f"{sign}${abs(value):,.2f}"


def format_number(value: float) -> str:
    return f"{value:,.0f}"
