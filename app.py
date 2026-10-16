import io
from pathlib import Path

import pandas as pd
import streamlit as st


# --------------------------------------------------
# 1. PAGE SETTINGS AND THEME
# --------------------------------------------------
st.set_page_config(
    page_title="Retail Business Analytics",
    page_icon="📊",
    layout="wide",
)

st.markdown(
    """
    <style>
    :root { color-scheme: dark; }
    .stApp {
        background: radial-gradient(circle at 15% 0%, #142d4b 0%, #09182b 42%, #071321 100%);
        color: #edf4ff;
    }
    [data-testid="stHeader"] { background: rgba(7, 19, 33, 0.88); }
    [data-testid="stSidebar"] {
        background: #081629;
        border-right: 1px solid #203b59;
    }
    [data-testid="stSidebar"] * { color: #e6effb; }
    .block-container { padding-top: 1.5rem; padding-bottom: 2.5rem; max-width: 1500px; }
    h1 { letter-spacing: -0.035em; font-weight: 750 !important; }
    h2, h3 { letter-spacing: -0.02em; }
    [data-testid="stMetric"] {
        background: linear-gradient(145deg, rgba(18, 43, 70, 0.96), rgba(14, 34, 57, 0.96));
        border: 1px solid #254968;
        padding: 13px 16px;
        border-radius: 13px;
        min-height: 102px;
        box-shadow: 0 6px 18px rgba(0, 0, 0, 0.12);
    }
    [data-testid="stMetricLabel"] { color: #a9c2df; font-size: 0.82rem; }
    [data-testid="stMetricValue"] { color: #f4f8ff; font-size: 1.55rem; }
    [data-testid="stPlotlyChart"], [data-testid="stVegaLiteChart"], [data-testid="stArrowVegaLiteChart"] {
        border-radius: 12px;
    }
    [data-testid="stDataFrame"] {
        border: 1px solid #203f5e;
        border-radius: 10px;
        overflow: hidden;
    }
    div[data-testid="stVerticalBlock"] > div:has(> div[data-testid="stPlotlyChart"]) {
        background: rgba(13, 32, 53, 0.72);
        border: 1px solid #1d3e5d;
        border-radius: 13px;
        padding: 8px 10px 4px 10px;
    }
    .dashboard-subtitle { color: #a9c3df; margin-top: -12px; margin-bottom: 20px; font-size: 0.98rem; }
    .section-note { color: #a9c3df; font-size: 0.88rem; }
    div[data-testid="stHorizontalBlock"] { gap: 1rem; }
    .stDownloadButton button {
        border-radius: 9px;
        border: 1px solid #2d628d;
        background: #12395b;
        color: #f4f8ff;
        font-weight: 600;
    }
    .stDownloadButton button:hover { border-color: #5da8e5; background: #17466f; color: white; }
    hr { border-color: #203d5b; }
    </style>
    """,
    unsafe_allow_html=True,
)

st.title("📊 Retail Business Analytics")
st.markdown(
    '<p class="dashboard-subtitle">Sales performance · Profitability · Target tracking · Business insights</p>',
    unsafe_allow_html=True,
)


# --------------------------------------------------
# 2. LOAD AND VALIDATE DATA
# --------------------------------------------------
data_path = Path("data/processed/cleaned_sales.csv")
target_path = Path("data/raw/product_targets.csv")

if not data_path.exists():
    st.error("Cleaned sales data was not found. Run the data-preparation notebook first.")
    st.stop()

if not target_path.exists():
    st.error("Product targets file was not found at data/raw/product_targets.csv.")
    st.stop()

try:
    df = pd.read_csv(data_path, parse_dates=["Order_Date"])
    targets = pd.read_csv(target_path)
except Exception as exc:
    st.error(f"Could not read a data file: {exc}")
    st.stop()

required_sales_columns = [
    "Order_ID", "Order_Date", "Product", "Category",
    "Unit_Price", "Quantity", "Region", "Revenue",
]
required_target_columns = ["Product", "Monthly_Target"]

