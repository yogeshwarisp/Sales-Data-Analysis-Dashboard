"""Run the whole pipeline in order: clean -> analyse -> SQL.

Usage (from the project root, with the virtual environment active):
    python src/run_all.py
"""

import sys

import clean_sales
import sales_analysis
import sql_analysis

STEPS = [
    ("STEP 1/3: Cleaning data", clean_sales.main),
    ("STEP 2/3: Python analysis and charts", sales_analysis.main),
    ("STEP 3/3: SQL analysis and verification", sql_analysis.main),
]


def main() -> int:
    for title, step in STEPS:
        print("\n" + "#" * 60)
        print(title)
        print("#" * 60)
        if step() != 0:
            print(f"\nStopped: {title} did not finish successfully.")
            return 1
    print("\nPipeline finished. Next: build the Power BI dashboard (docs/POWER_BI_GUIDE.md).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
