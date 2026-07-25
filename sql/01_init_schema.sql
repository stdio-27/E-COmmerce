-- Initial PostgreSQL schema migration for LumaStyle Customer Lifecycle & Profitability Analytics

-- Create customers table
CREATE TABLE IF NOT EXISTS customers (
    customer_id VARCHAR(50) PRIMARY KEY,
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    signup_date DATE NOT NULL,
    acquisition_channel VARCHAR(50) NOT NULL, -- e.g., 'Google Ads', 'Meta Ads', 'Email', 'Organic', 'Referral'
    customer_segment VARCHAR(50),             -- e.g., 'Bronze', 'Silver', 'Gold', 'VIP' (or null initially, updated via RFM/K-Means)
    city VARCHAR(100),
    country VARCHAR(100) DEFAULT 'United States'
);

-- Create transactions table
CREATE TABLE IF NOT EXISTS transactions (
    transaction_id VARCHAR(50) PRIMARY KEY,
    customer_id VARCHAR(50) REFERENCES customers(customer_id) ON DELETE CASCADE,
    transaction_date TIMESTAMP NOT NULL,
    product_category VARCHAR(100) NOT NULL,    -- e.g., 'Apparel', 'Accessories', 'Home & Living', 'Footwear'
    size_tier VARCHAR(50) NOT NULL,           -- e.g., 'XS', 'S', 'M', 'L', 'XL'
    quantity INTEGER NOT NULL CHECK (quantity > 0),
    price_per_unit DECIMAL(10, 2) NOT NULL CHECK (price_per_unit >= 0),
    discount_percent DECIMAL(5, 2) NOT NULL DEFAULT 0.00 CHECK (discount_percent >= 0.00 AND discount_percent <= 100.00),
    sales_channel VARCHAR(50) NOT NULL,       -- e.g., 'Online', 'In-Store'
    total_amount DECIMAL(10, 2) NOT NULL CHECK (total_amount >= 0) -- calculated as quantity * price_per_unit * (1 - discount_percent/100)
);

-- Create marketing_spend table
CREATE TABLE IF NOT EXISTS marketing_spend (
    campaign_id VARCHAR(50) PRIMARY KEY,
    campaign_name VARCHAR(255) NOT NULL,
    date DATE NOT NULL,
    channel VARCHAR(50) NOT NULL,             -- e.g., 'Google Ads', 'Meta Ads', 'Email', 'Organic', 'Referral'
    spend DECIMAL(10, 2) NOT NULL CHECK (spend >= 0),
    impressions INTEGER NOT NULL DEFAULT 0 CHECK (impressions >= 0),
    clicks INTEGER NOT NULL DEFAULT 0 CHECK (clicks >= 0),
    conversions INTEGER NOT NULL DEFAULT 0 CHECK (conversions >= 0)
);

-- Create product_returns table
CREATE TABLE IF NOT EXISTS product_returns (
    return_id VARCHAR(50) PRIMARY KEY,
    transaction_id VARCHAR(50) REFERENCES transactions(transaction_id) ON DELETE CASCADE,
    return_date TIMESTAMP NOT NULL,
    return_reason VARCHAR(255),               -- e.g., 'Defective', 'Wrong Size', 'Not as Described', 'Buyer Remorse'
    refund_amount DECIMAL(10, 2) NOT NULL CHECK (refund_amount >= 0)
);

-- Indexing for performance optimizations
CREATE INDEX IF NOT EXISTS idx_transactions_customer_id ON transactions(customer_id);
CREATE INDEX IF NOT EXISTS idx_transactions_date ON transactions(transaction_date);
CREATE INDEX IF NOT EXISTS idx_returns_transaction_id ON product_returns(transaction_id);
CREATE INDEX IF NOT EXISTS idx_marketing_spend_date ON marketing_spend(date);
CREATE INDEX IF NOT EXISTS idx_marketing_spend_channel ON marketing_spend(channel);