missing_sales = [col for col in required_sales_columns if col not in df.columns]
missing_targets = [col for col in required_target_columns if col not in targets.columns]

if missing_sales:
    st.error(f"Sales data is missing these columns: {missing_sales}")
    st.stop()

if missing_targets:
    st.error(f"Target data is missing these columns: {missing_targets}")
    st.stop()

for col in ["Unit_Price", "Quantity", "Revenue"]:
    df[col] = pd.to_numeric(df[col], errors="coerce")

targets["Monthly_Target"] = pd.to_numeric(targets["Monthly_Target"], errors="coerce")
df = df.dropna(subset=["Order_Date", "Product", "Category", "Region", "Revenue", "Unit_Price", "Quantity"]).copy()
targets = targets.dropna(subset=["Product", "Monthly_Target"]).copy()

if df.empty:
    st.error("The cleaned sales dataset has no valid records.")
    st.stop()

if targets["Product"].duplicated().any():
    st.error("Each product must appear only once in product_targets.csv.")
    st.stop()

if (targets["Monthly_Target"] < 0).any():
    st.error("Monthly targets cannot be negative.")
    st.stop()

target_products = set(targets["Product"].astype(str))
sales_products = set(df["Product"].astype(str))
unmatched_products = sorted(sales_products - target_products)
if unmatched_products:
    st.warning(f"No target is defined for: {', '.join(unmatched_products)}. Target analysis will exclude these products.")


# --------------------------------------------------
# 3. SIDEBAR FILTERS
# --------------------------------------------------
st.sidebar.title("Dashboard Filters")
st.sidebar.caption("Adjust the selections to update the dashboard.")

min_date = df["Order_Date"].min().date()
max_date = df["Order_Date"].max().date()

date_range = st.sidebar.date_input(
    "Order date range",
    value=(min_date, max_date),
    min_value=min_date,
    max_value=max_date,
)

if isinstance(date_range, (tuple, list)) and len(date_range) == 2:
    start_date, end_date = date_range
elif isinstance(date_range, (tuple, list)) and len(date_range) == 1:
    start_date = end_date = date_range[0]
else:
    start_date, end_date = min_date, max_date

regions = sorted(df["Region"].astype(str).unique())
products = sorted(df["Product"].astype(str).unique())

selected_regions = st.sidebar.multiselect("Region", regions, default=regions)
selected_products = st.sidebar.multiselect("Product", products, default=products)

filtered = df[
    df["Region"].astype(str).isin(selected_regions)
    & df["Product"].astype(str).isin(selected_products)
    & (df["Order_Date"].dt.date >= start_date)
    & (df["Order_Date"].dt.date <= end_date)
].copy()

if filtered.empty:
    st.warning("No sales records match these filters. Adjust the date, region, or product selection.")
    st.stop()


# --------------------------------------------------
# 4. ESTIMATED PROFIT
# --------------------------------------------------
# Demonstration assumptions only; these are not verified business costs.
cost_rates = {
    "Laptop": 0.80,
    "Mouse": 0.55,
    "Keyboard": 0.60,
    "Monitor": 0.75,
    "Headphones": 0.60,
    "Printer": 0.78,
}
filtered["Estimated_Cost"] = (
    filtered["Unit_Price"] * filtered["Quantity"]
    * filtered["Product"].map(cost_rates).fillna(0.70)
)
filtered["Estimated_Profit"] = filtered["Revenue"] - filtered["Estimated_Cost"]
filtered["Profit_Margin"] = (
    filtered["Estimated_Profit"] / filtered["Revenue"].replace(0, float("nan"))
) * 100


# --------------------------------------------------
# 5. KPI CARDS
# --------------------------------------------------
revenue = filtered["Revenue"].sum()
orders = filtered["Order_ID"].nunique()
units = filtered["Quantity"].sum()
average_order_value = revenue / orders if orders else 0
estimated_profit = filtered["Estimated_Profit"].sum()
profit_margin = estimated_profit / revenue * 100 if revenue else 0

