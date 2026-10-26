-- =====================================================================
-- Sales Data Analysis: SQL queries (SQLite)
-- Table: sales   (created from data/cleaned_sales_data.csv)
-- Each query starts with a "-- name:" line. src/sql_analysis.py runs them.
-- You can also paste any query into DB Browser for SQLite.
-- =====================================================================

-- name: 01_overall_kpis
SELECT
    COUNT(*)                                         AS total_records,
    COUNT(DISTINCT order_id)                         AS total_orders,
    ROUND(SUM(sales), 2)                             AS total_sales,
    ROUND(SUM(profit), 2)                            AS total_profit,
    SUM(quantity)                                    AS total_quantity,
    ROUND(SUM(profit) * 100.0 / SUM(sales), 2)       AS profit_margin_pct,
    ROUND(SUM(sales) * 1.0 / COUNT(DISTINCT order_id), 2) AS avg_order_value
FROM sales;

-- name: 02_sales_profit_by_category
SELECT
    category,
    ROUND(SUM(sales), 2)                             AS total_sales,
    ROUND(SUM(profit), 2)                            AS total_profit,
    SUM(quantity)                                    AS total_quantity,
    ROUND(SUM(profit) * 100.0 / SUM(sales), 2)       AS profit_margin_pct,
    ROUND(SUM(sales) * 100.0 / (SELECT SUM(sales) FROM sales), 2) AS sales_share_pct
FROM sales
GROUP BY category
ORDER BY total_sales DESC;

-- name: 03_sales_profit_by_subcategory
SELECT
    category,
    sub_category,
    ROUND(SUM(sales), 2)                             AS total_sales,
    ROUND(SUM(profit), 2)                            AS total_profit,
    ROUND(SUM(profit) * 100.0 / SUM(sales), 2)       AS profit_margin_pct
FROM sales
GROUP BY category, sub_category
ORDER BY total_profit ASC;

-- name: 04_sales_by_region
SELECT
    region,
    ROUND(SUM(sales), 2)                             AS total_sales,
    ROUND(SUM(profit), 2)                            AS total_profit,
    COUNT(DISTINCT order_id)                         AS total_orders,
    ROUND(SUM(profit) * 100.0 / SUM(sales), 2)       AS profit_margin_pct
FROM sales
GROUP BY region
ORDER BY total_sales DESC;

-- name: 05_sales_by_state
SELECT
    state,
    region,
    ROUND(SUM(sales), 2)                             AS total_sales,
    ROUND(SUM(profit), 2)                            AS total_profit,
    ROUND(SUM(profit) * 100.0 / SUM(sales), 2)       AS profit_margin_pct
FROM sales
GROUP BY state, region
ORDER BY total_sales DESC;

-- name: 06_yearly_sales
SELECT
    strftime('%Y', order_date)                       AS order_year,
    ROUND(SUM(sales), 2)                             AS total_sales,
    ROUND(SUM(profit), 2)                            AS total_profit,
    COUNT(DISTINCT order_id)                         AS total_orders
FROM sales
GROUP BY strftime('%Y', order_date)
ORDER BY order_year;

-- name: 07_monthly_revenue_trend
WITH monthly AS (
    SELECT
        strftime('%Y-%m', order_date) AS year_month,
        SUM(sales)                    AS monthly_sales,
        SUM(profit)                   AS monthly_profit
    FROM sales
    GROUP BY strftime('%Y-%m', order_date)
)
SELECT
    year_month,
    ROUND(monthly_sales, 2)  AS total_sales,
    ROUND(monthly_profit, 2) AS total_profit,
    ROUND(
        (monthly_sales - LAG(monthly_sales) OVER (ORDER BY year_month)) * 100.0
        / LAG(monthly_sales) OVER (ORDER BY year_month), 2
    ) AS mom_change_pct
FROM monthly
ORDER BY year_month;

-- name: 08_top_10_products_by_sales
SELECT
    product_name,
    MIN(category)                                    AS category,
    ROUND(SUM(sales), 2)                             AS total_sales,
    ROUND(SUM(profit), 2)                            AS total_profit,
    SUM(quantity)                                    AS total_quantity
FROM sales
GROUP BY product_name
ORDER BY SUM(sales) DESC
LIMIT 10;

-- name: 09_products_with_negative_profit
SELECT
    product_name,
    MIN(category)                                    AS category,
    MIN(sub_category)                                AS sub_category,
    ROUND(SUM(sales), 2)                             AS total_sales,
    ROUND(SUM(profit), 2)                            AS total_profit,
    SUM(quantity)                                    AS total_quantity
FROM sales
GROUP BY product_name
HAVING SUM(profit) < 0
ORDER BY SUM(profit) ASC;

-- name: 10_order_level_top_20
SELECT
    order_id,
    MIN(order_date)                                  AS order_date,
    COUNT(*)                                         AS line_items,
    SUM(quantity)                                    AS total_quantity,
    ROUND(SUM(sales), 2)                             AS order_sales,
    ROUND(SUM(profit), 2)                            AS order_profit,
    ROUND(AVG(discount) * 100, 1)                    AS avg_discount_pct,
    CASE
        WHEN SUM(profit) < 0 THEN 'Loss-making'
        WHEN SUM(profit) = 0 THEN 'Break-even'
        ELSE 'Profitable'
    END                                              AS order_status
FROM sales
GROUP BY order_id
ORDER BY SUM(sales) DESC
LIMIT 20;

-- name: 11_order_profitability_summary
WITH order_totals AS (
    SELECT order_id, SUM(sales) AS order_sales, SUM(profit) AS order_profit
    FROM sales
    GROUP BY order_id
)
SELECT
    CASE
        WHEN order_profit < 0 THEN 'Loss-making'
        WHEN order_profit = 0 THEN 'Break-even'
        ELSE 'Profitable'
    END                                              AS order_status,
    COUNT(*)                                         AS orders,
    ROUND(SUM(order_sales), 2)                       AS total_sales,
    ROUND(SUM(order_profit), 2)                      AS total_profit
FROM order_totals
GROUP BY order_status
ORDER BY orders DESC;

-- name: 12_discount_profitability
SELECT
    CASE
        WHEN discount = 0    THEN 'No Discount'
        WHEN discount <= 0.2 THEN '1-20%'
        WHEN discount <= 0.4 THEN '21-40%'
        ELSE 'Over 40%'
    END                                              AS discount_band,
    COUNT(*)                                         AS records,
    ROUND(AVG(discount) * 100, 2)                    AS avg_discount_pct,
    ROUND(SUM(sales), 2)                             AS total_sales,
    ROUND(SUM(profit), 2)                            AS total_profit,
    ROUND(SUM(profit) * 100.0 / SUM(sales), 2)       AS profit_margin_pct,
    SUM(CASE WHEN profit < 0 THEN 1 ELSE 0 END)      AS loss_making_records
FROM sales
GROUP BY discount_band
ORDER BY MIN(discount);
