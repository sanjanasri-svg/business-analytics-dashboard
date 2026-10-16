# 📊 Retail Business Analytics Dashboard

An interactive business intelligence dashboard built with Python and Streamlit to analyze retail sales performance, profitability, product targets, and business trends.

🔗 **Live Dashboard:** https://sanjana-sales-analytics.streamlit.app/

## 🎯 Project Overview

This project transforms retail sales data into meaningful business insights through interactive visualizations, key performance indicators (KPIs), and product-level performance analysis.

It demonstrates an end-to-end data analytics workflow, from data preparation and transformation to interactive dashboard development and deployment.

## ✨ Key Features

- **Sales Performance Analysis:** Monitor sales revenue and overall business performance.
- **KPI Dashboard:** View key metrics in one place.
- **Interactive Filters:** Explore data based on available categories, products, regions, and dates.
- **Sales Trend Analysis:** Understand changes in sales performance over time.
- **Profitability Analysis:** Explore estimated profitability using assumed product costs.
- **Product Target Tracking:** Compare product performance against defined sales targets.
- **Business Insights:** Identify trends and performance patterns.
- **Data Export:** Download available analysis results in CSV and Excel formats.
- **Online Deployment:** Access the dashboard through Streamlit Community Cloud.

## 🛠️ Technologies Used

- **Python** — Core programming language
- **Pandas** — Data cleaning, transformation, and analysis
- **NumPy** — Numerical operations
- **Matplotlib & Seaborn** — Data visualization
- **Streamlit** — Interactive dashboard and web application
- **Git & GitHub** — Version control and project hosting
- **Streamlit Community Cloud** — Dashboard deployment

## 📁 Project Structure

```text
business-analytics-dashboard/
├── app.py
├── requirements.txt
├── README.md
├── data/
│   ├── raw/
│   │   ├── sales.csv
│   │   └── product_targets.csv
│   └── processed/
│       └── cleaned_sales.csv
├── notebooks/
└── src/
```

## 🚀 Run Locally

### 1. Clone the repository

```bash
git clone https://github.com/sanjanasri-svg/business-analytics-dashboard.git
cd business-analytics-dashboard
```

### 2. Create a virtual environment

```bash
python -m venv .venv
```

Activate it on Windows PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Launch the dashboard

```bash
python -m streamlit run app.py
```

The application will open in your browser.

**Note:** The required CSV files must be present in the expected `data/` paths for the dashboard to load successfully.

## 📈 Dataset & Assumptions

This project uses demonstration retail sales data. Product sales targets are illustrative values, and profitability calculations use assumed costs rather than verified business expenses.

The dashboard is intended to demonstrate data analytics and business intelligence techniques, not to represent the financial performance of a real company.

## 💡 Learning Outcomes

- Data cleaning and preprocessing
- Exploratory data analysis
- KPI identification and calculation
- Interactive data visualization
- Business performance and trend analysis
- Dashboard development with Streamlit
- GitHub-based project management
- Cloud deployment of a Python application

## 🌟 Future Enhancements

- Add more datasets and advanced business metrics.
- Improve dashboard interactivity and customization.
- Expand analytical insights and reporting capabilities.
- Add further data validation and error handling.

## 👩‍💻 Author

**Sanjanasri M.**

B.Tech — Artificial Intelligence and Data Science

Sri Venkateswara College of Engineering

---

⭐ If you find this project interesting, feel free to explore the repository and try the live dashboard!
