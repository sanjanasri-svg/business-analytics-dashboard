
import io
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
import streamlit as st


# --------------------------------------------------
# 1. PAGE SETTINGS
# --------------------------------------------------

st.set_page_config(
    page_title="Business Analytics Dashboard",
    page_icon="📊",
    layout="wide"
)

st.title("📊 Retail Business Analytics Dashboard")
st.caption("Sales performance, profitability, and business insights")


# --------------------------------------------------
# 2. LOAD DATA
# --------------------------------------------------

data_path = Path("data/processed/cleaned_sales.csv")

if not data_path.exists():
    st.error(
        "Cleaned data not found. "
        "Run the data-preparation notebook first."
    )
    st.stop()

df = pd.read_csv(data_path, parse_dates=["Order_Date"])

# Load product targets
target_path = Path("data/raw/product_targets.csv")

if not target_path.exists():
    st.error("Product targets file not found: data/raw/product_targets.csv")
    st.stop()

targets = pd.read_csv(target_path)

required_target_columns = ["Product", "Monthly_Target"]

if not all(column in targets.columns for column in required_target_columns):
    st.error("Target file must contain Product and Monthly_Target columns.")
    st.stop()

targets["Monthly_Target"] = pd.to_numeric(
    targets["Monthly_Target"], errors="coerce"
)

if targets["Monthly_Target"].isna().any():
    st.error("Monthly_Target must contain valid numbers.")
    st.stop()

if targets["Product"].duplicated().any():
    st.error("Each product must appear only once in product_targets.csv.")
    st.stop()


if df.empty:
    st.error("The sales dataset is empty.")
    st.stop()

required_columns = [
    "Order_ID", "Order_Date", "Product", "Category",
    "Unit_Price", "Quantity", "Region", "Revenue"
]

missing_columns = [
    column for column in required_columns
    if column not in df.columns
]

if missing_columns:
    st.error(f"Missing columns in dataset: {missing_columns}")
    st.stop()

df = df.dropna(
    subset=["Order_Date", "Product", "Category", "Region"]
).copy()

if df.empty:
    st.error("No valid sales records are available.")
    st.stop()


# --------------------------------------------------
# 3. SIDEBAR FILTERS
# --------------------------------------------------

st.sidebar.header("Dashboard Filters")

min_date = df["Order_Date"].min().date()
max_date = df["Order_Date"].max().date()

date_range = st.sidebar.date_input(
    "Select date range",
    value=(min_date, max_date),
    min_value=min_date,
    max_value=max_date
)

regions = sorted(df["Region"].unique())

selected_regions = st.sidebar.multiselect(
    "Select regions",
    regions,
    default=regions
)

products = sorted(df["Product"].unique())

selected_products = st.sidebar.multiselect(
    "Select products",
    products,
    default=products
)


# --------------------------------------------------
# 4. FILTER SALES DATA
# --------------------------------------------------

if len(date_range) == 2:
    start_date, end_date = date_range
elif len(date_range) == 1:
    start_date = end_date = date_range[0]
else:
    start_date, end_date = min_date, max_date

filtered = df[
    df["Region"].isin(selected_regions)
    & df["Product"].isin(selected_products)
    & (df["Order_Date"].dt.date >= start_date)
    & (df["Order_Date"].dt.date <= end_date)
].copy()


# --------------------------------------------------
# 5. ESTIMATED PROFIT CALCULATION
# --------------------------------------------------

# Demonstration assumptions, not actual business costs.
cost_rates = {
    "Laptop": 0.80,
    "Mouse": 0.55,
    "Keyboard": 0.60,
    "Monitor": 0.75,
    "Headphones": 0.60,
    "Printer": 0.78
}

filtered["Estimated_Cost"] = (
    filtered["Unit_Price"]
    * filtered["Quantity"]
    * filtered["Product"].map(cost_rates).fillna(0.70)
)

filtered["Estimated_Profit"] = (
    filtered["Revenue"] - filtered["Estimated_Cost"]
)

filtered["Profit_Margin"] = (
    filtered["Estimated_Profit"]
    / filtered["Revenue"].replace(0, float("nan"))
) * 100


# --------------------------------------------------
# 6. KPI CARDS
# --------------------------------------------------

st.subheader("Key Performance Indicators")

revenue = filtered["Revenue"].sum()
orders = filtered["Order_ID"].nunique()
units = filtered["Quantity"].sum()

average_order_value = (
    revenue / orders if orders > 0 else 0
)

estimated_profit = filtered["Estimated_Profit"].sum()

profit_margin = (
    estimated_profit / revenue * 100
    if revenue > 0 else 0
)

c1, c2, c3 = st.columns(3)