st.subheader("Performance Overview")
k1, k2, k3 = st.columns(3)
k1.metric("Total Revenue", f"₹{revenue:,.0f}")
k2.metric("Total Orders", f"{orders:,}")
k3.metric("Units Sold", f"{units:,.0f}")

k4, k5, k6 = st.columns(3)
k4.metric("Average Revenue / Order", f"₹{average_order_value:,.2f}")
k5.metric("Estimated Profit", f"₹{estimated_profit:,.0f}")
k6.metric("Estimated Profit Margin", f"{profit_margin:.1f}%")

st.caption("Profit and margin are estimates based on assumed product costs, not verified business costs.")


# --------------------------------------------------
# 6. PREPARE MONTHLY TARGET PERFORMANCE
# --------------------------------------------------
sales_with_targets = filtered.merge(targets, on="Product", how="left")
sales_with_targets["Month"] = sales_with_targets["Order_Date"].dt.to_period("M").astype(str)

monthly_sales = (
    sales_with_targets
    .groupby(["Month", "Product"], as_index=False)
    .agg(
        Actual_Revenue=("Revenue", "sum"),
        Monthly_Target=("Monthly_Target", "first"),
    )
)

# Prorate monthly targets for the selected portion of each calendar month.
monthly_sales["Month_Start"] = pd.to_datetime(monthly_sales["Month"] + "-01")
monthly_sales["Month_End"] = monthly_sales["Month_Start"] + pd.offsets.MonthEnd(0)
monthly_sales["Selected_Start"] = monthly_sales["Month_Start"].dt.date.apply(lambda d: max(d, start_date))
monthly_sales["Selected_End"] = monthly_sales["Month_End"].dt.date.apply(lambda d: min(d, end_date))
monthly_sales["Selected_Days"] = (
    (monthly_sales["Selected_End"] - monthly_sales["Selected_Start"]).apply(lambda d: max(0, d.days + 1))
)
monthly_sales["Days_In_Month"] = monthly_sales["Month_End"].dt.days_in_month
monthly_sales["Monthly_Target"] = (
    monthly_sales["Monthly_Target"]
    * monthly_sales["Selected_Days"]
    / monthly_sales["Days_In_Month"]
)

monthly_sales["Achievement_Percentage"] = (
    monthly_sales["Actual_Revenue"]
    / monthly_sales["Monthly_Target"].replace(0, float("nan"))
) * 100
monthly_sales["Target_Gap"] = monthly_sales["Actual_Revenue"] - monthly_sales["Monthly_Target"]

valid_target_sales = monthly_sales.dropna(subset=["Monthly_Target"]).copy()
total_actual = valid_target_sales["Actual_Revenue"].sum()
total_target = valid_target_sales["Monthly_Target"].sum()
overall_achievement = total_actual / total_target * 100 if total_target > 0 else 0


# --------------------------------------------------
# 7. TARGET PERFORMANCE
# --------------------------------------------------
st.divider()
st.subheader("🎯 Sales vs Monthly Target")

t1, t2, t3 = st.columns(3)
t1.metric("Actual Revenue (targeted products)", f"₹{total_actual:,.0f}")
t2.metric("Adjusted Target", f"₹{total_target:,.0f}")
t3.metric("Target Achievement", f"{overall_achievement:.1f}%")

left, right = st.columns([1.25, 1])

with left:
    st.markdown("#### Actual Revenue vs Target")
    if not valid_target_sales.empty:
        product_comparison = (
            valid_target_sales.groupby("Product", as_index=False)
            .agg(
                Actual_Revenue=("Actual_Revenue", "sum"),
                Target_Revenue=("Monthly_Target", "sum"),
            )
            .set_index("Product")
            .sort_values("Actual_Revenue")
        )
        st.bar_chart(
            product_comparison,
            height=210,
            x_label="Product",
            y_label="Revenue (₹)",
        )
    else:
        st.info("No target data is available for the selected products.")

