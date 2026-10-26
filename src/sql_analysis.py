"""Step 3 of the pipeline: SQL analysis with SQLite.

Reads  : data/cleaned_sales_data.csv, sql/analysis_queries.sql
Writes : data/sales.db                (table: sales)
         reports/sql_results/*.csv    (one file per query)

It also CHECKS the SQL results against Pandas so you can trust both.
"""

import sqlite3
import sys

import pandas as pd

from utils import (
    DB_FILE,
    DB_TABLE,
    SQL_QUERIES_FILE,
    SQL_RESULTS_DIR,
    ensure_folders,
    load_cleaned_data,
)


def build_database(df: pd.DataFrame) -> None:
    """Create sales.db with one table named 'sales' (replaces old data)."""
    data = df.copy()
    for column in ("order_date", "ship_date"):
        data[column] = data[column].dt.strftime("%Y-%m-%d")  # text, SQLite-friendly

    with sqlite3.connect(DB_FILE) as connection:
        data.to_sql(DB_TABLE, connection, if_exists="replace", index=False)
        connection.execute(f"CREATE INDEX IF NOT EXISTS idx_order_date ON {DB_TABLE}(order_date)")
        connection.execute(f"CREATE INDEX IF NOT EXISTS idx_category ON {DB_TABLE}(category)")
        connection.execute(f"CREATE INDEX IF NOT EXISTS idx_region ON {DB_TABLE}(region)")
    print(f"Database created: {DB_FILE}  (table '{DB_TABLE}', {len(data):,} rows)")


def load_queries() -> dict[str, str]:
    """Read sql/analysis_queries.sql and split it into named queries."""
    if not SQL_QUERIES_FILE.exists():
        raise FileNotFoundError(f"SQL file not found: {SQL_QUERIES_FILE}")

    queries: dict[str, str] = {}
    name = None
    lines: list[str] = []
    for line in SQL_QUERIES_FILE.read_text(encoding="utf-8").splitlines():
        if line.startswith("-- name:"):
            if name:
                queries[name] = "\n".join(lines).strip().rstrip(";")
            name = line.split(":", 1)[1].strip()
            lines = []
        elif name is not None:
            lines.append(line)
    if name:
        queries[name] = "\n".join(lines).strip().rstrip(";")
    return queries


def run_queries(queries: dict[str, str]) -> dict[str, pd.DataFrame]:
    """Run every query, print a preview and save the full result as CSV."""
    results = {}
    with sqlite3.connect(DB_FILE) as connection:
        for name, sql in queries.items():
            result = pd.read_sql_query(sql, connection)
            results[name] = result
            result.to_csv(SQL_RESULTS_DIR / f"{name}.csv", index=False)
            print("\n" + "-" * 60)
            print(f"{name}  ({len(result):,} rows)")
            print("-" * 60)
            print(result.head(10).to_string(index=False))
    return results


def verify_against_pandas(df: pd.DataFrame, results: dict[str, pd.DataFrame]) -> bool:
    """Compare key SQL results with Pandas. Returns True if everything matches."""
    kpi = results["01_overall_kpis"].to_dict("records")[0]  # keeps whole numbers whole
    product_profit = df.groupby("product_name")["profit"].sum()
    category_sales = df.groupby("category")["sales"].sum().sort_values(ascending=False)
    sql_category = results["02_sales_profit_by_category"]

    checks = [
        ("Total records", kpi["total_records"], len(df), 0),
        ("Total orders", kpi["total_orders"], df["order_id"].nunique(), 0),
        ("Total sales", kpi["total_sales"], df["sales"].sum(), 0.01),
        ("Total profit", kpi["total_profit"], df["profit"].sum(), 0.01),
        ("Total quantity", kpi["total_quantity"], df["quantity"].sum(), 0),
        ("Products with negative profit",
         len(results["09_products_with_negative_profit"]), int((product_profit < 0).sum()), 0),
        ("Number of categories", len(sql_category), len(category_sales), 0),
        ("Top category by sales (name)", sql_category.iloc[0]["category"], category_sales.index[0], None),
    ]

    print("\n" + "=" * 60)
    print("VERIFICATION: SQL vs Pandas")
    print("=" * 60)
    all_ok = True
    for label, sql_value, pandas_value, tolerance in checks:
        if tolerance is None:
            ok = sql_value == pandas_value
        else:
            ok = abs(float(sql_value) - float(pandas_value)) <= max(tolerance, 1e-9)
        all_ok = all_ok and ok
        status = "PASS" if ok else "FAIL"
        print(f"[{status}] {label}: SQL = {sql_value} | Pandas = {pandas_value}")
    print("=" * 60)
    print("All checks passed." if all_ok else "Some checks FAILED. Please investigate.")
    return all_ok


def main() -> int:
    try:
        df = load_cleaned_data()
        queries = load_queries()
    except FileNotFoundError as error:
        print(f"ERROR: {error}")
        return 1

    ensure_folders()
    try:
        build_database(df)
        results = run_queries(queries)
    except sqlite3.Error as error:
        print(f"\nSQL ERROR: {error}")
        return 1

    return 0 if verify_against_pandas(df, results) else 1


if __name__ == "__main__":
    sys.exit(main())