c1.metric("Total Revenue", f"₹{revenue:,.0f}")
c2.metric("Total Orders", f"{orders:,}")
c3.metric("Units Sold", f"{units:,}")

c4, c5, c6 = st.columns(3)

c4.metric(
    "Avg. Revenue / Order",
    f"₹{average_order_value:,.2f}"
)

c5.metric(
    "Estimated Profit",
    f"₹{estimated_profit:,.0f}"
)

c6.metric(
    "Estimated Profit Margin",
    f"{profit_margin:.2f}%"
)

st.caption(
    "Profit and profit margin are estimates based on assumed "
    "product costs, not verified business costs."
)

st.divider()

# --------------------------------------------------
# SALES VS MONTHLY TARGET
# --------------------------------------------------

st.subheader("🎯 Sales vs Monthly Target")

# Add the monthly target to each sales record
sales_with_targets = filtered.merge(
    targets,
    on="Product",
    how="left"
)

# Create a month column
sales_with_targets["Month"] = (
    sales_with_targets["Order_Date"]
    .dt.to_period("M")
    .astype(str)
)

# Calculate actual revenue for each product and month
monthly_sales = (
    sales_with_targets
    .groupby(["Month", "Product"], as_index=False)
    .agg(
        Actual_Revenue=("Revenue", "sum"),
        Monthly_Target=("Monthly_Target", "first")
    )
)


# Adjust monthly targets for the selected date range
monthly_sales["Month_Start"] = pd.to_datetime(
    monthly_sales["Month"] + "-01"
)

monthly_sales["Month_End"] = (
    monthly_sales["Month_Start"]
    + pd.offsets.MonthEnd(0)
)

# Count the days of each month included in the filter
monthly_sales["Selected_Days"] = (
    (
        monthly_sales["Month_End"].dt.date
        .where(monthly_sales["Month_End"].dt.date < end_date, end_date)
    )
    .apply(lambda d: (d - start_date).days + 1)
)

monthly_sales["Selected_Days"] = monthly_sales.apply(
    lambda row: max(
        0,
        (
            min(row["Month_End"].date(), end_date)
            - max(row["Month_Start"].date(), start_date)
        ).days + 1
    ),
    axis=1
)

monthly_sales["Days_In_Month"] = (
    monthly_sales["Month_End"].dt.days_in_month
)

# Pro-rate the target for partial months
monthly_sales["Monthly_Target"] = (
    monthly_sales["Monthly_Target"]
    * monthly_sales["Selected_Days"]
    / monthly_sales["Days_In_Month"]
)

# Calculate target achievement
monthly_sales["Achievement_Percentage"] = (
    monthly_sales["Actual_Revenue"]
    / monthly_sales["Monthly_Target"].replace(0, float("nan"))
) * 100

monthly_sales["Target_Gap"] = (
    monthly_sales["Actual_Revenue"]
    - monthly_sales["Monthly_Target"]
)


monthly_sales["Target_Gap"] = (
    monthly_sales["Actual_Revenue"]
    - monthly_sales["Monthly_Target"]
)

# Display overall results for the selected filters
total_actual = monthly_sales["Actual_Revenue"].sum()
total_target = monthly_sales["Monthly_Target"].sum()

achievement = (
    total_actual / total_target * 100
    if total_target > 0 else 0
)

target_col1, target_col2, target_col3 = st.columns(3)

target_col1.metric(
    "Actual Revenue",
    f"₹{total_actual:,.0f}"
)

target_col2.metric(
    "Total Monthly Target",
    f"₹{total_target:,.0f}"
)

target_col3.metric(
    "Target Achievement",
    f"{achievement:.1f}%"
)

# Display product-level comparison
st.markdown("#### Product-wise Target Performance")

st.dataframe(
    monthly_sales[
        [
            "Month",
            "Product",
            "Actual_Revenue",
            "Monthly_Target",
            "Achievement_Percentage",
            "Target_Gap"
        ]
    ].rename(
        columns={
            "Month": "Month",
            "Product": "Product",
            "Actual_Revenue": "Actual Revenue (₹)",
            "Monthly_Target": "Monthly Target (₹)",
            "Achievement_Percentage": "Achievement (%)",
            "Target_Gap": "Difference (₹)"
        }
    ).round(2),
    width="stretch"
)

# Visual comparison: actual revenue vs target

st.markdown("#### Actual Revenue vs Target by Product")

product_comparison = (
    monthly_sales
    .groupby("Product", as_index=False)
    .agg(
        Actual_Revenue=("Actual_Revenue", "sum"),
        Target_Revenue=("Monthly_Target", "sum")
    )
)

