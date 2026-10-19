-- Import results/cleaned_transactions.csv into SQLite as table `transactions`.
-- Use DB Browser for SQLite or another SQLite client.

-- 1. Overall sales KPIs
SELECT
    ROUND(SUM(Revenue), 2) AS positive_sales_revenue_gbp,
    COUNT(DISTINCT InvoiceNo) AS unique_invoices,
    COUNT(DISTINCT CustomerID) AS identified_customers,
    ROUND(SUM(Revenue) / COUNT(DISTINCT InvoiceNo), 2) AS average_order_value_gbp
FROM transactions;

-- 2. Monthly sales trend
SELECT
    Month,
    ROUND(SUM(Revenue), 2) AS revenue_gbp,
    COUNT(DISTINCT InvoiceNo) AS orders,
    ROUND(SUM(Revenue) / COUNT(DISTINCT InvoiceNo), 2) AS average_order_value_gbp
FROM transactions
GROUP BY Month
ORDER BY Month;

-- 3. Top 10 products by revenue
SELECT
    StockCode,
    Description,
    ROUND(SUM(Revenue), 2) AS revenue_gbp,
    SUM(Quantity) AS units_sold
FROM transactions
GROUP BY StockCode, Description
ORDER BY revenue_gbp DESC
LIMIT 10;

-- 4. Country performance
SELECT
    Country,
    ROUND(SUM(Revenue), 2) AS revenue_gbp,
    COUNT(DISTINCT InvoiceNo) AS orders
FROM transactions
GROUP BY Country
ORDER BY revenue_gbp DESC;

-- 5. Monthly revenue growth (SQLite window function)
WITH monthly AS (
    SELECT Month, SUM(Revenue) AS revenue
    FROM transactions
    GROUP BY Month
)
SELECT
    Month,
    ROUND(revenue, 2) AS revenue_gbp,
    ROUND(100.0 * (revenue - LAG(revenue) OVER (ORDER BY Month))
          / NULLIF(LAG(revenue) OVER (ORDER BY Month), 0), 2) AS month_over_month_growth_pct
FROM monthly
ORDER BY Month;
