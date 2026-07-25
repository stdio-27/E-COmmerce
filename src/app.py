import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import os

# Set page config
st.set_page_config(
    page_title="Executive Dashboard", 
    page_icon="📈", 
    layout="wide", 
    initial_sidebar_state="expanded"
)

# Custom CSS for aesthetics
st.markdown("""
<style>
    .reportview-container {
        background: #fafafa;
    }
    .sidebar .sidebar-content {
        background: #f0f2f6;
    }
    h1, h2, h3 {
        color: #1E3A8A;
    }
    .stMetric {
        background-color: #ffffff;
        padding: 15px;
        border-radius: 10px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05);
    }
</style>
""", unsafe_allow_html=True)

@st.cache_data
def load_data():
    base_path = os.path.join(os.path.dirname(__file__), "..", "data")
    
    try:
        customers = pd.read_csv(os.path.join(base_path, "customers.csv"))
        transactions = pd.read_csv(os.path.join(base_path, "transactions.csv"))
        product_returns = pd.read_csv(os.path.join(base_path, "product_returns.csv"))
        customer_metrics = pd.read_csv(os.path.join(base_path, "customer_metrics.csv"))
        channel_performance = pd.read_csv(os.path.join(base_path, "channel_performance.csv"))
    except FileNotFoundError as e:
        st.error(f"Data file not found: {e}")
        st.stop()
        
    # Convert dates
    transactions['transaction_date'] = pd.to_datetime(transactions['transaction_date'])
    product_returns['return_date'] = pd.to_datetime(product_returns['return_date'])
    
    # Generate Customer Segments if missing (e.g. all NaN or empty)
    if customer_metrics['customer_segment'].isnull().all() or (customer_metrics['customer_segment'] == "").all():
        q33 = customer_metrics['net_monetary'].quantile(0.33)
        q66 = customer_metrics['net_monetary'].quantile(0.66)
        def assign_segment(val):
            if val <= q33: return "Low Value"
            elif val <= q66: return "Medium Value"
            else: return "High Value"
        customer_metrics['customer_segment'] = customer_metrics['net_monetary'].apply(assign_segment)
    
    # Join returns with transactions
    tx_returns = pd.merge(transactions, product_returns, on='transaction_id', how='left')
    tx_returns['is_returned'] = tx_returns['return_id'].notna()
    
    # Join transactions with customer metrics to get segment and channel for filtering
    tx_full = pd.merge(tx_returns, customer_metrics[['customer_id', 'acquisition_channel', 'customer_segment']], on='customer_id', how='left')
    
    return customers, transactions, product_returns, customer_metrics, channel_performance, tx_full

customers, transactions, product_returns, customer_metrics, channel_performance, tx_full = load_data()

# --- SIDEBAR FILTERS ---
st.sidebar.image("https://cdn-icons-png.flaticon.com/512/3135/3135695.png", width=50)
st.sidebar.title("Global Filters")

# Date Filter
min_date = tx_full['transaction_date'].min().date()
max_date = tx_full['transaction_date'].max().date()

start_date = st.sidebar.date_input("Start Date", min_date, min_value=min_date, max_value=max_date)
end_date = st.sidebar.date_input("End Date", max_date, min_value=min_date, max_value=max_date)

# Channel Filter
channels = sorted(tx_full['acquisition_channel'].dropna().unique().tolist())
selected_channels = st.sidebar.multiselect("Acquisition Channel", options=channels, default=channels)

# Segment Filter
segments = sorted(tx_full['customer_segment'].dropna().unique().tolist())
selected_segments = st.sidebar.multiselect("Customer Segment", options=segments, default=segments)

# Apply Filters to tx_full
mask = (
    (tx_full['transaction_date'].dt.date >= start_date) & 
    (tx_full['transaction_date'].dt.date <= end_date) &
    (tx_full['acquisition_channel'].isin(selected_channels)) &
    (tx_full['customer_segment'].isin(selected_segments))
)

filtered_tx = tx_full[mask]

