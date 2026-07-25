"""
LumaStyle Customer Lifecycle & Profitability Analytics
Data Transformation & Feature Engineering Module

This module reads raw ingested DataFrames, cleans dates, processes refunds,
and transforms raw transactions/marketing data into analytical tables:
1. Customer Metrics: Recency, Frequency, Monetary value (RFM), refund rates, and net profitability.
2. Channel Metrics: Total CAC (Customer Acquisition Cost), CPA (Cost Per Acquisition), and ROI by acquisition channel.
"""

import os
import pandas as pd
import numpy as np
import logging
from src.ingestion import load_csv_data

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

OUTPUT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data"))

def transform_customer_metrics():
    """Computes customer-level features, returns, and RFM metrics."""
    logger.info("Starting Customer-level calculations and RFM transformations...")
    
    # Load raw tables
    df_cust = load_csv_data("customers")
    df_tx = load_csv_data("transactions")
    df_ret = load_csv_data("product_returns")
    
    # Convert dates to datetime
    df_tx["transaction_date"] = pd.to_datetime(df_tx["transaction_date"])
    df_cust["signup_date"] = pd.to_datetime(df_cust["signup_date"])
    
    # Handle Returns: Merge returns with transactions to resolve transaction links
    df_tx_with_returns = pd.merge(
        df_tx, 
        df_ret[["transaction_id", "return_date", "refund_amount"]], 
        on="transaction_id", 
        how="left"
    )
    # Fill missing return info
    df_tx_with_returns["refund_amount"] = df_tx_with_returns["refund_amount"].fillna(0.0)
    df_tx_with_returns["is_returned"] = df_tx_with_returns["refund_amount"] > 0
    df_tx_with_returns["net_amount"] = df_tx_with_returns["total_amount"] - df_tx_with_returns["refund_amount"]
    
    # Define Analysis Date (1 day after latest transaction for Recency calculations)
    max_tx_date = df_tx["transaction_date"].max()
    analysis_date = max_tx_date + pd.Timedelta(days=1)
    logger.info(f"Using reference analysis date for Recency: {analysis_date.date()}")
    
    # Customer transactional aggregation
    cust_tx_agg = df_tx_with_returns.groupby("customer_id").agg(
        first_purchase_date=("transaction_date", "min"),
        last_purchase_date=("transaction_date", "max"),
        frequency=("transaction_id", "count"),
        gross_monetary=("total_amount", "sum"),
        total_refunded=("refund_amount", "sum"),
        net_monetary=("net_amount", "sum"),
        total_quantity=("quantity", "sum"),
        returns_count=("is_returned", "sum")
    ).reset_index()
    
    # Compute RFM features
    cust_tx_agg["recency"] = (analysis_date - cust_tx_agg["last_purchase_date"]).dt.days
    cust_tx_agg["return_rate"] = (cust_tx_agg["returns_count"] / cust_tx_agg["frequency"]).fillna(0.0)
    
    # Merge aggregations back to customer profiles
    customer_profile = pd.merge(df_cust, cust_tx_agg, on="customer_id", how="left")
    
    # Fill metrics for customers with zero transactions
    customer_profile["frequency"] = customer_profile["frequency"].fillna(0).astype(int)
    customer_profile["gross_monetary"] = customer_profile["gross_monetary"].fillna(0.0)
    customer_profile["total_refunded"] = customer_profile["total_refunded"].fillna(0.0)
    customer_profile["net_monetary"] = customer_profile["net_monetary"].fillna(0.0)
    customer_profile["total_quantity"] = customer_profile["total_quantity"].fillna(0).astype(int)
    customer_profile["returns_count"] = customer_profile["returns_count"].fillna(0).astype(int)
    customer_profile["return_rate"] = customer_profile["return_rate"].fillna(0.0)
    
    # Calculate customer lifetime span (tenure in days since signup to analysis_date)
    customer_profile["tenure_days"] = (analysis_date - customer_profile["signup_date"]).dt.days
    
    # Write transformed table
    output_path = os.path.join(OUTPUT_DIR, "customer_metrics.csv")
    customer_profile.to_csv(output_path, index=False)
    logger.info(f"Created: {output_path} ({customer_profile.shape[0]} rows)")
    
    return customer_profile

def transform_marketing_channels():
    """Computes Customer Acquisition Cost (CAC) and marketing ROI metrics."""
    logger.info("Starting Marketing spend analysis and acquisition metrics...")
    
    df_cust = load_csv_data("customers")
    df_mkt = load_csv_data("marketing_spend")
    
    # Convert date format
    df_mkt["date"] = pd.to_datetime(df_mkt["date"])
    
    # Aggregate marketing spend by channel
    mkt_agg = df_mkt.groupby("channel").agg(
        total_spend=("spend", "sum"),
        total_impressions=("impressions", "sum"),
        total_clicks=("clicks", "sum"),
        total_conversions=("conversions", "sum")
    ).reset_index()
    
    # Aggregate custom signup acquisitions by channel
    signup_agg = df_cust.groupby("acquisition_channel").size().reset_index(name="total_signups")
    signup_agg.rename(columns={"acquisition_channel": "channel"}, inplace=True)
    
    # Combine marketing metrics
    channel_performance = pd.merge(mkt_agg, signup_agg, on="channel", how="outer").fillna(0)
    
    # KPI Calculations
    # CAC = Spend / Signups (using customers table attribution)
    channel_performance["cac"] = np.where(
        channel_performance["total_signups"] > 0,
        channel_performance["total_spend"] / channel_performance["total_signups"],
        0.0
    ).round(2)
    
    # Cost per Conversion (CPA) = Spend / Conversions (reported by marketing campaigns)
    channel_performance["cpa"] = np.where(
        channel_performance["total_conversions"] > 0,
        channel_performance["total_spend"] / channel_performance["total_conversions"],
        0.0
    ).round(2)
    
    # Click-Through Rate (CTR) = Clicks / Impressions
    channel_performance["ctr_percent"] = np.where(
        channel_performance["total_impressions"] > 0,
        (channel_performance["total_clicks"] / channel_performance["total_impressions"]) * 100.0,
        0.0
    ).round(4)
    
    # Conversion Rate (CR) = Conversions / Clicks
    channel_performance["conversion_rate_percent"] = np.where(
        channel_performance["total_clicks"] > 0,
        (channel_performance["total_conversions"] / channel_performance["total_clicks"]) * 100.0,
        0.0
    ).round(4)
    
    output_path = os.path.join(OUTPUT_DIR, "channel_performance.csv")
    channel_performance.to_csv(output_path, index=False)
    logger.info(f"Created: {output_path} ({channel_performance.shape[0]} rows)")
    
    return channel_performance

def main():
    print("Starting LumaStyle Data Transformations...")
    transform_customer_metrics()
    transform_marketing_channels()
    print("Data transformations completed successfully!")

if __name__ == "__main__":
    main()
