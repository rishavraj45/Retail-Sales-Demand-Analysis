from pathlib import Path
from urllib.request import urlretrieve
from zipfile import ZipFile
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parent
RAW = ROOT / "data" / "raw"
OUT = ROOT / "results"
RAW.mkdir(parents=True, exist_ok=True)
OUT.mkdir(parents=True, exist_ok=True)
ZIP_URL = "https://archive.ics.uci.edu/static/public/352/online+retail.zip"
ZIP_FILE = RAW / "online_retail.zip"
XLSX_FILE = RAW / "Online Retail.xlsx"

def load_data():
    if not XLSX_FILE.exists():
        if not ZIP_FILE.exists():
            print("Downloading UCI Online Retail dataset (about 23 MB)...")
            try:
                urlretrieve(ZIP_URL, ZIP_FILE)
            except Exception as exc:
                raise SystemExit(
                    f"Download failed: {exc}\nDownload Online Retail.xlsx from "
                    "https://archive.ics.uci.edu/dataset/352/online-retail\n"
                    f"Save it to: {XLSX_FILE}"
                )
        with ZipFile(ZIP_FILE) as zf:
            candidates = [name for name in zf.namelist() if name.lower().endswith(".xlsx")]
            if not candidates:
                raise SystemExit("The downloaded ZIP did not contain an .xlsx file.")
            with zf.open(candidates[0]) as src, open(XLSX_FILE, "wb") as dst:
                dst.write(src.read())
    return pd.read_excel(XLSX_FILE)

