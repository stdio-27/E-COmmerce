"""
LumaStyle Customer Lifecycle & Profitability Analytics
Data Ingestion Module

This module handles loading CSV files from the local filesystem into Pandas DataFrames,
validates schemas, and provides utility functions to load tables into PostgreSQL.
"""

import os
import pandas as pd
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

DATA_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data"))

# Schema definition for validation
EXPECTED_SCHEMAS = {
    "customers": {
        "columns": ["customer_id", "first_name", "last_name", "email", "signup_date", "acquisition_channel", "customer_segment", "city", "country"],
        "key": "customer_id"
    },
    "transactions": {
        "columns": ["transaction_id", "customer_id", "transaction_date", "product_category", "size_tier", "quantity", "price_per_unit", "discount_percent", "sales_channel", "total_amount"],
        "key": "transaction_id"
    },
    "product_returns": {
        "columns": ["return_id", "transaction_id", "return_date", "return_reason", "refund_amount"],
        "key": "return_id"
    },
    "marketing_spend": {
        "columns": ["campaign_id", "campaign_name", "date", "channel", "spend", "impressions", "clicks", "conversions"],
        "key": "campaign_id"
    }
}

def check_and_generate_data():
    """Checks if mock data exists, and runs the generator if missing."""
    required_files = [f"{table}.csv" for table in EXPECTED_SCHEMAS.keys()]
    missing = [f for f in required_files if not os.path.exists(os.path.join(DATA_DIR, f))]
    
    if missing:
        logger.warning(f"Missing files: {missing}. Triggering data generation script...")
        from src.generate_mock_data import main as run_generator
        run_generator()
    else:
        logger.info("All raw CSV data source files verified.")

def load_csv_data(table_name):
    """Loads and validates a CSV file into a Pandas DataFrame."""
    if table_name not in EXPECTED_SCHEMAS:
        raise ValueError(f"Unknown table name: {table_name}")
        
    filepath = os.path.join(DATA_DIR, f"{table_name}.csv")
    
    if not os.path.exists(filepath):
        check_and_generate_data()
        
    logger.info(f"Ingesting {table_name} from {filepath}...")
    df = pd.read_csv(filepath)
    
    # Validation
    expected_cols = EXPECTED_SCHEMAS[table_name]["columns"]
    missing_cols = [col for col in expected_cols if col not in df.columns]
    
    if missing_cols:
        logger.error(f"Validation failed for {table_name}. Missing columns: {missing_cols}")
        raise ValueError(f"Schema validation failed for {table_name}")
        
    # Standardize empty/null strings
    df = df.replace({r'^\s*$': None}, regex=True)
    
    # Confirm primary key uniqueness
    pk = EXPECTED_SCHEMAS[table_name]["key"]
    if df[pk].duplicated().any():
        logger.warning(f"Duplicate primary keys found in table '{table_name}' on column '{pk}'.")
        
    logger.info(f"Successfully ingested {table_name} - Rows: {df.shape[0]}, Columns: {df.shape[1]}")
    return df

def ingest_to_postgres(connection_string=None):
    """
    Template function for writing DataFrames to PostgreSQL database.
    Requires psycopg2/sqlalchemy.
    """
    if not connection_string:
        logger.info("PostgreSQL connection string not provided. Skipping database load.")
        return False
        
    try:
        from sqlalchemy import create_engine
        engine = create_engine(connection_string)
        
        for table in EXPECTED_SCHEMAS.keys():
            df = load_csv_data(table)
            # Match schema database names (mostly lowercase matching CSVs)
            logger.info(f"Writing {table} to PostgreSQL...")
            df.to_sql(table, engine, if_exists="replace", index=False)
            logger.info(f"Successfully wrote {table} to database.")
        return True
    except ImportError:
        logger.error("SQLAlchemy or Psycopg2 not installed. Please run: pip install sqlalchemy psycopg2-binary")
        return False
    except Exception as e:
        logger.error(f"Error loading to database: {e}")
        return False

if __name__ == "__main__":
    check_and_generate_data()
    # Test loading
    for table_name in EXPECTED_SCHEMAS.keys():
        load_csv_data(table_name)
