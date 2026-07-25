"""
LumaStyle Customer Lifecycle & Profitability Analytics
Mock Data Generation Script

This script generates a synthetic dataset simulating a multi-channel retail brand (LumaStyle).
It creates four CSV files in the '../data/' directory:
1. customers.csv: Demographic profile, signup details, and marketing channel attribution.
2. transactions.csv: Purchase history including category, channel (Online vs. In-Store), price, and discounts.
3. product_returns.csv: Linked return transactions containing reasons and refund amounts.
4. marketing_spend.csv: Daily campaign statistics (spend, impressions, clicks, conversions) by channel.
"""

import os
import csv
import random
import uuid
from datetime import datetime, timedelta

# Configuration & Seed
random.seed(42)
START_DATE = datetime(2024, 1, 1)
END_DATE = datetime(2026, 6, 30)
NUM_CUSTOMERS = 1500
OUTPUT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data"))

# Reference Lists
CHANNELS = ["Google Ads", "Meta Ads", "Email", "Organic", "Referral"]
SEGMENTS = [None]  # Segment is determined by RFM/K-Means later
CITIES = [
    ("New York", "United States"),
    ("Los Angeles", "United States"),
    ("Chicago", "United States"),
    ("Houston", "United States"),
    ("Miami", "United States"),
    ("San Francisco", "United States"),
    ("Seattle", "United States"),
    ("Boston", "United States"),
    ("Austin", "United States"),
    ("Denver", "United States"),
]

FIRST_NAMES = [
    "Emma", "Liam", "Olivia", "Noah", "Ava", "Oliver", "Sophia", "Elijah", "Isabella", "James",
    "Mia", "Benjamin", "Charlotte", "Lucas", "Amelia", "Mason", "Harper", "Ethan", "Evelyn", "Alexander",
    "Abigail", "Henry", "Emily", "Jacob", "Elizabeth", "Michael", "Sofia", "Daniel", "Avery", "Logan"
]

LAST_NAMES = [
    "Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis", "Rodriguez", "Martinez",
    "Hernandez", "Lopez", "Gonzalez", "Wilson", "Anderson", "Thomas", "Taylor", "Moore", "Jackson", "Martin",
    "Lee", "Perez", "Thompson", "White", "Harris", "Sanchez", "Clark", "Ramirez", "Lewis", "Robinson"
]

PRODUCT_CATEGORIES = {
    "Apparel": {"min_price": 25.00, "max_price": 120.00, "discount_prob": 0.35, "max_discount": 30.00},
    "Accessories": {"min_price": 10.00, "max_price": 75.00, "discount_prob": 0.20, "max_discount": 15.00},
    "Home & Living": {"min_price": 35.00, "max_price": 300.00, "discount_prob": 0.15, "max_discount": 20.00},
    "Footwear": {"min_price": 50.00, "max_price": 200.00, "discount_prob": 0.40, "max_discount": 40.00}
}

RETURN_REASONS = [
    "Wrong Size", "Defective", "Not as Described", "Changed Mind", "Late Delivery"
]

SIZE_TIERS = ["XS", "S", "M", "L", "XL"]

def generate_customers():
    """Generates customer master records."""
    customers = []
    for i in range(1, NUM_CUSTOMERS + 1):
        cust_id = f"CUST{i:05d}"
        first_name = random.choice(FIRST_NAMES)
        last_name = random.choice(LAST_NAMES)
        email = f"{first_name.lower()}.{last_name.lower()}{random.randint(10, 99)}@example.com"
        
        # Random signup date between START_DATE and mid-2026
        days_range = (END_DATE - START_DATE).days
        signup_days = random.randint(0, int(days_range * 0.9))  # ensure some tenure
        signup_date = START_DATE + timedelta(days=signup_days)
        
        # Weighted acquisition channel
        channel = random.choices(
            CHANNELS, 
            weights=[0.30, 0.25, 0.15, 0.20, 0.10], 
            k=1
        )[0]
        
        city, country = random.choice(CITIES)
        
        customers.append({
            "customer_id": cust_id,
            "first_name": first_name,
            "last_name": last_name,
            "email": email,
            "signup_date": signup_date.strftime("%Y-%m-%d"),
            "acquisition_channel": channel,
            "customer_segment": "",  # placeholder
            "city": city,
            "country": country
        })
    return customers

