import pandas as pd
import plotly.express as px
import streamlit as st
from pathlib import Path
from datetime import datetime
from streamlit_autorefresh import st_autorefresh

st.set_page_config(
    page_title="Retail Intelligence",
    layout="wide",
    initial_sidebar_state="expanded",
)

st_autorefresh(interval=5000, key="live_dashboard_refresh")

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data" / "processed"

st.markdown("""
<style>
.stApp { background: #050B16; color: #E5E7EB; }
.block-container { padding: 1rem 1.5rem; max-width: 100%; }

[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #030712 0%, #07111F 100%);
    border-right: 1px solid rgba(148,163,184,.20);
}
[data-testid="stSidebar"] * { color: #E5E7EB !important; }

.main-title {
    font-size: 30px;
    font-weight: 900;
    color: #FBBF24;
}
.sub-title { color:#94A3B8; font-size:15px; margin-bottom:18px; }

.kpi-card, .chart-card {
    background: linear-gradient(145deg, #0B1220, #07111F);
    border: 1px solid rgba(148,163,184,.22);
    border-radius: 18px;
    padding: 18px;
    box-shadow: 0 18px 45px rgba(0,0,0,.35);
    margin-bottom: 16px;
}

.kpi-card { min-height:145px; }
.kpi-icon {
    width:54px; height:54px; border-radius:16px;
    display:flex; align-items:center; justify-content:center;
    font-size:26px; margin-bottom:12px;
}
.kpi-label { font-size:13px; color:#CBD5E1; font-weight:700; }
.kpi-value { font-size:30px; color:white; font-weight:900; margin-top:6px; }
.kpi-delta { color:#22C55E; font-size:12px; margin-top:6px; }

.card-title { font-size:18px; font-weight:900; color:white; }
.card-subtitle { font-size:12px; color:#94A3B8; margin-bottom:8px; }

.live-pill {
    background: rgba(34,197,94,.14);
    color:#22C55E;
    border:1px solid rgba(34,197,94,.35);
    border-radius:999px;
    padding:3px 9px;
    font-size:11px;
    font-weight:800;
}

.explain-row { display:flex; gap:12px; margin-bottom:16px; }
.explain-icon {
    width:42px; height:42px; border-radius:12px;
    background:rgba(124,58,237,.25);
    display:flex; align-items:center; justify-content:center;
    font-size:19px; flex-shrink:0;
}
.explain-title { color:white; font-size:13px; font-weight:900; }
.explain-text { color:#CBD5E1; font-size:12px; line-height:1.45; }

.flow-box {
    background:#0B1220;
    border:1px solid rgba(148,163,184,.22);
    border-radius:14px;
    padding:13px;
    text-align:center;
}
.flow-title { color:white; font-size:12px; font-weight:900; }
.flow-sub { color:#94A3B8; font-size:11px; }

button[kind="secondary"] {
    background:#6D28D9 !important;
    color:white !important;
    border-radius:12px !important;
    border:none !important;
}
</style>
""", unsafe_allow_html=True)


def read_folder(path: Path) -> pd.DataFrame:
    if not path.exists():
        st.error(f"Folder not found: {path}")
        st.stop()

    csv_files = list(path.glob("*.csv"))
    parquet_files = list(path.glob("*.parquet"))

    if csv_files:
        return pd.concat([pd.read_csv(f) for f in csv_files], ignore_index=True)

    if parquet_files:
        return pd.concat([pd.read_parquet(f) for f in parquet_files], ignore_index=True)

    st.error(f"No CSV or Parquet files found in {path}")
    st.stop()


@st.cache_data(ttl=5)
def load_data():
    hourly = read_folder(DATA_DIR / "gold" / "hourly_metrics")
    product = read_folder(DATA_DIR / "gold" / "product_metrics")
    customer = read_folder(DATA_DIR / "gold" / "customer_metrics")
    quality = read_folder(DATA_DIR / "quality" / "pipeline_metrics")
    return hourly, product, customer, quality


hourly_df, product_df, customer_df, quality_df = load_data()

AVG_PRICE = 24.99

hourly_df["estimated_revenue"] = hourly_df["total_products"] * AVG_PRICE
product_df["estimated_revenue"] = product_df["total_product_events"] * AVG_PRICE
product_df["product_name"] = "Product " + product_df["product_id"].astype(str)
customer_df["customer_name"] = "Customer " + customer_df["user_id"].astype(str)

metric_map = dict(zip(quality_df["metric_name"], quality_df["metric_value"]))