with right:
    st.markdown("#### Monthly Target Achievement")
    if not valid_target_sales.empty:
        monthly_performance = (
            valid_target_sales.groupby("Month", as_index=False)
            .agg(
                Actual_Revenue=("Actual_Revenue", "sum"),
                Target_Revenue=("Monthly_Target", "sum"),
            )
        )
        monthly_performance["Achievement (%)"] = (
            monthly_performance["Actual_Revenue"]
            / monthly_performance["Target_Revenue"].replace(0, float("nan"))
        ) * 100
        st.line_chart(
            monthly_performance.set_index("Month")[["Achievement (%)"]],
            height=210,
            y_label="Achievement (%)",
        )
        st.caption("100% means the adjusted target was achieved.")
    else:
        st.info("No target data is available for the selected products.")

st.markdown("#### Product-wise Target Performance")
if not valid_target_sales.empty:
    target_table = valid_target_sales[
        ["Month", "Product", "Actual_Revenue", "Monthly_Target", "Achievement_Percentage", "Target_Gap"]
    ].rename(
        columns={
            "Actual_Revenue": "Actual Revenue (₹)",
            "Monthly_Target": "Adjusted Target (₹)",
            "Achievement_Percentage": "Achievement (%)",
            "Target_Gap": "Difference (₹)",
        }
    )
    st.dataframe(target_table.round(2), width="stretch", height=280)
else:
    st.info("No target performance rows are available.")


# --------------------------------------------------
# 8. SALES CHARTS
# --------------------------------------------------
st.divider()
st.subheader("Sales Analysis")
st.caption("Compact view · compare product, region, category, and estimated profitability at a glance.")

chart_left, chart_right = st.columns(2)

with chart_left:
    st.markdown("#### Revenue by Product")
    revenue_by_product = filtered.groupby("Product")["Revenue"].sum().sort_values()
    st.bar_chart(
        revenue_by_product,
        horizontal=True,
        height=175,
        x_label="Revenue (₹)",
        y_label="Product",
    )

with chart_right:
    st.markdown("#### Revenue by Region")
    revenue_by_region = filtered.groupby("Region")["Revenue"].sum().sort_values(ascending=False)
    st.bar_chart(
        revenue_by_region,
        height=175,
        x_label="Region",
        y_label="Revenue (₹)",
    )

category_col, profit_col = st.columns(2)

with category_col:
    st.markdown("#### Revenue by Category")
    category_revenue = filtered.groupby("Category")["Revenue"].sum().sort_values(ascending=False)
    st.bar_chart(
        category_revenue,
        horizontal=True,
        height=160,
        x_label="Revenue (₹)",
        y_label="Category",
    )

with profit_col:
    st.markdown("#### Estimated Profit by Product")
    profit_by_product = filtered.groupby("Product")["Estimated_Profit"].sum().sort_values()
    st.bar_chart(
        profit_by_product,
        horizontal=True,
        height=175,
        x_label="Estimated profit (₹)",
        y_label="Product",
    )

st.markdown("#### Monthly Revenue Trend")
filtered["Month"] = filtered["Order_Date"].dt.to_period("M").astype(str)
monthly_revenue = filtered.groupby("Month")["Revenue"].sum().sort_index()
st.line_chart(monthly_revenue, height=210, y_label="Revenue (₹)")


# --------------------------------------------------
# 9. BUSINESS INSIGHTS
# --------------------------------------------------
st.divider()
st.subheader("💡 Business Insights")

product_revenue = filtered.groupby("Product")["Revenue"].sum()
region_revenue = filtered.groupby("Region")["Revenue"].sum()
best_product = product_revenue.idxmax()
best_region = region_revenue.idxmax()

i1, i2 = st.columns(2)
with i1:
    st.info(f"**Top product:** {best_product}  \nRevenue: ₹{product_revenue[best_product]:,.0f}")
with i2:
    st.info(f"**Top region:** {best_region}  \nRevenue: ₹{region_revenue[best_region]:,.0f}")

