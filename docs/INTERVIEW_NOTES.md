# Interview Notes: Explaining This Project

Fill in the numbers from **your** `reports/key_findings.md` after you run the project.
Do not quote any figure you have not calculated yourself.

## 30-second summary
"I built an end-to-end sales analytics project. I cleaned a retail sales dataset with Pandas, explored it with Python and charts,
repeated the key analysis in SQL using SQLite, and built an interactive Power BI dashboard. I verified that Python, SQL and Power BI
produced the same totals. Main findings: **[your top category]**, **[your best region]**, and **[what discounts did to profit]**."

## Likely questions and how to answer

**How did you clean the data?**
Standardised column names, removed exact duplicates (saved to a file for audit), converted dates and numbers, dropped rows missing key
financial fields, filled a missing discount with 0, labelled missing text categories "Unknown", and removed impossible values. I did
**not** remove negative profit, because a loss is a valid business result.

**Why did you validate across tools?**
Different tools can disagree because of data types, filters or aggregation mistakes. Matching totals across Python, SQL and Power BI shows the numbers are right.

**Why DISTINCTCOUNT for orders?**
One order has several line items. Counting rows would overstate the number of orders.

**Why is profit margin a measure and not a column?**
Margin must be total profit divided by total sales for the selected data. Averaging row-level margins is mathematically wrong.

**Which SQL features did you use?**
GROUP BY, HAVING, ORDER BY, aggregates, CASE, a CTE, a window function (LAG for month-over-month change), subqueries, and `strftime` for dates.

**What would you improve?**
Add forecasting, customer-segment analysis, automated tests for the cleaning functions, and a scheduled data refresh in Power BI.

**What did you learn about discounts?**
Quote the discount table from your own results and say that correlation does not prove causation.

## Associate System Engineer angle
Mention: modular Python scripts, error handling for missing files and columns, a virtual environment and `requirements.txt`, SQL and database design,
version control with Git, documentation, and reproducibility (`python src/run_all.py` rebuilds everything).