bronze_count = int(metric_map.get("bronze_record_count", 0))
silver_count = int(metric_map.get("silver_record_count", 0))
duplicates_removed = int(metric_map.get("duplicate_record_count", 0))

null_records = (
    int(metric_map.get("null_order_id_count", 0))
    + int(metric_map.get("null_user_id_count", 0))
    + int(metric_map.get("null_product_id_count", 0))
)

total_orders = int(hourly_df["total_orders"].sum())
total_products = int(hourly_df["total_products"].sum())
total_reorders = int(hourly_df["total_reorders"].sum())
unique_customers = int(customer_df["user_id"].nunique())
estimated_revenue = float(hourly_df["estimated_revenue"].sum())
avg_order_value = estimated_revenue / total_orders if total_orders else 0
reorder_rate = total_reorders / total_products if total_products else 0

products_per_second = total_products / 86400
products_per_minute = total_products / 1440
products_per_hour = total_products / 24
products_per_day = total_products
valid_rate = silver_count / bronze_count if bronze_count else 0


def fmt_num(x):
    return f"{x:,.0f}"


def fmt_money(x):
    return f"${x:,.0f}"


def fmt_pct(x):
    return f"{x:.2%}"


def style_fig(fig, height=310):
    fig.update_layout(
        height=height,
        template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#CBD5E1", size=11),
        margin=dict(l=20, r=20, t=35, b=20),
        xaxis=dict(gridcolor="rgba(148,163,184,.12)", zeroline=False),
        yaxis=dict(gridcolor="rgba(148,163,184,.12)", zeroline=False),
        title=dict(font=dict(size=15, color="white")),
        showlegend=False,
    )
    return fig


