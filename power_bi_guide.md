# Power BI dashboard guide

1. Run `python run_analysis.py`.
2. Import these files with **Get Data → Text/CSV**:
   - `results/kpis.csv`
   - `results/monthly_sales.csv`
   - `results/product_performance.csv`
   - `results/country_performance.csv`
   - `results/monthly_sales_with_forecast.csv`
3. Suggested visuals:
   - KPI cards: positive-sales revenue, unique invoices, identified customers, average order value.
   - Line chart: Month vs Revenue.
   - Bar chart: Top 10 products by revenue.
   - Bar chart: Top 10 countries by revenue.
   - Line chart: actual monthly revenue vs `forecast_prev_3m_avg`.
4. Format revenue as GBP currency.
5. Use `Month` as a chronological category (or create a date field from its year-month value).
6. Use the generated CSV outputs as source tables; do not manually type result numbers into visuals.

The forecast is a simple baseline. Clearly label it as the previous-three-month average, not an advanced model.
