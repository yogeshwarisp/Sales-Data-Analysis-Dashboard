
"""Step 1 of the pipeline: clean the raw sales data.

Reads  : data/sales_data.csv
Writes : data/cleaned_sales_data.csv
         reports/removed_duplicates.csv (only if duplicates were found)
"""

import sys

import numpy as np
import pandas as pd

from utils import (
    CLEANED_FILE,
    DISCOUNT_BAND_LABELS,
    RAW_FILE,
    REPORTS_DIR,
    REQUIRED_COLUMNS,
    ensure_folders,
    load_raw_data,
    normalise_column_name,
)

NUMERIC_COLUMNS = ["sales", "quantity", "discount", "profit"]
DATE_COLUMNS = ["order_date", "ship_date"]

DROP_IF_MISSING = [
    "order_id",
    "order_date",
    "product_name",
    "sales",
    "quantity",
    "profit",
]

FILL_UNKNOWN = ["category", "sub_category", "region", "state"]


# ----------------------------------------------------------------------
# Helper functions
# ----------------------------------------------------------------------
def standardise_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Rename columns to lower_snake_case and standardise dataset names."""
    df = df.copy()
    df.columns = [normalise_column_name(col) for col in df.columns]

    # Support the downloaded Superstore dataset.
    # Its state column may be named state_province.
    if "state" not in df.columns and "state_province" in df.columns:
        df = df.rename(columns={"state_province": "state"})

    # Support common alternate column names.
    aliases = {
        "country_region": "country",
        "sub_category": "sub_category",
    }

    for old_name, new_name in aliases.items():
        if old_name in df.columns and new_name not in df.columns:
            df = df.rename(columns={old_name: new_name})

    return df


def check_required_columns(df: pd.DataFrame) -> None:
    """Stop with a clear message if a required column is missing."""
    missing = [col for col in REQUIRED_COLUMNS if col not in df.columns]

    if missing:
        raise ValueError(
            "The dataset is missing required column(s): "
            f"{missing}\nColumns found in your file: {list(df.columns)}"
        )


def trim_text(df: pd.DataFrame) -> pd.DataFrame:
    """Trim extra spaces in text columns and treat empty strings as missing."""
    df = df.copy()

    for column in df.columns:
        if pd.api.types.is_object_dtype(df[column]) or pd.api.types.is_string_dtype(
            df[column]
        ):
            df[column] = df[column].str.strip().replace("", np.nan)

    return df


def parse_dates(series: pd.Series) -> pd.Series:
    """Convert dates, trying month/day/year first."""
    parsed = pd.to_datetime(
        series, format="%m/%d/%Y", errors="coerce"
    )

    leftover = parsed.isna() & series.notna()

    if leftover.any():
        # Use format='mixed' where supported by the installed pandas.
        try:
            parsed.loc[leftover] = pd.to_datetime(
                series.loc[leftover],
                format="mixed",
                errors="coerce",
            )
        except (TypeError, ValueError):
            parsed.loc[leftover] = pd.to_datetime(
                series.loc[leftover],
                errors="coerce",
            )

    return parsed


def parse_numbers(series: pd.Series) -> pd.Series:
    """Convert text such as '$1,234.50' to numeric values."""
    text = series.astype("string").str.replace(
        r"[$,\s]", "", regex=True
    )

    return pd.to_numeric(text, errors="coerce")


def add_discount_band(df: pd.DataFrame) -> pd.DataFrame:
    """Add discount band and numeric sorting columns."""
    conditions = [
        df["discount"] == 0,
        df["discount"] <= 0.20,
        df["discount"] <= 0.40,
    ]

    df["discount_band"] = np.select(
        conditions,
        DISCOUNT_BAND_LABELS[:3],
        default=DISCOUNT_BAND_LABELS[3],
    )

    order_lookup = {
        label: i + 1
        for i, label in enumerate(DISCOUNT_BAND_LABELS)
    }

    df["discount_band_order"] = df["discount_band"].map(order_lookup)

    return df


def add_date_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Add date helper columns for analysis."""
    df["order_year"] = df["order_date"].dt.year
    df["order_month"] = df["order_date"].dt.month
    df["order_month_name"] = df["order_date"].dt.strftime("%b")
    df["order_year_month"] = df["order_date"].dt.strftime("%Y-%m")

    df["order_quarter"] = (
        "Q" + df["order_date"].dt.quarter.astype(str)
    )

    df["ship_days"] = (
        df["ship_date"] - df["order_date"]
    ).dt.days.astype("Int64")

    return df