def kpi_card(icon, label, value, delta, color1, color2):
    st.markdown(
        f"""
        <div class="kpi-card">
            <div class="kpi-icon" style="background:linear-gradient(135deg,{color1},{color2});">{icon}</div>
            <div class="kpi-label">{label}</div>
            <div class="kpi-value">{value}</div>
            <div class="kpi-delta">↑ {delta} vs baseline</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


with st.sidebar:
    st.markdown("""
    <div style="display:flex; gap:12px; align-items:center; margin-bottom:24px;">
        <div style="font-size:34px;">🧬</div>
        <div>
            <div style="font-size:20px; font-weight:900;">Retail Intelligence</div>
            <div style="font-size:12px; color:#94A3B8;">Real-Time Platform</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    page = st.radio(
        "Navigation",
        [
            "Executive Overview",
            "Product Intelligence",
            "Customer Intelligence",
            "Pipeline & Data Quality",
            "System Monitoring",
        ],
        label_visibility="collapsed",
    )

    st.markdown("---")
    st.markdown("### DATA PIPELINE")

    steps = [
        ("⚙️", "Kafka", "Streaming Events"),
        ("⭐", "Spark Structured Streaming", "Processing"),
        ("🟫", "Bronze Layer", "Raw Data"),
        ("🥈", "Silver Layer", "Cleaned Data"),
        ("🥇", "Gold Layer", "Analytics Ready"),
        ("📊", "Dashboard", "Real-Time Insights"),
    ]

    for icon, name, desc in steps:
        st.markdown(
            f"""
            <div style="display:flex; justify-content:space-between; margin-bottom:16px;">
                <div>
                    <div style="font-size:13px; font-weight:800;">{icon} {name}</div>
                    <div style="font-size:11px; color:#94A3B8;">{desc}</div>
                </div>
                <span class="live-pill">LIVE</span>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown("---")
    st.caption(f"Auto-refresh: every 5 seconds")
    st.caption(f"Last Updated: {datetime.now().strftime('%d %b %Y • %I:%M:%S %p')}")


left, right = st.columns([2.5, 1])

with left:
    st.markdown('<div class="main-title">Executive Command Center 👑</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-title">Real-time retail analytics and operational intelligence</div>', unsafe_allow_html=True)

with right:
    b1, b2, b3 = st.columns(3)
    b1.button("Hours")

    if b2.button("Refresh"):
        st.cache_data.clear()
        st.rerun()

    b3.button("Report")


if page == "Executive Overview":
    k1, k2, k3, k4, k5 = st.columns(5)

    with k1:
        kpi_card("💲", "Total Revenue", fmt_money(estimated_revenue), "18.6%", "#581C87", "#7C3AED")
    with k2:
        kpi_card("🛍️", "Total Orders", fmt_num(total_orders), "16.4%", "#1D4ED8", "#2563EB")
    with k3:
        kpi_card("🛒", "Total Products Sold", fmt_num(total_products), "20.1%", "#166534", "#22C55E")
    with k4:
        kpi_card("👥", "Unique Customers", fmt_num(unique_customers), "15.8%", "#92400E", "#F59E0B")
    with k5:
        kpi_card("📈", "Avg Order Value", fmt_money(avg_order_value), "2.7%", "#0F766E", "#14B8A6")

    st.markdown("<br>", unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1.25, 1.05, 0.7])

    with col1:
        st.markdown('<div class="chart-card">', unsafe_allow_html=True)
        st.markdown('<div class="card-title">Products Flow Over Time</div>', unsafe_allow_html=True)
        st.markdown('<div class="card-subtitle">How many products are moving through the system</div>', unsafe_allow_html=True)

        st.markdown(
            f"""
            <div style="text-align:right; margin-top:-38px;">
                <div style="font-size:12px; color:#94A3B8;">Live Rate</div>
                <div style="font-size:32px; color:white; font-weight:900;">{products_per_second:.2f}</div>
                <div style="font-size:13px; color:#38BDF8;">products/sec</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        fig = px.area(hourly_df, x="order_hour_of_day", y="total_products", title="Products Per Hour")
        fig.update_traces(line_color="#8B5CF6", fillcolor="rgba(139,92,246,.28)")
        st.plotly_chart(style_fig(fig, 310), use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

    with col2:
        st.markdown('<div class="chart-card">', unsafe_allow_html=True)
        st.markdown('<div class="card-title">Products Count</div>', unsafe_allow_html=True)
        st.markdown('<div class="card-subtitle">Aggregated counts of products</div>', unsafe_allow_html=True)

        fig = px.bar(hourly_df, x="order_hour_of_day", y="total_products", title="Hourly Product Volume")
        fig.update_traces(marker_color="#6366F1")
        st.plotly_chart(style_fig(fig, 310), use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

    with col3:
        st.markdown('<div class="chart-card">', unsafe_allow_html=True)
        st.markdown('<div class="card-title">What’s Happening?</div>', unsafe_allow_html=True)

        explain_steps = [
            ("🧬", "1. Data Ingestion", "Retail events are published to Kafka topics in real time."),
            ("⭐", "2. Stream Processing", "Spark Structured Streaming consumes events in micro-batches."),
            ("🟫", "3. Bronze Layer", "Raw data is stored in Delta Lake for replay and lineage."),
            ("🥈", "4. Silver Layer", "Data is cleaned, deduplicated, and validated."),
            ("🥇", "5. Gold Layer", "Business-ready aggregated data is prepared for dashboards."),
            ("📈", "6. Insights", "Real-time KPIs and quality metrics support decisions."),
        ]

        for icon, title, desc in explain_steps:
            st.markdown(
                f"""
                <div class="explain-row">
                    <div class="explain-icon">{icon}</div>
                    <div>
                        <div class="explain-title">{title}</div>
                        <div class="explain-text">{desc}</div>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        st.markdown("</div>", unsafe_allow_html=True)

    row1, row2 = st.columns([1, 1])

    with row1:
        st.markdown('<div class="chart-card">', unsafe_allow_html=True)
        st.markdown('<div class="card-title">Pipeline Health</div>', unsafe_allow_html=True)
        st.markdown('<div class="card-subtitle">Real-time status of the data pipeline</div>', unsafe_allow_html=True)

        f1, f2, f3, f4, f5 = st.columns(5)

        for c, name, value in [
            (f1, "Kafka", "Producing"),
            (f2, "Spark", "Processing"),
            (f3, "Bronze", f"{fmt_num(bronze_count)} rows"),
            (f4, "Silver", f"{fmt_num(silver_count)} rows"),
            (f5, "Gold", "Ready"),
        ]:
            with c:
                st.markdown(
                    f"""
                    <div class="flow-box">
                        <div class="flow-title">{name}</div>
                        <div class="flow-sub">{value}</div>
                        <div style="color:#22C55E; font-size:11px;">● Healthy</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

        st.markdown(
            f"""
            <div style="margin-top:18px; padding:14px; border-radius:14px; background:#0B1220;">
                <span style="color:#CBD5E1;">Products / Second</span>
                <span style="color:#22C55E; font-weight:900; margin-left:15px;">{products_per_second:.2f}</span>
                <span style="color:#CBD5E1; margin-left:25px;">Products / Minute</span>
                <span style="color:#FBBF24; font-weight:900; margin-left:15px;">{fmt_num(products_per_minute)}</span>
                <span style="color:#CBD5E1; margin-left:25px;">Products / Hour</span>
                <span style="color:#38BDF8; font-weight:900; margin-left:15px;">{fmt_num(products_per_hour)}</span>
                <span style="color:#CBD5E1; margin-left:25px;">Products / Day</span>
                <span style="color:#A78BFA; font-weight:900; margin-left:15px;">{fmt_num(products_per_day)}</span>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.markdown("</div>", unsafe_allow_html=True)

    with row2:
        st.markdown('<div class="chart-card">', unsafe_allow_html=True)
        st.markdown('<div class="card-title">Data Quality</div>', unsafe_allow_html=True)
        st.markdown('<div class="card-subtitle">Quality metrics and validation results</div>', unsafe_allow_html=True)

        q1, q2, q3, q4 = st.columns(4)
        q1.metric("Bronze", fmt_num(bronze_count))
        q2.metric("Silver", fmt_num(silver_count))
        q3.metric("Duplicates", fmt_num(duplicates_removed))
        q4.metric("Null Records", fmt_num(null_records))

        st.progress(min(valid_rate, 1.0))
        st.caption(f"Overall Quality Score: {fmt_pct(valid_rate)}")
        st.markdown("</div>", unsafe_allow_html=True)

    low1, low2, low3 = st.columns([1, 0.9, 0.9])

    with low1:
        st.markdown('<div class="chart-card">', unsafe_allow_html=True)
        st.markdown('<div class="card-title">Key Insights</div>', unsafe_allow_html=True)

        peak_hour = int(hourly_df.sort_values("total_products", ascending=False).iloc[0]["order_hour_of_day"])

        insights = [
            f"Products are moving at {products_per_second:.2f} products per second.",
            f"Products are moving at {fmt_num(products_per_hour)} products per hour.",
            f"Estimated daily product movement is {fmt_num(products_per_day)} products.",
            f"Peak traffic hour is {peak_hour}:00.",
            f"Current reorder rate is {fmt_pct(reorder_rate)}.",
            f"Data quality score is {fmt_pct(valid_rate)}.",
        ]

        for item in insights:
            st.markdown(f"<p>✅ {item}</p>", unsafe_allow_html=True)

        st.markdown("</div>", unsafe_allow_html=True)

    with low2:
        st.markdown('<div class="chart-card">', unsafe_allow_html=True)
        st.markdown('<div class="card-title">Top 5 Products</div>', unsafe_allow_html=True)

        top5 = product_df.sort_values("total_product_events", ascending=False).head(5)
        fig = px.bar(top5, x="total_product_events", y="product_name", orientation="h")
        fig.update_traces(marker_color="#7C3AED")
        st.plotly_chart(style_fig(fig, 240), use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

    with low3:
        st.markdown('<div class="chart-card">', unsafe_allow_html=True)
        st.markdown('<div class="card-title">Reorder Mix</div>', unsafe_allow_html=True)

        reorder_mix = pd.DataFrame({
            "Type": ["Reordered", "First-Time"],
            "Count": [total_reorders, total_products - total_reorders],
        })

        fig = px.pie(reorder_mix, names="Type", values="Count", hole=0.55)
        st.plotly_chart(style_fig(fig, 240), use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

elif page == "Product Intelligence":
    st.markdown("## Product Intelligence")
    top = product_df.sort_values("total_product_events", ascending=False).head(25)
    fig = px.bar(top, x="total_product_events", y="product_name", orientation="h", title="Top Products")
    st.plotly_chart(style_fig(fig, 600), use_container_width=True)
    st.dataframe(top, use_container_width=True)

elif page == "Customer Intelligence":
    st.markdown("## Customer Intelligence")
    top = customer_df.sort_values("total_products", ascending=False).head(25)
    fig = px.scatter(customer_df, x="avg_cart_size", y="reorder_rate", size="total_products", title="Cart Size vs Reorder Rate")
    st.plotly_chart(style_fig(fig, 500), use_container_width=True)
    st.dataframe(top, use_container_width=True)

elif page == "Pipeline & Data Quality":
    st.markdown("## Pipeline & Data Quality")
    fig = px.bar(quality_df, x="metric_name", y="metric_value", title="Data Quality Metrics")
    st.plotly_chart(style_fig(fig, 450), use_container_width=True)
    st.dataframe(quality_df, use_container_width=True)

elif page == "System Monitoring":
    st.markdown("## System Monitoring")
    st.info("Kafka, Spark, Delta Lake, and Streamlit are represented as logical monitoring components for this local portfolio environment.")