chart_data = product_comparison.set_index("Product")[
    ["Actual_Revenue", "Target_Revenue"]
]

st.bar_chart(chart_data)

# Monthly target achievement trend

st.markdown("#### Monthly Target Achievement Trend")

monthly_performance = (
    monthly_sales
    .groupby("Month", as_index=False)
    .agg(
        Actual_Revenue=("Actual_Revenue", "sum"),
        Target_Revenue=("Monthly_Target", "sum")
    )
)

monthly_performance["Achievement_Percentage"] = (
    monthly_performance["Actual_Revenue"]
    / monthly_performance["Target_Revenue"].replace(
        0, float("nan")
    )
) * 100

trend_chart = monthly_performance.set_index("Month")[
    ["Achievement_Percentage"]
]

st.line_chart(trend_chart)

st.caption(
    "100% means the sales target was achieved. "
    "Above 100% means sales exceeded the target."
)

# --------------------------------------------------
# 7. HANDLE EMPTY FILTER RESULTS
# --------------------------------------------------

if filtered.empty:
    st.warning(
        "No sales records match your selected filters. "
        "Change the date range, region, or product."
    )
    st.stop()


# --------------------------------------------------
# 8. REVENUE BY PRODUCT
# --------------------------------------------------

st.subheader("Revenue by Product")

revenue_by_product = (
    filtered.groupby("Product")["Revenue"]
    .sum()
    .sort_values()
)

fig, ax = plt.subplots()

revenue_by_product.plot(
    kind="barh",
    ax=ax
)

ax.set_xlabel("Revenue (₹)")
ax.set_ylabel("Product")
fig.tight_layout()

st.pyplot(fig)
plt.close(fig)


# --------------------------------------------------
# 9. REVENUE BY REGION
# --------------------------------------------------

st.subheader("Revenue by Region")

revenue_by_region = (
    filtered.groupby("Region")["Revenue"]
    .sum()
    .sort_values(ascending=False)
)

fig, ax = plt.subplots()

revenue_by_region.plot(
    kind="bar",
    ax=ax
)

ax.set_ylabel("Revenue (₹)")
ax.set_xlabel("Region")
fig.tight_layout()

st.pyplot(fig)
plt.close(fig)


# --------------------------------------------------
# 10. REVENUE BY CATEGORY
# --------------------------------------------------

st.subheader("Revenue by Category")

category_revenue = (
    filtered.groupby("Category")["Revenue"]
    .sum()
    .sort_values(ascending=False)
)

col1, col2 = st.columns(2)

with col1:
    st.dataframe(
        category_revenue.rename("Revenue (₹)"),
        width="stretch"
    )

with col2:
    fig, ax = plt.subplots()

    category_revenue.plot(
        kind="pie",
        autopct="%1.1f%%",
        startangle=90,
        ax=ax
    )

    ax.set_ylabel("")
    fig.tight_layout()

    st.pyplot(fig)
    plt.close(fig)


# --------------------------------------------------
# 11. MONTHLY REVENUE TREND
# --------------------------------------------------

st.subheader("Monthly Revenue Trend")

filtered["Month"] = (
    filtered["Order_Date"]
    .dt.to_period("M")
    .astype(str)
)

monthly_revenue = (
    filtered.groupby("Month")["Revenue"]
    .sum()
    .sort_index()
)

fig, ax = plt.subplots()

monthly_revenue.plot(
    kind="line",
    marker="o",
    ax=ax
)

ax.set_xlabel("Month")
ax.set_ylabel("Revenue (₹)")
ax.grid(True)
fig.tight_layout()

st.pyplot(fig)
plt.close(fig)


# --------------------------------------------------
# 12. ESTIMATED PROFIT BY PRODUCT
# --------------------------------------------------

st.subheader("Estimated Profit by Product")

profit_by_product = (
    filtered.groupby("Product")["Estimated_Profit"]
    .sum()
    .sort_values()
)

fig, ax = plt.subplots()

profit_by_product.plot(
    kind="barh",
    ax=ax
)

ax.set_xlabel("Estimated Profit (₹)")
ax.set_ylabel("Product")
fig.tight_layout()

st.pyplot(fig)
plt.close(fig)


# --------------------------------------------------
# 13. BUSINESS INSIGHTS
# --------------------------------------------------

st.subheader("Business Insights")

product_revenue = filtered.groupby("Product")["Revenue"].sum()
region_revenue = filtered.groupby("Region")["Revenue"].sum()

best_product = product_revenue.idxmax()
best_region = region_revenue.idxmax()

col1, col2 = st.columns(2)

with col1:
    st.success(
        f"Top Product: {best_product} "
        f"(₹{product_revenue[best_product]:,.0f} revenue)"
    )

