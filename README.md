# Retail Sales & Demand Analysis

A beginner-friendly project using SQL, Python, Excel and Power BI to analyze transaction data and create a simple demand baseline.

## Business questions
- Which products and countries contribute the most sales?
- How do monthly sales change over time?
- How well does a simple moving-average baseline estimate the next month?

## Dataset
UCI Online Retail dataset: https://archive.ics.uci.edu/dataset/352/online-retail
The dataset has 541,909 transaction records covering 1 December 2010 to 9 December 2011. It includes invoice number, product code/description, quantity, invoice date, unit price, customer ID and country.

## Project structure
- `run_analysis.py`: downloads the dataset if needed, cleans transactions, performs analysis, creates CSV outputs and charts.
- `sql/analysis.sql`: SQL queries (SQLite syntax).
- `power_bi_guide.md`: dashboard instructions.
- `requirements.txt`: Python dependencies.
- `data/raw/`: downloaded source file.
- `results/`: generated outputs.

## Run on Windows
```bash
py -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python run_analysis.py
```

First run downloads the official UCI ZIP. If download fails, download `Online Retail.xlsx` from the UCI page above and save it to `data/raw/Online Retail.xlsx`.

## Methodology
- Remove rows without product descriptions and rows with non-positive quantity or unit price from the sales-only analysis.
- Exclude cancellation invoices (invoice numbers beginning with C) from positive-sales analysis.
- Calculate line revenue as quantity × unit price.
- Aggregate monthly revenue and forecast each month from the mean of the previous three months (simple baseline).
- Evaluate the baseline with MAE on months for which three prior months are available.

## Limitations
- Excluding returns/cancellations makes the main sales analysis a positive-sales view, not net accounting revenue.
- The dataset ends in December 2011; results are historical and not current market performance.
- No stock-on-hand or lead-time fields are provided. Inventory planning is not measured directly.
- The moving-average forecast is intentionally simple and is a baseline, not an advanced forecasting system.