# ----------------------------------------------------------------------
# Main cleaning logic
# ----------------------------------------------------------------------
def clean_data(raw: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    """Clean raw data and return the cleaned dataset and summary."""
    summary = {
        "raw_rows": len(raw),
        "raw_columns": raw.shape[1],
    }

    df = standardise_columns(raw)
    check_required_columns(df)
    df = trim_text(df)

    # Record missing values before cleaning.
    missing_counts = df.isna().sum()
    summary["missing_before"] = (
        missing_counts[missing_counts > 0].to_dict()
    )

    # Remove exact duplicate records, ignoring row_id.
    compare_columns = [
        col for col in df.columns if col != "row_id"
    ]

    duplicate_mask = df.duplicated(
        subset=compare_columns,
        keep="first",
    )

    summary["duplicates_removed"] = int(duplicate_mask.sum())

    if duplicate_mask.any():
        ensure_folders()
        df.loc[duplicate_mask].to_csv(
            REPORTS_DIR / "removed_duplicates.csv",
            index=False,
        )

    df = df.loc[~duplicate_mask].copy()

    # Convert dates and numeric fields.
    failed_conversions = {}

    for column in DATE_COLUMNS:
        if column in df.columns:
            original = df[column]
            df[column] = parse_dates(original)

            failed_conversions[column] = int(
                (df[column].isna() & original.notna()).sum()
            )

    for column in NUMERIC_COLUMNS:
        if column in df.columns:
            original = df[column]
            df[column] = parse_numbers(original)

            failed_conversions[column] = int(
                (df[column].isna() & original.notna()).sum()
            )

    summary["failed_conversions"] = {
        key: value
        for key, value in failed_conversions.items()
        if value
    }

    # Drop rows missing critical fields.
    rows_before = len(df)

    df = df.dropna(
        subset=DROP_IF_MISSING
    ).copy()

    summary["dropped_missing_key_fields"] = (
        rows_before - len(df)
    )

    # Missing discount means no recorded discount.
    summary["discount_filled_with_zero"] = int(
        df["discount"].isna().sum()
    )

    df["discount"] = df["discount"].fillna(0.0)

    # Missing category information is retained as Unknown.
    unknown_filled = {}

    for column in FILL_UNKNOWN:
        unknown_filled[column] = int(
            df[column].isna().sum()
        )

        df[column] = df[column].fillna("Unknown")

    summary["filled_unknown"] = {
        key: value
        for key, value in unknown_filled.items()
        if value
    }

    # Remove impossible numeric values. Negative profit is valid.
    invalid_mask = (
        (df["sales"] < 0)
        | (df["quantity"] <= 0)
        | (df["quantity"] % 1 != 0)
        | (df["discount"] < 0)
        | (df["discount"] > 1)
    )

    summary["dropped_invalid_values"] = int(
        invalid_mask.sum()
    )

    df = df.loc[~invalid_mask].copy()

    # Clear ship dates earlier than order dates.
    bad_ship_mask = (
        df["ship_date"].notna()
        & (df["ship_date"] < df["order_date"])
    )

    summary["ship_date_before_order_date_cleared"] = int(
        bad_ship_mask.sum()
    )

    df.loc[bad_ship_mask, "ship_date"] = pd.NaT

    df["quantity"] = df["quantity"].astype(int)

    # Add analysis helper columns.
    df = add_date_columns(df)
    df = add_discount_band(df)

    df = df.sort_values(
        "order_date",
        kind="stable",
    ).reset_index(drop=True)

    summary["final_rows"] = len(df)
    summary["final_columns"] = df.shape[1]

    return df, summary


def print_summary(summary: dict) -> None:
    """Print a summary of the cleaning results."""
    print("\n" + "=" * 60)
    print("CLEANING SUMMARY")
    print("=" * 60)

    print(
        f"Raw data           : {summary['raw_rows']:,} rows "
        f"x {summary['raw_columns']} columns"
    )

    print(
        f"Missing values     : "
        f"{summary['missing_before'] or 'none'}"
    )

    print(
        f"Duplicates removed : "
        f"{summary['duplicates_removed']}"
    )

    print(
        f"Failed conversions : "
        f"{summary['failed_conversions'] or 'none'}"
    )

    print(
        f"Dropped (missing key fields) : "
        f"{summary['dropped_missing_key_fields']}"
    )

    print(
        f"Dropped (invalid values)     : "
        f"{summary['dropped_invalid_values']}"
    )

    print(
        f"Discount filled with 0       : "
        f"{summary['discount_filled_with_zero']}"
    )

    print(
        f"Filled with 'Unknown'        : "
        f"{summary['filled_unknown'] or 'none'}"
    )

    print(
        f"Ship date cleared (before order): "
        f"{summary['ship_date_before_order_date_cleared']}"
    )

    print("-" * 60)

    print(
        f"Cleaned data       : {summary['final_rows']:,} rows "
        f"x {summary['final_columns']} columns"
    )

    print(
        f"Rows removed total : "
        f"{summary['raw_rows'] - summary['final_rows']}"
    )

    print(f"Saved to           : {CLEANED_FILE}")
    print("=" * 60)


def main() -> int:
    """Load, clean, and save the sales dataset."""
    print(f"Loading raw data from: {RAW_FILE}")

    try:
        raw = load_raw_data()
        cleaned, summary = clean_data(raw)

    except FileNotFoundError as error:
        print(f"\nERROR: {error}")
        return 1

    except ValueError as error:
        print(f"\nERROR: {error}")
        return 1

    ensure_folders()

    cleaned.to_csv(
        CLEANED_FILE,
        index=False,
        date_format="%Y-%m-%d",
    )

    print_summary(summary)

    return 0


if __name__ == "__main__":
    sys.exit(main())
