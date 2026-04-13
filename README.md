# HealthFlow Analytics Dashboard

An end-to-end healthcare documentation analytics platform demonstrating SQL, Python, Excel, Power BI, and interactive data visualization skills.

![Python](https://img.shields.io/badge/Python-3.10+-blue?logo=python)
![SQL](https://img.shields.io/badge/SQL-SQLite-green?logo=sqlite)
![Streamlit](https://img.shields.io/badge/Streamlit-Dashboard-red?logo=streamlit)
![Excel](https://img.shields.io/badge/Excel-openpyxl-darkgreen?logo=microsoftexcel)
![Power BI](https://img.shields.io/badge/Power_BI-Star_Schema-yellow?logo=powerbi)

## What This Project Does

Takes real healthcare encounter data (from [Synthea](https://synthetichealth.github.io/synthea/)), runs it through a complete analytics pipeline, and produces:

- **10 complex SQL queries** with CTEs, window functions, anomaly detection
- **Python ETL pipeline** — data cleaning, KPI computation, statistical analysis
- **Professional Excel dashboard** — 5 sheets with charts and conditional formatting
- **Power BI star schema** — 5 dimension + 2 fact tables with DAX measures
- **Interactive web dashboard** — Streamlit + Plotly with filters and 5 analytics tabs
- **SQLite database** — for live SQL query execution

## Quick Start

```bash
# Clone
git clone https://github.com/Rahat463/HealthFlow-Analytics-Dashboard.git
cd HealthFlow-Analytics-Dashboard

# Install dependencies
pip install -r requirements.txt

# Run the full pipeline (generates all output in ~3 seconds)
python run_all.py

# Launch the interactive web dashboard
streamlit run 06_web_dashboard/app.py
```

## Project Structure

```
.
├── run_all.py                      # Master orchestrator (runs everything)
├── requirements.txt                # Dependencies
│
├── 01_data_generation/
│   └── generate_dataset.py         # Load Synthea + add healthcare documentation layer
│
├── 02_sql_analytics/
│   ├── schema.sql                  # 8-table database schema
│   ├── kpi_queries.sql             # 10 production-grade SQL queries
│   └── load_to_sqlite.py           # Load into SQLite + execute queries
│
├── 03_python_pipeline/
│   ├── data_cleaning.py            # ETL: nulls, dupes, outliers, imputation
│   ├── kpi_engine.py               # KPI computation in pandas
│   └── statistical_analysis.py     # t-tests, Z-score anomaly, correlation
│
├── 04_excel_dashboard/
│   └── build_dashboard.py          # 5-sheet Excel workbook (openpyxl)
│
├── 05_powerbi_prep/
│   ├── export_star_schema.py       # Dimensional model export
│   └── dax_measures.md             # 15 DAX measures reference
│
├── 06_web_dashboard/
│   └── app.py                      # Streamlit interactive dashboard
│
└── synthea_raw/                    # Real Synthea patient data (5 CSVs)
```

## Key Analytics

### SQL Highlights (10 Queries)
| # | Query | Techniques |
|---|-------|-----------|
| 1 | Executive Summary KPIs | CTE + conditional aggregation |
| 2 | Provider Scorecard | RANK() OVER PARTITION BY + composite scoring |
| 3 | Month-over-Month Trends | LAG() + growth rate + ALERT flags |
| 4 | Scribe Leaderboard | Multi-JOIN + NTILE quartiles |
| 5 | Specialty x Month Pivot | COUNT CASE WHEN crosstab |
| 6 | SLA Compliance | Window function vs department average |
| 7 | Patient Gap Analysis | LEAD() + risk classification |
| 8 | Rolling 7-Day Anomaly | ROWS BETWEEN frame clause |
| 9 | Telehealth Trends | 3 CTEs + moving average |
| 10 | QA Audit Impact | Correlated subquery + HAVING |

### Statistical Analysis
- **Telehealth vs In-Person quality** — Welch's t-test (p=0.05, Cohen's d=0.16)
- **TAT anomaly detection** — Z-score method (4.4% flagged)
- **Quality trend regression** — Linear fit over time (no significant trend)
- **Scribe experience correlation** — Pearson r=0.73, p=0.02 (strong positive)

### Web Dashboard
5 interactive tabs: Overview, Provider Performance, Scribe Productivity, Trends & Alerts, Statistical Analysis — with sidebar filters for specialty, encounter type, and date range.

## Data Source

[Synthea Synthetic Patient Population](https://synthetichealth.github.io/synthea/) by MITRE Corporation — real-structured open-source healthcare data. We use 5 CSVs (encounters, patients, providers, conditions, medications) and layer documentation-specific metrics on top (turnaround time, quality scores, scribe assignments, audit logs).

## Tech Stack

| Layer | Tools |
|-------|-------|
| Data Generation | Python, NumPy, Pandas, Synthea |
| SQL Analytics | SQLite, Window Functions, CTEs |
| Python Pipeline | Pandas ETL, SciPy Statistics |
| Excel Dashboard | openpyxl (charts, conditional formatting) |
| Power BI | Star Schema, DAX Measures |
| Web Dashboard | Streamlit, Plotly |

## Author

**Sheikh Rahat Mahmud**
- BSc in CSE, Bangladesh University of Engineering & Technology (BUET)
- Email: sheikhrahatm@gmail.com
- LinkedIn: [sheikh-rahat-mahmud](https://www.linkedin.com/in/sheikh-rahat-mahmud/)
- GitHub: [Rahat463](https://github.com/Rahat463)