def generate_transactions_and_returns(customers):
    """Generates customer transactions and corresponding returns."""
    transactions = []
    returns = []
    
    transaction_counter = 1
    return_counter = 1
    
    for customer in customers:
        signup_dt = datetime.strptime(customer["signup_date"], "%Y-%m-%d")
        
        # Determine customer purchase behavior based on channel & random factor
        # E.g., referrals/organic customers might purchase more frequently
        freq_modifier = 1.2 if customer["acquisition_channel"] in ["Referral", "Organic"] else 1.0
        num_purchases = int(random.lognormvariate(1.2, 0.8) * freq_modifier)
        
        # Guarantee at least 1 purchase for 85% of customers
        if num_purchases == 0 and random.random() < 0.85:
            num_purchases = 1
            
        purchase_dates = []
        for _ in range(num_purchases):
            # Purchase date must be after signup date and before END_DATE
            if (END_DATE - signup_dt).days <= 0:
                continue
            purchase_days = random.randint(0, (END_DATE - signup_dt).days)
            purchase_dates.append(signup_dt + timedelta(days=purchase_days))
            
        purchase_dates.sort()
        
        for dt in purchase_dates:
            tx_id = f"TX{transaction_counter:06d}"
            category = random.choice(list(PRODUCT_CATEGORIES.keys()))
            meta = PRODUCT_CATEGORIES[category]
            
            quantity = random.choices([1, 2, 3, 4], weights=[0.70, 0.20, 0.07, 0.03])[0]
            price = round(random.uniform(meta["min_price"], meta["max_price"]), 2)
            
            # Apply discounts
            discount = 0.00
            if random.random() < meta["discount_prob"]:
                discount = round(random.uniform(5.00, meta["max_discount"]), 2)
                
            sales_channel = random.choices(["Online", "In-Store"], weights=[0.60, 0.40])[0]
            size_tier = random.choices(SIZE_TIERS, weights=[0.10, 0.25, 0.35, 0.20, 0.10])[0]
            
            # Math
            subtotal = quantity * price
            discount_amount = subtotal * (discount / 100.0)
            total_amount = round(subtotal - discount_amount, 2)
            
            transactions.append({
                "transaction_id": tx_id,
                "customer_id": customer["customer_id"],
                "transaction_date": dt.strftime("%Y-%m-%d %H:%M:%S"),
                "product_category": category,
                "size_tier": size_tier,
                "quantity": quantity,
                "price_per_unit": price,
                "discount_percent": discount,
                "sales_channel": sales_channel,
                "total_amount": total_amount
            })
            
            # Generate returns (Online has higher return rate: ~10%, In-Store: ~3%)
            return_rate = 0.10 if sales_channel == "Online" else 0.03
            
            # Inject correlation: 'Apparel' category and 'XS' or 'XL' size have much higher return rate
            if category == "Apparel":
                if size_tier in ["XS", "XL"]:
                    return_rate += 0.45
                else:
                    return_rate += 0.10
            elif category == "Footwear":
                return_rate += 0.15
            
            if random.random() < return_rate:
                ret_id = f"RET{return_counter:05d}"
                # Return happens 1 to 14 days after purchase
                ret_days = random.randint(1, 14)
                ret_dt = dt + timedelta(days=ret_days)
                
                if ret_dt <= END_DATE:
                    # Refund could be full or partial if multi-quantity, let's simulate full refund
                    refund = total_amount
                    reason = random.choice(RETURN_REASONS)
                    
                    returns.append({
                        "return_id": ret_id,
                        "transaction_id": tx_id,
                        "return_date": ret_dt.strftime("%Y-%m-%d %H:%M:%S"),
                        "return_reason": reason,
                        "refund_amount": refund
                    })
                    return_counter += 1
            
            transaction_counter += 1
            
    return transactions, returns

