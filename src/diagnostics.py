"""
LumaStyle Customer Lifecycle & Profitability Analytics
Diagnostic script for root-cause analysis of product returns.

This script implements a Decision Tree model to predict product return probabilities
based on product categories, size tiers, discount levels, and acquisition channels.
"""

import os
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.tree import DecisionTreeClassifier, export_text
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.metrics import classification_report

DATA_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data"))

def load_and_merge_data():
    """Loads transactions, returns, and customers and merges them."""
    transactions_df = pd.read_csv(os.path.join(DATA_DIR, "transactions.csv"))
    returns_df = pd.read_csv(os.path.join(DATA_DIR, "product_returns.csv"))
    customers_df = pd.read_csv(os.path.join(DATA_DIR, "customers.csv"))
    
    # Create is_returned target variable
    returned_tx = set(returns_df["transaction_id"])
    transactions_df["is_returned"] = transactions_df["transaction_id"].apply(lambda x: 1 if x in returned_tx else 0)
    
    # Merge with customers to get acquisition_channel
    merged_df = pd.merge(
        transactions_df, 
        customers_df[["customer_id", "acquisition_channel"]], 
        on="customer_id", 
        how="left"
    )
    
    return merged_df

def print_statistical_summary(df):
    """Generates a statistical summary report isolating top product categories and size tiers."""
    print("=" * 80)
    print("STATISTICAL SUMMARY: RETURN RATES BY CATEGORY & SIZE TIER")
    print("=" * 80)
    
    overall_return_rate = df["is_returned"].mean()
    print(f"Overall Return Rate: {overall_return_rate:.2%}\n")
    
    summary = df.groupby(["product_category", "size_tier"]).agg(
        total_transactions=("transaction_id", "count"),
        returned_count=("is_returned", "sum")
    )
    summary["return_rate"] = summary["returned_count"] / summary["total_transactions"]
    
    summary = summary.sort_values(by="return_rate", ascending=False).reset_index()
    
    print(summary.to_string(index=False, formatters={
        'return_rate': '{:.2%}'.format
    }))
    print("\n")

def train_and_evaluate_model(df):
    """Trains a Decision Tree model and prints feature importances and evaluation metrics."""
    print("=" * 80)
    print("DECISION TREE CLASSIFIER: ROOT CAUSE DIAGNOSTICS")
    print("=" * 80)
    
    # Features and Target
    categorical_features = ["product_category", "size_tier", "acquisition_channel"]
    numerical_features = ["discount_percent"]
    
    X = df[categorical_features + numerical_features]
    y = df["is_returned"]
    
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)
    
    # Preprocessing
    preprocessor = ColumnTransformer(
        transformers=[
            ("num", StandardScaler(), numerical_features),
            ("cat", OneHotEncoder(handle_unknown="ignore"), categorical_features)
        ]
    )
    
    # Model pipeline
    # We restrict depth to keep the tree highly interpretable for root-cause analysis
    model = Pipeline([
        ("preprocessor", preprocessor),
        ("classifier", DecisionTreeClassifier(max_depth=4, class_weight="balanced", random_state=42))
    ])
    
    model.fit(X_train, y_train)
    
    # Evaluation
    y_pred = model.predict(X_test)
    print("Classification Report on Test Data:")
    print(classification_report(y_test, y_pred))
    
    # Feature Importances
    dt_classifier = model.named_steps["classifier"]
    encoded_cat_features = model.named_steps["preprocessor"].named_transformers_["cat"].get_feature_names_out(categorical_features)
    all_features = numerical_features + list(encoded_cat_features)
    
    importances = dt_classifier.feature_importances_
    feature_importance_df = pd.DataFrame({
        "Feature": all_features,
        "Importance": importances
    }).sort_values(by="Importance", ascending=False)
    
    print("\nTop Drivers of Returns (Feature Importances):")
    print(feature_importance_df.head(10).to_string(index=False))
    
    # Decision Rules Extraction
    print("\nDecision Tree Rules Extraction:")
    tree_rules = export_text(dt_classifier, feature_names=all_features)
    # Print only top 20 lines to keep output concise
    print("\n".join(tree_rules.split("\n")[:20]))
    print("...")

def main():
    df = load_and_merge_data()
    print_statistical_summary(df)
    train_and_evaluate_model(df)

if __name__ == "__main__":
    main()