if len(monthly_revenue) >= 2:
    previous_month = monthly_revenue.iloc[-2]
    latest_month = monthly_revenue.iloc[-1]
    if previous_month != 0:
        growth = (latest_month - previous_month) / previous_month * 100
        st.metric("Latest Month Revenue Growth", f"{growth:.1f}%", delta=f"{growth:.1f}%")
    else:
        st.caption("Monthly growth cannot be calculated because the previous month's revenue was zero.")
else:
    st.caption("More than one month of data is needed to calculate monthly revenue growth.")

if not valid_target_sales.empty:
    product_performance = (
        valid_target_sales.groupby("Product")
        .agg(
            Actual_Revenue=("Actual_Revenue", "sum"),
            Target_Revenue=("Monthly_Target", "sum"),
        )
    )
    product_performance["Achievement (%)"] = (
        product_performance["Actual_Revenue"]
        / product_performance["Target_Revenue"].replace(0, float("nan"))
    ) * 100
    product_performance = product_performance.dropna(subset=["Achievement (%)"])

    if not product_performance.empty:
        best_target_product = product_performance["Achievement (%)"].idxmax()
        lowest_target_product = product_performance["Achievement (%)"].idxmin()
        i3, i4 = st.columns(2)
        with i3:
            st.success(
                f"**Best target performance:** {best_target_product} "
                f"({product_performance.loc[best_target_product, 'Achievement (%)']:.1f}%)"
            )
        with i4:
            st.warning(
                f"**Lowest target performance:** {lowest_target_product} "
                f"({product_performance.loc[lowest_target_product, 'Achievement (%)']:.1f}%)"
            )
        below_target = product_performance[product_performance["Achievement (%)"] < 100]
        if not below_target.empty:
            st.info("Below target: " + ", ".join(below_target.index.astype(str)))
        else:
            st.success("All products with defined targets met or exceeded their targets.")


# --------------------------------------------------
# 10. SALES DATA TABLE
# --------------------------------------------------
st.divider()
st.subheader("Sales Data")
st.dataframe(filtered.drop(columns=["Month"], errors="ignore"), width="stretch", height=320)


# --------------------------------------------------
# 11. DOWNLOAD REPORTS
# --------------------------------------------------
st.divider()
st.subheader("Download Reports")

sales_report = filtered.drop(columns=["Month"], errors="ignore").copy()

target_report = valid_target_sales[
    ["Month", "Product", "Actual_Revenue", "Monthly_Target", "Achievement_Percentage", "Target_Gap"]
].rename(
    columns={
        "Actual_Revenue": "Actual Revenue (INR)",
        "Monthly_Target": "Adjusted Target (INR)",
        "Achievement_Percentage": "Achievement (%)",
        "Target_Gap": "Revenue Difference (INR)",
    }
).copy()

if not target_report.empty:
    numeric_columns = [
        "Actual Revenue (INR)",
        "Adjusted Target (INR)",
        "Achievement (%)",
        "Revenue Difference (INR)",
    ]
    target_report[numeric_columns] = target_report[numeric_columns].round(2)

download_left, download_right = st.columns(2)

with download_left:
    st.download_button(
        "Download Target Performance CSV",
        data=target_report.to_csv(index=False).encode("utf-8-sig"),
        file_name="target_performance_report.csv",
        mime="text/csv",
        use_container_width=True,
    )

excel_buffer = io.BytesIO()
with pd.ExcelWriter(excel_buffer, engine="openpyxl") as writer:
    sales_report.to_excel(writer, sheet_name="Sales Data", index=False)
    target_report.to_excel(writer, sheet_name="Target Performance", index=False)

with download_right:
    st.download_button(
        "Download Complete Excel Report",
        data=excel_buffer.getvalue(),
        file_name="business_analytics_report.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        use_container_width=True,
    )

st.caption(
    "Target values are sample planning assumptions. Partial-month targets are prorated by calendar days; "
    "profit figures are estimates based on assumed product costs."
)