def generate_marketing_spend():
    """Generates daily marketing spend records."""
    marketing_records = []
    campaign_counter = 1
    
    current_dt = START_DATE
    while current_dt <= END_DATE:
        # Marketing spend occurs on paid channels: Google Ads, Meta Ads, Email
        # Organic and Referral have impressions/clicks but $0 spend
        for channel in CHANNELS:
            camp_id = f"CAMP{campaign_counter:05d}"
            camp_name = f"LumaStyle_{channel.replace(' ', '')}_{current_dt.strftime('%Y%m')}"
            
            if channel == "Google Ads":
                spend = round(random.uniform(150.00, 500.00), 2)
                impressions = int(spend * random.uniform(40, 60))
                clicks = int(impressions * random.uniform(0.015, 0.035))
                conversions = int(clicks * random.uniform(0.02, 0.05))
            elif channel == "Meta Ads":
                spend = round(random.uniform(100.00, 450.00), 2)
                impressions = int(spend * random.uniform(50, 80))
                clicks = int(impressions * random.uniform(0.008, 0.020))
                conversions = int(clicks * random.uniform(0.03, 0.07))
            elif channel == "Email":
                spend = round(random.uniform(20.00, 80.00), 2)  # platform costs
                impressions = random.randint(2000, 5000)        # emails sent
                clicks = int(impressions * random.uniform(0.10, 0.22))  # open/click rate
                conversions = int(clicks * random.uniform(0.01, 0.03))
            elif channel == "Organic":
                spend = 0.00
                impressions = random.randint(3000, 8000)
                clicks = int(impressions * random.uniform(0.02, 0.04))
                conversions = int(clicks * random.uniform(0.01, 0.03))
            else:  # Referral
                spend = 0.00
                impressions = random.randint(500, 2000)
                clicks = int(impressions * random.uniform(0.05, 0.12))
                conversions = int(clicks * random.uniform(0.04, 0.08))
                
            marketing_records.append({
                "campaign_id": camp_id,
                "campaign_name": camp_name,
                "date": current_dt.strftime("%Y-%m-%d"),
                "channel": channel,
                "spend": spend,
                "impressions": impressions,
                "clicks": clicks,
                "conversions": conversions
            })
            campaign_counter += 1
            
        current_dt += timedelta(days=1)
        
    return marketing_records

def write_to_csv(data, filename, fieldnames):
    """Utility to write dictionaries to CSV."""
    filepath = os.path.join(OUTPUT_DIR, filename)
    with open(filepath, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(data)
    print(f"Generated: {filepath} ({len(data)} rows)")

def main():
    print("Starting mock data generation for LumaStyle Analytics...")
    
    # Create target directory if it doesn't exist
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)
        print(f"Created directory: {OUTPUT_DIR}")
        
    # Generate data
    customers = generate_customers()
    transactions, returns = generate_transactions_and_returns(customers)
    marketing = generate_marketing_spend()
    
    # Write to files
    write_to_csv(
        customers, 
        "customers.csv", 
        ["customer_id", "first_name", "last_name", "email", "signup_date", "acquisition_channel", "customer_segment", "city", "country"]
    )
    
    write_to_csv(
        transactions, 
        "transactions.csv", 
        ["transaction_id", "customer_id", "transaction_date", "product_category", "size_tier", "quantity", "price_per_unit", "discount_percent", "sales_channel", "total_amount"]
    )
    
    write_to_csv(
        returns, 
        "product_returns.csv", 
        ["return_id", "transaction_id", "return_date", "return_reason", "refund_amount"]
    )
    
    write_to_csv(
        marketing, 
        "marketing_spend.csv", 
        ["campaign_id", "campaign_name", "date", "channel", "spend", "impressions", "clicks", "conversions"]
    )
    
    print("Mock data generation successfully completed!")

if __name__ == "__main__":
    main()
