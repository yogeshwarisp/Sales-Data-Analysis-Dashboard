# Sales Data Analysis Dashboard (Python, SQL & Power BI)

An end-to-end sales analytics project: raw retail data → cleaning (Pandas) → exploratory analysis (Matplotlib/Seaborn) → SQL analysis (SQLite) → interactive Power BI dashboard.

> **Before publishing:** the sections marked **[FILL IN]** need your real numbers. Run the project, then copy values from
> `reports/key_findings.md`. Do not publish figures you have not calculated.

## Project Overview
This project analyses retail sales records to find revenue trends, seasonal patterns, product and regional performance, profit margins and
growth opportunities. The same cleaned dataset is analysed in Python and SQL, and visualised in Power BI. The totals are cross-checked between the three tools.

## Business Problem
A retail business wants to know where revenue and profit come from, which products and regions underperform, and how discounting affects profitability, so it can decide where to focus.

## Objectives
- Clean and validate the sales data.
- Calculate sales, profit, order and quantity KPIs.
- Identify trends, seasonality, top products and loss-making products.
- Study the relationship between discount and profit.
- Build an interactive dashboard with Year, Region and Category slicers.
- Verify that Python, SQL and Power BI agree.

## Technologies Used
Python · Pandas · NumPy · Matplotlib · Seaborn · SQLite · SQL · Power BI Desktop (DAX) · Git/GitHub · VS Code

## Dataset
- **Source:** Sample Superstore ("Superstore Dataset Final", Kaggle). **[FILL IN: confirm the source link and licence you used.]**
- **Records:** **[FILL IN: the exact row count printed by `python src/check_setup.py`]**. The dataset is not padded or extended in any way.
- Place the CSV at `data/sales_data.csv`.

## Project Architecture
```
data/sales_data.csv
   │  src/clean_sales.py
   ▼
data/cleaned_sales_data.csv ──► src/sales_analysis.py ──► reports/*.csv, *.png, key_findings.md
   │                                                          
   ├──► src/sql_analysis.py ──► data/sales.db ──► reports/sql_results/*.csv (+ verification vs Pandas)
   │
   └──► Power BI Desktop ──► reports/Sales_Analysis_Dashboard.pbix
```

## Folder Structure
```
Sales-Data-Analysis-Dashboard/
├── data/            raw, cleaned data and SQLite database
├── reports/         charts, summary tables, SQL results, Power BI file
├── images/          dashboard screenshots used in this README
├── sql/             analysis_queries.sql (all SQL queries)
├── powerbi/         corporate_theme.json (Power BI theme)
├── docs/            Power BI, GitHub and interview guides
├── src/
│   ├── utils.py            shared paths and helpers
│   ├── clean_sales.py      data cleaning
│   ├── sales_analysis.py   EDA, charts, findings
│   ├── sql_analysis.py     builds SQLite DB, runs SQL, verifies against Pandas
│   ├── run_all.py          runs the whole pipeline
│   └── check_setup.py      confirms the raw file is readable
├── requirements.txt
└── .gitignore
```

## Data Cleaning Methodology
- Column names standardised (`Sub-Category` → `sub_category`).
- Exact duplicate records removed (identical in every field except Row ID); removed rows are saved to `reports/removed_duplicates.csv`.
- Dates parsed (month/day/year first), numbers converted (currency symbols and commas removed).
- Rows missing `order_id`, `order_date`, `product_name`, `sales`, `quantity` or `profit` are dropped; a missing `discount` becomes 0; missing text categories become "Unknown".
- Impossible values removed (negative sales, quantity ≤ 0, discount outside 0–1). **Negative profit is kept**: it represents real losses.
- Added columns: year, month, month name, year-month, quarter, ship days, discount band.
- The full cleaning report is printed when you run `clean_sales.py`.

## SQL Analysis
12 queries in [`sql/analysis_queries.sql`](sql/analysis_queries.sql): KPIs, category/sub-category, region/state, yearly and monthly trends (with month-over-month change using `LAG`),
top products, negative-profit products, order-level analysis, and discount profitability. Uses `GROUP BY`, `HAVING`, `CASE`, CTEs, window functions and `strftime`.
`sql_analysis.py` also compares SQL results with Pandas and prints PASS/FAIL.

## Dashboard Features
- 5 KPI cards: Total Sales, Total Profit, Total Orders, Total Quantity, Profit Margin %
- Monthly sales trend, sales by region, sales by category (donut), top 10 products, profit by category, sales vs profit comparison
- Slicers: Year, Region, Category
- Consistent corporate theme (`powerbi/corporate_theme.json`)
- Build instructions and every DAX measure: [`docs/POWER_BI_GUIDE.md`](docs/POWER_BI_GUIDE.md)

## Key Findings
**[FILL IN: paste the lines from `reports/key_findings.md`, generated from your actual data.]**

Topics it covers: highest-sales category, best region, strongest months, loss-making products, and discount vs profit.

## Dashboard Screenshots
![Dashboard overview](images/dashboard_overview.png)
**[FILL IN: add your screenshot as `images/dashboard_overview.png` after building the dashboard.]**

## Installation and Execution (Windows, VS Code)
```powershell
# 1. Clone or open the project folder, then create a virtual environment
python -m venv venv
venv\Scripts\Activate.ps1

# 2. Install libraries
pip install -r requirements.txt

# 3. Put the dataset at data\sales_data.csv, then check it
python src/check_setup.py

# 4. Run the full pipeline (clean -> analyse -> SQL + verification)
python src/run_all.py
```
Or run each step: `python src/clean_sales.py`, `python src/sales_analysis.py`, `python src/sql_analysis.py`.

Then open Power BI Desktop and follow `docs/POWER_BI_GUIDE.md`.

## Future Improvements
- Sales forecasting (time-series models)
- Customer segmentation and repeat-purchase analysis
- Automated tests for the cleaning functions
- Scheduled refresh and a published Power BI report

![alt text](<Screenshot 2026-10-26 231648.png>)


## Author
Yogeshwari Sandip Pawar · [GitHub](https://github.com/yogeshwarisp)