# --- NAVIGATION ---
st.sidebar.markdown("---")
page = st.sidebar.radio("Navigation", ["Unit Economics & Profit Leakage", "Customer LTV vs. CAC Matrix"])

# --- PAGE 1: Unit Economics & Profit Leakage ---
if page == "Unit Economics & Profit Leakage":
    st.title("💸 Unit Economics & Profit Leakage")
    st.markdown("Analyze gross-to-net revenue streams and identify key drivers of profit leakage.")
    
    if filtered_tx.empty:
        st.warning("No data available for the selected filters.")
    else:
        # KPIs
        gross_revenue = filtered_tx['total_amount'].sum()
        total_refunds = filtered_tx['refund_amount'].sum()
        net_revenue = gross_revenue - total_refunds
        total_tx = len(filtered_tx)
        returned_tx = filtered_tx['is_returned'].sum()
        return_rate = (returned_tx / total_tx) if total_tx > 0 else 0
        
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Gross Revenue", f"${gross_revenue:,.0f}")
        col2.metric("Total Refunds", f"${total_refunds:,.0f}")
        col3.metric("Net Revenue", f"${net_revenue:,.0f}")
        col4.metric("Return Rate", f"{return_rate:.1%}")
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        col_chart1, col_chart2 = st.columns(2)
        
        with col_chart1:
            st.subheader("Revenue to Net Profit Breakdown")
            fig_waterfall = go.Figure(go.Waterfall(
                name="20", orientation="v",
                measure=["absolute", "relative", "total"],
                x=["Gross Revenue", "Refunds", "Net Revenue"],
                textposition="outside",
                text=[f"${gross_revenue:,.0f}", f"-${total_refunds:,.0f}", f"${net_revenue:,.0f}"],
                y=[gross_revenue, -total_refunds, net_revenue],
                connector={"line":{"color":"rgb(63, 63, 63)"}},
                decreasing={"marker":{"color":"#EF4444"}},
                increasing={"marker":{"color":"#10B981"}},
                totals={"marker":{"color":"#3B82F6"}}
            ))
            fig_waterfall.update_layout(
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                margin=dict(l=20, r=20, t=40, b=20),
                showlegend=False
            )
            st.plotly_chart(fig_waterfall, use_container_width=True)
            
        with col_chart2:
            st.subheader("Return Reasons Breakdown")
            returned_data = filtered_tx[filtered_tx['is_returned']]
            if not returned_data.empty:
                reasons = returned_data['return_reason'].value_counts().reset_index()
                reasons.columns = ['return_reason', 'count']
                fig_reasons = px.pie(
                    reasons, names='return_reason', values='count', 
                    hole=0.4, color_discrete_sequence=px.colors.qualitative.Pastel
                )
                fig_reasons.update_layout(
                    plot_bgcolor='rgba(0,0,0,0)',
                    paper_bgcolor='rgba(0,0,0,0)',
                    margin=dict(l=20, r=20, t=20, b=20)
                )
                st.plotly_chart(fig_reasons, use_container_width=True)
            else:
                st.info("No return data available for the selected filters.")
            
        st.markdown("---")
        st.subheader("Time-Series Refund Trends")
        
        if not returned_data.empty:
            refund_trend = returned_data.groupby(pd.Grouper(key='return_date', freq='ME'))['refund_amount'].sum().reset_index()
            fig_trend = px.area(
                refund_trend, x='return_date', y='refund_amount', 
                color_discrete_sequence=["#EF4444"],
                labels={"return_date": "Date", "refund_amount": "Total Refund Amount ($)"}
            )
            fig_trend.update_layout(
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                xaxis=dict(showgrid=False),
                yaxis=dict(showgrid=True, gridcolor='#e5e7eb')
            )
            st.plotly_chart(fig_trend, use_container_width=True)
        else:
            st.info("No refunds in this period.")

