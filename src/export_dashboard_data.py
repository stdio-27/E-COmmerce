"""
LumaStyle Customer Lifecycle & Profitability Analytics
Dashboard Data Exporter

This script aggregates the cleaned data models (transactions, customer metrics, 
channel performance, and returns) into a unified, denormalized reporting dataset 
optimized for direct import into Power BI, Tableau, or other BI tools.
"""

import os
import pandas as pd
import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

DATA_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data"))
OUTPUT_FILE = os.path.join(DATA_DIR, "bi_dashboard_export.csv")

def create_dashboard_export():
    logger.info("Starting dashboard data aggregation...")
    
    # 1. Load Data
    try:
        transactions = pd.read_csv(os.path.join(DATA_DIR, "transactions.csv"))
        returns = pd.read_csv(os.path.join(DATA_DIR, "product_returns.csv"))
        customers = pd.read_csv(os.path.join(DATA_DIR, "customers.csv"))
        customer_metrics = pd.read_csv(os.path.join(DATA_DIR, "customer_metrics.csv"))
        channel_metrics = pd.read_csv(os.path.join(DATA_DIR, "channel_performance.csv"))
    except FileNotFoundError as e:
        logger.error(f"Missing required data file: {e}")
        return

    # 2. Merge Transactions with Returns (Left Join)
    # This gives us transaction-level return diagnostics
    logger.info("Merging transactions with returns...")
    df_export = pd.merge(
        transactions,
        returns[["transaction_id", "return_date", "return_reason", "refund_amount"]],
        on="transaction_id",
        how="left"
    )
    
    # Create derived columns for BI ease of use
    df_export["is_returned"] = df_export["refund_amount"].notna().astype(int)
    df_export["refund_amount"] = df_export["refund_amount"].fillna(0.0)
    df_export["net_revenue"] = df_export["total_amount"] - df_export["refund_amount"]

    # 3. Merge with Customer Data & Metrics
    logger.info("Merging customer demographics and RFM/LTV metrics...")
    # Select relevant columns from customers and metrics to avoid bloat/duplication
    cust_info = customers[["customer_id", "acquisition_channel", "city", "country"]]
    cust_metrics_info = customer_metrics[["customer_id", "recency", "frequency", "net_monetary", "customer_segment"]]
    
    cust_combined = pd.merge(cust_info, cust_metrics_info, on="customer_id", how="left")
    
    df_export = pd.merge(
        df_export,
        cust_combined,
        on="customer_id",
        how="left"
    )

    # 4. Merge with Channel Performance (CAC)
    logger.info("Merging channel performance metrics (CAC)...")
    # We want to attach the average CAC for the customer's acquisition channel
    # so we can compute LTV:CAC per customer in the dashboard
    channel_cac = channel_metrics[["channel", "cac", "cpa"]]
    
    df_export = pd.merge(
        df_export,
        channel_cac,
        left_on="acquisition_channel",
        right_on="channel",
        how="left"
    )
    df_export.drop(columns=["channel"], inplace=True) # drop duplicate column

    # 5. Export to CSV
    logger.info(f"Exporting unified dataset to {OUTPUT_FILE}...")
    df_export.to_csv(OUTPUT_FILE, index=False)
    
    logger.info(f"Dashboard export completed successfully! Shape: {df_export.shape}")
    logger.info("Data includes transaction details, return flags, customer segments, and CAC.")

if __name__ == "__main__":
    create_dashboard_export()
