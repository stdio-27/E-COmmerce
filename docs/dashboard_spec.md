# Executive Dashboard Wireframe & Specification

## Target Audience
C-Suite Executives, E-commerce Directors, and Marketing Managers.

## Tool 
Power BI / Tableau (or equivalent BI Tool).

---

## Page 1: Unit Economics & Profit Leakage Overview

**Objective:** Provide a high-level view of revenue, profit, and the financial impact of product returns across the business.

### Key Performance Indicators (KPIs) - Top Ribbon
- **Gross Revenue:** Total amount generated before discounts and returns.
- **Net Revenue:** Gross Revenue - (Discounts + Refunds).
- **Return Rate:** Percentage of returned transactions over total transactions (Target: < 10%).
- **Total Refunded Amount:** The actual dollar value leaked due to returns.

### Core Visualizations
1. **Revenue to Net Profit Waterfall Chart**
   - **X-axis:** Gross Revenue -> Discounts -> Refunds -> Net Revenue.
   - **Purpose:** Clearly illustrates how much top-line revenue is lost to discounts and returns.
2. **Refunds Over Time (Line Chart)**
   - **X-axis:** Time (Months/Weeks).
   - **Y-axis:** Refund amount ($).
   - **Purpose:** Tracks the trend of profit leakage and identifies seasonal spikes in returns.
3. **Return Reason Breakdown (Donut Chart)**
   - **Slices:** Wrong Size, Defective, Not as Described, Changed Mind, Late Delivery.
   - **Purpose:** Highlights qualitative reasons behind customer returns.

---

## Page 2: Customer LTV vs. CAC Matrix & Return Hotspots

**Objective:** Highlight actionable segments and identify specific product/size combinations driving profit leakage.

### Key Performance Indicators (KPIs) - Top Ribbon
- **Average CAC (Customer Acquisition Cost):** Total Marketing Spend / New Customers Acquired.
- **Average LTV (Customer Lifetime Value):** Average Net Profit generated per customer over their lifecycle.
- **LTV:CAC Ratio:** Efficiency of marketing spend (Target: > 3.0x).

### Core Visualizations
1. **LTV vs. CAC by Customer Segment (Scatter Plot)**
   - **X-axis:** CAC ($).
   - **Y-axis:** LTV ($).
   - **Color Coding:** K-Means Segments (Champions, Loyal Customers, High-Risk Churners, Value Destroyers).
   - **Purpose:** Helps executives instantly see which customer profiles are highly profitable vs. those that cost more to acquire than they yield.
2. **Profit Leakage Heatmap: Category vs. Size Tier**
   - **Rows:** Product Category (Apparel, Footwear, Accessories, Home & Living).
   - **Columns:** Size Tier (XS, S, M, L, XL).
   - **Values / Color Intensity:** Return Rate %.
   - **Purpose:** Pinpoints the exact product segments driving returns (e.g., Apparel in XS and XL size tiers showing ~50% return rates).

### Filtering Capabilities (Global across all pages)
- **Date Range:** Filter by Transaction/Return Date.
- **Acquisition Channel:** Organic, Meta Ads, Google Ads, Email, Referral.
- **Customer Segment:** Isolate views for Champions vs. Value Destroyers.
- **Sales Channel:** Online vs. In-Store.

---

## Data Model Requirements
To build this dashboard, the BI tool will require the following fact and dimension tables linked via a star schema:
- **Fact Tables:** `transactions`, `product_returns`, `marketing_spend`
- **Dimension Tables:** `customers` (including K-Means Segment labels), `customer_metrics` (LTV, CAC per user)