def main():
    raw = load_data()
    original_rows = len(raw)
    df = raw.copy()
    df["InvoiceDate"] = pd.to_datetime(df["InvoiceDate"], errors="coerce")
    df["Quantity"] = pd.to_numeric(df["Quantity"], errors="coerce")
    df["UnitPrice"] = pd.to_numeric(df["UnitPrice"], errors="coerce")
    df["CustomerID"] = df["CustomerID"].astype("string")
    df["Description"] = df["Description"].astype("string").str.strip()

    missing_description = int(df["Description"].isna().sum())
    missing_customer = int(df["CustomerID"].isna().sum())
    cancellation_rows = int(df["InvoiceNo"].astype(str).str.upper().str.startswith("C").sum())
    invalid_rows = int((df["Quantity"].le(0) | df["UnitPrice"].le(0)).sum())

    # For the main positive-sales analysis, remove cancellations and invalid sales rows.
    clean = df[
        df["InvoiceDate"].notna()
        & df["Description"].notna()
        & df["Quantity"].gt(0)
        & df["UnitPrice"].gt(0)
        & ~df["InvoiceNo"].astype(str).str.upper().str.startswith("C")
    ].copy()
    clean["Revenue"] = clean["Quantity"] * clean["UnitPrice"]
    clean["Month"] = clean["InvoiceDate"].dt.to_period("M").astype(str)
    clean.to_csv(OUT / "cleaned_transactions.csv", index=False)

    quality = pd.DataFrame([
        ["original_rows", original_rows],
        ["rows_missing_description_in_raw", missing_description],
        ["rows_missing_customer_id_in_raw", missing_customer],
        ["cancellation_invoice_rows_in_raw", cancellation_rows],
        ["rows_with_nonpositive_quantity_or_price_in_raw", invalid_rows],
        ["rows_retained_for_positive_sales_analysis", len(clean)],
        ["rows_removed_for_positive_sales_analysis", original_rows - len(clean)]
    ], columns=["metric", "value"])
    quality.to_csv(OUT / "data_quality.csv", index=False)

    total_revenue = clean["Revenue"].sum()
    order_count = clean["InvoiceNo"].nunique()
    customer_count = clean["CustomerID"].nunique()
    avg_order_value = total_revenue / order_count if order_count else 0

    kpis = pd.DataFrame([
        ["Positive-sales revenue (GBP)", round(total_revenue, 2)],
        ["Unique invoices", int(order_count)],
        ["Identified customers", int(customer_count)],
        ["Average order value (GBP)", round(avg_order_value, 2)],
        ["Products/SKUs", int(clean["StockCode"].nunique())]
    ], columns=["metric", "value"])
    kpis.to_csv(OUT / "kpis.csv", index=False)

    monthly = clean.groupby("Month").agg(
        revenue=("Revenue", "sum"),
        orders=("InvoiceNo", "nunique"),
        units_sold=("Quantity", "sum"),
        unique_customers=("CustomerID", "nunique")
    ).reset_index()
    monthly["avg_order_value"] = monthly["revenue"] / monthly["orders"]
    monthly.to_csv(OUT / "monthly_sales.csv", index=False)

    product = clean.groupby(["StockCode", "Description"], dropna=False).agg(
        units_sold=("Quantity", "sum"),
        revenue=("Revenue", "sum"),
        orders=("InvoiceNo", "nunique")
    ).reset_index().sort_values("revenue", ascending=False)
    product.to_csv(OUT / "product_performance.csv", index=False)
    product.head(20).to_csv(OUT / "top_20_products.csv", index=False)

    country = clean.groupby("Country").agg(
        revenue=("Revenue", "sum"),
        orders=("InvoiceNo", "nunique"),
        customers=("CustomerID", "nunique"),
        units_sold=("Quantity", "sum")
    ).reset_index().sort_values("revenue", ascending=False)
    country["revenue_share_pct"] = country["revenue"] / total_revenue * 100
    country.to_csv(OUT / "country_performance.csv", index=False)
    country.head(15).to_csv(OUT / "top_15_countries.csv", index=False)

    # Forecast: mean of previous 3 months, evaluated only where 3 prior months exist.
    monthly["forecast_prev_3m_avg"] = monthly["revenue"].rolling(3).mean().shift(1)
    evaluated = monthly.dropna(subset=["forecast_prev_3m_avg"]).copy()
    if len(evaluated):
        evaluated["absolute_error"] = (evaluated["revenue"] - evaluated["forecast_prev_3m_avg"]).abs()
        mae = evaluated["absolute_error"].mean()
        evaluated.to_csv(OUT / "forecast_evaluation.csv", index=False)
    else:
        mae = np.nan
    monthly.to_csv(OUT / "monthly_sales_with_forecast.csv", index=False)

    # Charts
    plt.figure(figsize=(9, 4))
    plt.plot(monthly["Month"], monthly["revenue"], marker="o")
    plt.title("Monthly Positive-Sales Revenue")
    plt.xlabel("Month")
    plt.ylabel("Revenue (GBP)")
    plt.xticks(rotation=45, ha="right")
    plt.tight_layout()
    plt.savefig(OUT / "monthly_revenue.png", dpi=160)
    plt.close()

    top10 = product.head(10).sort_values("revenue")
    plt.figure(figsize=(9, 5))
    plt.barh(top10["Description"].astype(str), top10["revenue"])
    plt.title("Top 10 Products by Positive-Sales Revenue")
    plt.xlabel("Revenue (GBP)")
    plt.tight_layout()
    plt.savefig(OUT / "top_products.png", dpi=160)
    plt.close()

    forecast_rows = monthly.dropna(subset=["forecast_prev_3m_avg"])
    plt.figure(figsize=(9, 4))
    plt.plot(monthly["Month"], monthly["revenue"], marker="o", label="Actual")
    plt.plot(forecast_rows["Month"], forecast_rows["forecast_prev_3m_avg"], marker="x", label="Previous 3-month average")
    plt.title("Monthly Revenue: Actual vs Simple Baseline")
    plt.xlabel("Month")
    plt.ylabel("Revenue (GBP)")
    plt.xticks(rotation=45, ha="right")
    plt.legend()
    plt.tight_layout()
    plt.savefig(OUT / "forecast_vs_actual.png", dpi=160)
    plt.close()

    best_product = product.iloc[0]
    best_country = country.iloc[0]
    best_month = monthly.loc[monthly["revenue"].idxmax()]
    summary = f"""RETAIL SALES & DEMAND ANALYSIS — GENERATED RESULTS

Raw rows loaded: {original_rows:,}
Rows retained for positive-sales analysis: {len(clean):,}
Cancellation invoice rows in raw data: {cancellation_rows:,}
Rows with non-positive quantity or price in raw data: {invalid_rows:,}

Positive-sales revenue: GBP {total_revenue:,.2f}
Unique invoices: {order_count:,}
Identified customers: {customer_count:,}
Average order value: GBP {avg_order_value:,.2f}
Top product by revenue: {best_product['Description']} (GBP {best_product['revenue']:,.2f})
Top country by revenue: {best_country['Country']} (GBP {best_country['revenue']:,.2f})
Highest-revenue month: {best_month['Month']} (GBP {best_month['revenue']:,.2f})
Simple previous-three-month moving-average MAE: GBP {mae:,.2f}

IMPORTANT:
- Positive-sales revenue excludes cancellation invoices and non-positive quantity/price rows; it is not net accounting revenue.
- This historical dataset is not a current sales feed.
- No stock-on-hand or supplier lead-time data is included, so inventory levels cannot be directly evaluated.
- The forecast is a simple baseline, not a guarantee of future sales.
See CSVs and PNG charts for full results.
"""
    (OUT / "summary.txt").write_text(summary, encoding="utf-8")
    print(summary)
    print(f"All outputs saved to: {OUT}")

if __name__ == "__main__":
    main()