# --- PAGE 2: Customer LTV vs. CAC Matrix ---
elif page == "Customer LTV vs. CAC Matrix":
    st.title("🎯 Customer LTV vs. CAC Matrix & Return Hotspots")
    st.markdown("Evaluate acquisition efficiency and product-market fit issues.")
    
    st.subheader("Customer Segment LTV vs. CAC")
    
    # Filter customer metrics by selected filters to align with global context
    filtered_customers = customer_metrics[
        (customer_metrics['acquisition_channel'].isin(selected_channels)) &
        (customer_metrics['customer_segment'].isin(selected_segments))
    ]
    
    if filtered_customers.empty or channel_performance.empty:
        st.warning("No data available for the selected filters to compute LTV vs CAC.")
    else:
        # Calculate Avg LTV per segment & channel
        segment_ltv = filtered_customers.groupby(['customer_segment', 'acquisition_channel'])['net_monetary'].mean().reset_index()
        segment_ltv.columns = ['customer_segment', 'channel', 'avg_ltv']
        
        # Merge with CAC from channel_performance
        cac_ltv = pd.merge(segment_ltv, channel_performance[['channel', 'cac']], on='channel', how='inner')
        
        if not cac_ltv.empty:
            # Add population size for bubble chart
            segment_counts = filtered_customers.groupby(['customer_segment', 'acquisition_channel']).size().reset_index(name='customer_count')
            cac_ltv = pd.merge(cac_ltv, segment_counts, left_on=['customer_segment', 'channel'], right_on=['customer_segment', 'acquisition_channel'])
            
            fig_scatter = px.scatter(
                cac_ltv, x='cac', y='avg_ltv', color='customer_segment', size='customer_count',
                hover_name='channel', hover_data=['customer_segment'],
                labels={'cac': 'Customer Acquisition Cost (CAC)', 'avg_ltv': 'Average Lifetime Value (LTV)'},
                color_discrete_sequence=px.colors.qualitative.Set2,
                size_max=40
            )
            
            # 3:1 LTV:CAC Ratio Line
            max_val = max(cac_ltv['cac'].max(), cac_ltv['avg_ltv'].max())
            if max_val > 0:
                fig_scatter.add_shape(
                    type='line', x0=0, y0=0, x1=max_val/3, y1=max_val,
                    line=dict(color='Gray', dash='dash'), name='3:1 LTV:CAC Ratio'
                )
                
            fig_scatter.update_layout(
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                xaxis=dict(showgrid=True, gridcolor='#e5e7eb'),
                yaxis=dict(showgrid=True, gridcolor='#e5e7eb')
            )
            st.plotly_chart(fig_scatter, use_container_width=True)
        else:
            st.info("Insufficient overlap between channel performance and customer segments.")
    
    st.markdown("---")
    st.subheader("Return Hotspots: Product Category vs. Size Tier")
    
    if filtered_tx.empty:
        st.warning("No transaction data available.")
    else:
        cat_size = filtered_tx.groupby(['product_category', 'size_tier']).agg(
            total_items=('transaction_id', 'count'),
            returned_items=('is_returned', 'sum')
        ).reset_index()
        
        cat_size['return_rate'] = cat_size['returned_items'] / cat_size['total_items']
        
        # Sort sizes logically if possible
        size_order = ["XS", "S", "M", "L", "XL"]
        existing_sizes = [s for s in size_order if s in cat_size['size_tier'].unique()]
        other_sizes = [s for s in cat_size['size_tier'].unique() if s not in existing_sizes]
        all_sizes = existing_sizes + other_sizes
        
        heatmap_data = cat_size.pivot(index='product_category', columns='size_tier', values='return_rate').fillna(0)
        heatmap_data = heatmap_data.reindex(columns=all_sizes)
        
        fig_heatmap = px.imshow(
            heatmap_data, 
            text_auto=".1%", 
            aspect="auto",
            color_continuous_scale="Reds",
            labels=dict(x="Size Tier", y="Product Category", color="Return Rate")
        )
        fig_heatmap.update_layout(
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            margin=dict(l=20, r=20, t=20, b=20)
        )
        st.plotly_chart(fig_heatmap, use_container_width=True)