with col2:
    st.success(
        f"Top Region: {best_region} "
        f"(₹{region_revenue[best_region]:,.0f} revenue)"
    )

if len(monthly_revenue) >= 2:
    previous_month = monthly_revenue.iloc[-2]
    latest_month = monthly_revenue.iloc[-1]

    if previous_month != 0:
        growth = (
            (latest_month - previous_month)
            / previous_month
        ) * 100

        st.metric(
            "Latest Month Revenue Growth",
            f"{growth:.2f}%",
            delta=f"{growth:.2f}%"
        )
    else:
        st.info(
            "The previous month's revenue was zero, "
            "so growth cannot be calculated."
        )
else:
    st.info(
        "More than one month of data is needed "
        "to calculate monthly revenue growth."
    )

# Target performance insights

st.markdown("#### 🎯 Target Performance Insights")

if not monthly_sales.empty:
    product_performance = (
        monthly_sales
        .groupby("Product")
        .agg(
            Actual_Revenue=("Actual_Revenue", "sum"),
            Target_Revenue=("Monthly_Target", "sum")
        )
    )

    product_performance["Achievement"] = (
        product_performance["Actual_Revenue"]
        / product_performance["Target_Revenue"].replace(
            0, float("nan")
        )
    ) * 100

    valid_performance = product_performance.dropna(
        subset=["Achievement"]
    )

    if not valid_performance.empty:
        best_target_product = valid_performance["Achievement"].idxmax()
        lowest_target_product = valid_performance["Achievement"].idxmin()

        col1, col2 = st.columns(2)

        with col1:
            st.success(
                f"Best Target Performance: {best_target_product} "
                f"({valid_performance.loc[best_target_product, 'Achievement']:.1f}%)"
            )

        with col2:
            st.warning(
                f"Lowest Target Performance: {lowest_target_product} "
                f"({valid_performance.loc[lowest_target_product, 'Achievement']:.1f}%)"
            )

        below_target = valid_performance[
            valid_performance["Achievement"] < 100
        ]

        if not below_target.empty:
            st.info(
                "Products below target: "
                + ", ".join(below_target.index.tolist())
            )
        else:
            st.success("All products have met or exceeded their targets!")
    else:
        st.info("Target achievement cannot be calculated because targets are zero or invalid.")


# --------------------------------------------------
# 14. SALES DATA TABLE
# --------------------------------------------------

st.subheader("Sales Data")

st.dataframe(
    filtered.drop(columns=["Month"], errors="ignore"),
    width="stretch"
)

# --------------------------------------------------
# 15. DOWNLOAD COMPLETE REPORTS
# --------------------------------------------------

st.subheader("Download Reports")

# Prepare the filtered sales report
sales_report = filtered.drop(
    columns=["Month"], errors="ignore"
).copy()

# Prepare the target performance report
target_report = monthly_sales[
    [
        "Month",
        "Product",
        "Actual_Revenue",
        "Monthly_Target",
        "Achievement_Percentage",
        "Target_Gap"
    ]
].copy()

target_report = target_report.rename(
    columns={
        "Actual_Revenue": "Actual Revenue (INR)",
        "Monthly_Target": "Adjusted Target (INR)",
        "Achievement_Percentage": "Achievement (%)",
        "Target_Gap": "Revenue Difference (INR)"
    }
)

# Round values for readability
numeric_columns = [
    "Actual Revenue (INR)",
    "Adjusted Target (INR)",
    "Achievement (%)",
    "Revenue Difference (INR)"
]

target_report[numeric_columns] = (
    target_report[numeric_columns].round(2)
)

# CSV download: target performance
target_csv = target_report.to_csv(
    index=False
).encode("utf-8-sig")

st.download_button(
    label="Download Target Performance CSV",
    data=target_csv,
    file_name="target_performance_report.csv",
    mime="text/csv"
)

# Excel download: sales + target performance
excel_buffer = io.BytesIO()

with pd.ExcelWriter(
    excel_buffer,
    engine="openpyxl"
) as writer:
    sales_report.to_excel(
        writer,
        sheet_name="Sales Data",
        index=False
    )

    target_report.to_excel(
        writer,
        sheet_name="Target Performance",
        index=False
    )

st.download_button(
    label="Download Complete Excel Report",
    data=excel_buffer.getvalue(),
    file_name="business_analytics_report.xlsx",
    mime=(
        "application/vnd.openxmlformats-officedocument."
        "spreadsheetml.sheet"
    )
)

st.caption(
    "The Excel workbook includes filtered sales data and "
    "product-wise target performance for the selected period."
)
