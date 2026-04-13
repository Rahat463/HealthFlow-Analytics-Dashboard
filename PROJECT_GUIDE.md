# HealthFlow Analytics Dashboard — Complete Project Guide

## What Is This Project?

This is an **end-to-end healthcare documentation analytics platform** built to demonstrate skills in SQL, Python, Excel, Power BI, and data visualization — themed around the medical scribe industry's core workflow.

**The story you tell in your video:**
> "I built HealthFlow Analytics Dashboard — a complete data analytics pipeline that takes real healthcare encounter data, cleans it, runs complex SQL and Python analytics, performs statistical hypothesis tests, and produces interactive dashboards in both Excel and a live web app, plus exports a Power BI-ready star schema."

---

## Healthcare Documentation Domain

The medical scribe industry uses **ambient AI and human scribes** to convert doctor-patient conversations into structured medical notes in the EHR (Electronic Health Record).

**Key metrics tracked daily in this domain:**
| Metric | What It Means |
|--------|---------------|
| **TAT** (Turnaround Time) | How many minutes it takes to complete a medical note after the encounter |
| **NQS** (Note Quality Score) | 0.00 to 1.00 — how accurate and complete the note is |
| **Completion Rate** | % of notes that reach "Completed" status |
| **Scribe Productivity** | How many notes a scribe handles per day |
| **SLA Compliance** | % of notes delivered within the target time for that specialty |

This project simulates exactly these metrics using real healthcare encounter data.

---

## Data Source: Where Does the Data Come From?

### Synthea (Real Healthcare Data)
We use **Synthea** — a widely-used open-source synthetic patient generator maintained by MITRE Corporation. It produces realistic (but fake — no HIPAA concerns) patient records that mirror real US healthcare data.

**Downloaded from:** `https://synthetichealth.github.io/synthea-sample-data/`

**What Synthea gives us:**
- 8,316 healthcare encounters (doctor visits)
- 117 patients with demographics (name, DOB, gender, address, insurance)
- 274 providers (doctors)
- 4,023 medical conditions with real SNOMED-CT codes
- 5,860 medication prescriptions

### HealthFlow Layer (Synthetic Addition)
On top of the real Synthea data, we add documentation-specific columns that don't exist in Synthea:
- **Turnaround time (TAT)** — generated based on specialty (Cardiology takes longer than Family Medicine)
- **Quality scores (NQS)** — generated based on specialty and provider skill
- **Scribe assignments** — 10 synthetic scribes with varying experience
- **Quality audit log** — 150 QA review records (simulating a real-world QA workflow)
- **ICD-10 diagnosis codes** — mapped from Synthea's SNOMED codes to standard ICD-10
- **Controlled data quality issues** — intentional messiness for the cleaning step to fix

---

## Project Structure — File by File

```
project/
├── run_all.py                              ← Run this ONE file to generate everything
├── requirements.txt                        ← Python packages needed
│
├── 01_data_generation/
│   └── generate_dataset.py                 ← Step 1: Load Synthea + add HealthFlow layer
│
├── 02_sql_analytics/
│   ├── schema.sql                          ← Database table definitions (8 tables)
│   ├── kpi_queries.sql                     ← 10 complex SQL queries
│   └── load_to_sqlite.py                   ← Load data into SQLite + execute queries
│
├── 03_python_pipeline/
│   ├── data_cleaning.py                    ← Step 2: Clean the messy raw data
│   ├── kpi_engine.py                       ← Step 3: Compute KPIs in pandas
│   └── statistical_analysis.py             ← Step 4: Hypothesis tests
│
├── 04_excel_dashboard/
│   └── build_dashboard.py                  ← Step 5: Generate polished Excel workbook
│
├── 05_powerbi_prep/
│   ├── export_star_schema.py               ← Step 6: Export dimensional model for Power BI
│   └── dax_measures.md                     ← 15 DAX formulas ready to use
│
├── 06_web_dashboard/
│   └── app.py                              ← Step 7: Interactive Streamlit web dashboard
│
├── synthea_raw/                            ← Downloaded Synthea CSV files (raw source)
│
└── output/                                 ← ALL generated artifacts land here
    ├── raw_*.csv                           ← Raw data with intentional messiness
    ├── cleaned_encounters.csv              ← Cleaned data (after Step 2)
    ├── cleaning_report.csv                 ← Log of what was cleaned
    ├── kpi_*.csv                           ← Computed KPI tables
    ├── statistical_findings.csv            ← Results of hypothesis tests
    ├── HealthFlow_Dashboard.xlsx            ← The Excel dashboard (5 sheets)
    ├── healthflow.db                        ← SQLite database (for live SQL demos)
    └── powerbi/                            ← Star schema CSVs for Power BI
        ├── dim_dates.csv
        ├── dim_providers.csv
        ├── dim_patients.csv
        ├── dim_diagnoses.csv
        ├── dim_scribes.csv
        ├── fact_encounters.csv
        └── fact_scribe_activity.csv
```

---

## Step-by-Step: What Each Component Does

---

### STEP 1: Data Generation (`01_data_generation/generate_dataset.py`)

**What it does:** Loads real Synthea healthcare data and adds documentation-specific columns on top.

**Detailed breakdown:**

1. **Loads Synthea CSVs** from `synthea_raw/` folder (encounters, patients, providers, conditions, medications)

2. **Builds patients table (117 patients):**
   - Takes real patient names, DOB, gender, city, state, zip from Synthea
   - Assigns insurance types randomly with realistic distribution: 50% Private, 25% Medicare, 18% Medicaid, 7% Uninsured
   - Maps Synthea UUIDs to simple integer IDs (1, 2, 3...)

3. **Builds providers table (top 20 doctors):**
   - Picks the 20 most active doctors from Synthea (by encounter count)
   - Assigns diverse specialties: 4 General Practice, 3 Internal Medicine, 3 Cardiology, 2 Orthopedics, 2 Neurology, 2 Dermatology, 2 Pediatrics, 2 Obstetrics
   - Maps each to a department (e.g., Cardiology → "Heart Center")

4. **Builds scribes table (10 scribes):**
   - 10 scribes with diverse names
   - Each has experience_months (1-36) and shift (Morning/Afternoon/Evening)
   - More experienced scribes will produce higher quality scores later

5. **Builds encounters table (1,500 encounters):**
   - Takes the 1,500 most recent encounters from Synthea
   - For each encounter, generates:
     - **TAT**: Based on specialty (Cardiology mean=55min, Dermatology mean=30min, etc.) using normal distribution
     - **Quality score**: Based on specialty (Dermatology mean=0.90, Neurology mean=0.83, etc.)
     - **Encounter type**: "In-Person" or "Telehealth" with telehealth ratio growing over time (simulates adoption trend)
     - **ICD-10 code**: Mapped from Synthea's condition descriptions (e.g., "Hypertension" → I10)
     - **Notes status**: 67% Completed, 17% Reviewed, 8% Draft, 8% Pending

6. **Builds scribe activity (1,176 records):**
   - One record per completed/reviewed encounter
   - Scribes assigned round-robin within shifts
   - More experienced scribes → fewer edits, slightly higher quality

7. **Builds quality audit log (150 records):**
   - 150 randomly selected encounters get "audited"
   - 60% of audits find issues (score revised downward)
   - 40% confirm or slightly improve the score
   - Each audit has a finding category: "Missing HPI Details", "Incomplete ROS", "Wrong ICD Code", etc.

8. **Injects controlled messiness:**
   - ~3% of quality scores set to NULL (45 rows)
   - ~2% of TAT values set to NULL (29 rows)
   - ~1% of encounter_type changed to lowercase (15 rows: "in-person" instead of "In-Person")
   - 5 near-duplicate rows added (same patient+provider+date)
   - 3 impossible TAT values added (negative and >300 minutes)

**Output:** 8 CSV files in `output/` (raw_encounters.csv, raw_patients.csv, etc.)

---

### STEP 2: Data Cleaning (`03_python_pipeline/data_cleaning.py`)

**What it does:** Takes the messy raw data and systematically cleans it, logging every change.

**The 6 cleaning steps:**

| Step | What It Fixes | How | Rows Affected |
|------|--------------|-----|---------------|
| 1. Fix casing | "in-person" → "In-Person" | `str.strip().str.title()` | ~15 rows |
| 2. Remove duplicates | Same patient+provider+date | `drop_duplicates(subset=[...], keep='first')` | ~85 rows removed |
| 3. Remove impossible values | TAT < 0 or > 300 | Set to NaN | 3 rows |
| 4. Fill quality nulls | Missing quality scores | Fill with **provider-level median** using `groupby('provider_id').transform('median')` | ~45 rows |
| 5. Fill TAT nulls | Missing TAT values | Fill with **specialty-level median** (merge with providers first) | ~30 rows |
| 6. Add derived columns | Need month, day_of_week, etc. | `dt.to_period('M')`, `dt.day_name()`, `dt.dayofweek >= 5` | All rows |

**Why this matters:**
- Shows you can handle real-world dirty data
- The imputation strategy (provider median, then specialty median) is a real data engineering technique
- Referential integrity check catches orphaned foreign keys

**Output:** `cleaned_encounters.csv` (1,420 clean rows) + `cleaning_report.csv`

---

### STEP 3: KPI Computation (`03_python_pipeline/kpi_engine.py`)

**What it does:** Computes all the Key Performance Indicators in pandas, mirroring what the SQL queries do.

**8 KPI computations:**

#### 1. Monthly KPIs (`compute_monthly_kpis`)
Groups encounters by month and calculates:
- Total encounters, avg TAT, avg quality, completion rate, telehealth %, unique patients/providers
- Month-over-month growth using `.pct_change()`

#### 2. Provider Scorecard (`compute_provider_scorecard`)
For each of 18 providers:
- Merges encounters with providers table
- Calculates composite score: `0.4 × quality + 0.3 × (1 - TAT/120) + 0.3 × completion_rate`
- Ranks within specialty using `.rank(ascending=False)`

#### 3. Scribe Leaderboard (`compute_scribe_leaderboard`)
For each of 10 scribes:
- Notes completed, notes per day, avg quality, avg edits
- Quintile ranking using `pd.qcut()`
- Labels: "Top Performer", "On Track", "Needs Training"

#### 4. Specialty Pivot (`compute_specialty_pivot`)
Uses `pd.pivot_table()` to create: rows = specialty, columns = months, values = encounter count

#### 5. SLA Analysis (`compute_sla_analysis`)
- Each specialty has a TAT target (e.g., Cardiology = 60 min, Dermatology = 35 min)
- Calculates % of notes delivered within target per provider
- Compares each provider to their department average using `.transform('mean')`

#### 6. Daily Trends (`compute_daily_trends`)
- Daily encounter count, avg quality, avg TAT
- 7-day rolling averages using `.rolling(7)`
- Anomaly flags when quality drops >15% below rolling avg

#### 7. Telehealth Trends (`compute_telehealth_trends`)
- Monthly telehealth % by specialty
- 3-month moving average per specialty

#### 8. Diagnosis Distribution (`compute_diagnosis_distribution`)
- Top diagnoses by volume with category breakdown (Chronic/Acute/Preventive)

**Output:** `kpi_monthly.csv`, `kpi_provider_scorecard.csv`, `kpi_scribe_leaderboard.csv`, `kpi_daily_trends.csv`

---

### STEP 4: Statistical Analysis (`03_python_pipeline/statistical_analysis.py`)

**What it does:** Runs 4 formal statistical tests on the data.

#### Test 1: Telehealth vs In-Person Quality (Two-Sample t-test)
- **Question:** Is documentation quality different for telehealth vs in-person visits?
- **Method:** Welch's t-test (scipy.stats.ttest_ind)
- **Result:** p=0.05, Cohen's d=0.16 — marginally significant but negligible effect size
- **Interpretation:** Telehealth quality is statistically similar to in-person

#### Test 2: TAT Anomaly Detection (Z-score)
- **Question:** Which encounters have abnormally high turnaround times?
- **Method:** Calculate Z-score per provider, flag |z| > 2
- **Result:** 62 anomalies (4.4%) across all specialties
- **Also runs:** IQR method for comparison (only 2 anomalies — Z-score is more sensitive)

#### Test 3: Quality Trend Regression (Linear Regression)
- **Question:** Is overall quality improving or declining over time?
- **Method:** numpy polyfit (degree 1) + manual t-test on slope
- **Result:** slope = -0.00005/month, R² = 0.003, p = 0.67 — NO significant trend
- **Interpretation:** Quality is stable over time

#### Test 4: Scribe Experience vs Quality (Pearson Correlation)
- **Question:** Do more experienced scribes produce higher quality notes?
- **Method:** scipy.stats.pearsonr
- **Result:** r = 0.73, p = 0.02 — STRONG positive correlation
- **Interpretation:** Experience significantly improves quality — supports investing in scribe training and retention

**Output:** `statistical_findings.csv`

---

### STEP 5: Excel Dashboard (`04_excel_dashboard/build_dashboard.py`)

**What it does:** Generates a professional 5-sheet Excel workbook using openpyxl.

#### Sheet 1: Executive Summary
- **KPI Scorecards:** 6 large color-coded cards (Total Encounters, Avg Quality, Avg TAT, Completion Rate, Telehealth %, Unique Patients)
- **Monthly trend table:** Last 12 months with conditional formatting
  - Green cells: quality >= 0.88
  - Red cells: quality < 0.85
  - Data bars on encounter count column
- **Chart 1:** Dual-axis — monthly encounter volume (bars) + quality score (line)
- **Chart 2:** Monthly TAT trend line

#### Sheet 2: Provider Performance
- **Scorecard table:** All 18 providers with quality, TAT, completion rate, composite score, rank
- **Conditional formatting:**
  - Green on quality >= 0.9
  - Red on quality < 0.85
  - Red on TAT > 50 minutes
  - Green on rank = 1 (top in specialty)
- **Chart:** Horizontal bar chart of providers ranked by composite score

#### Sheet 3: Scribe Productivity
- **Leaderboard table:** 10 scribes with notes/day, quality, edits, duration
- **Row highlighting:**
  - Green rows for "Top Performer"
  - Red rows for "Needs Training"
- **Chart 1:** Bar chart of quality by scribe
- **Chart 2:** Experience (months) by scribe

#### Sheet 4: Specialty Analysis
- **Pivot table:** Specialty × Month encounter counts (last 6 months)
- **Stacked bar chart:** Monthly encounters by specialty
- **Top diagnoses table:** Top 10 diagnosis codes by volume
- **Pie chart:** Diagnosis category distribution (Chronic/Acute/Preventive)

#### Sheet 5: Trends & Alerts
- **Daily trend table:** Last 60 days with rolling averages
- **Anomaly rows highlighted in red** with bold text
- **Line chart:** Daily quality vs 7-day rolling average
- **Statistical findings table:** All 4 test results with method, metric, and interpretation
- **Significant findings highlighted in green**

**openpyxl techniques demonstrated:**
- `PatternFill` — colored cell backgrounds
- `Font` — bold, size, color
- `Border` — table borders
- `ConditionalFormatting` with `CellIsRule` — green/yellow/red thresholds
- `DataBarRule` — in-cell data bars
- `BarChart`, `LineChart`, `PieChart` — embedded charts
- `merge_cells` — KPI scorecards
- Number formatting — percentages, decimals

**Output:** `HealthFlow_Dashboard.xlsx` (25.9 KB, 5 sheets)

---

### STEP 6: Power BI Prep (`05_powerbi_prep/`)

**What it does:** Exports data as a **star schema** — the standard data modeling pattern for Power BI.

#### What is a Star Schema?
It separates data into:
- **Dimension tables (dim_):** Reference/lookup data that doesn't change often
- **Fact tables (fact_):** Transaction data with measurements and foreign keys

```
              dim_dates
                 |
dim_providers -- fact_encounters -- dim_patients
                 |
              dim_diagnoses

dim_scribes -- fact_scribe_activity
```

#### Dimension Tables:
| Table | Rows | Key Columns |
|-------|------|-------------|
| `dim_dates` | 1,931 | date_key, year, quarter, month_name, day_name, is_weekend |
| `dim_providers` | 20 | provider_id, name, specialty, department |
| `dim_patients` | 117 | patient_id, name, gender, insurance_type, age, age_group |
| `dim_diagnoses` | 31 | icd_code, description, category |
| `dim_scribes` | 10 | scribe_id, name, experience_months, shift, experience_tier |

#### Fact Tables:
| Table | Rows | Key Columns |
|-------|------|-------------|
| `fact_encounters` | 1,420 | encounter_id, date_key, patient_id, provider_id, TAT, quality, sla_met |
| `fact_scribe_activity` | 1,176 | activity_id, encounter_id, scribe_id, date_key, duration, edits, quality |

#### DAX Measures (`dax_measures.md`):
15 ready-to-use Power BI formulas including:
- `Total Encounters = COUNTROWS(fact_encounters)`
- `SLA Compliance % = DIVIDE(CALCULATE(..., sla_met = TRUE()), COUNTROWS(...))`
- `MoM Encounter Growth` using `DATEADD`
- `Provider Quality Rank` using `RANKX`
- `Rolling 7D Quality` using `DATESINPERIOD`

**Output:** 7 CSV files in `output/powerbi/` + `dax_measures.md`

---

### STEP 7: Web Dashboard (`06_web_dashboard/app.py`)

**What it does:** Interactive browser-based dashboard using Streamlit + Plotly.

**How to run:**
```bash
streamlit run project/06_web_dashboard/app.py
```
Then open `http://localhost:8501` in your browser.

#### Sidebar Filters:
- **Specialty dropdown:** Filter by Cardiology, Dermatology, etc.
- **Encounter Type:** All / In-Person / Telehealth
- **Date Range:** Interactive date picker

#### Tab 1: Overview
- 6 KPI metric cards at the top (update when you change filters)
- Dual-axis chart: encounter volume (bars) + quality (line)
- TAT trend line
- Pie charts: encounter type distribution + diagnosis category split

#### Tab 2: Provider Performance
- Horizontal bar chart: providers ranked by composite score, color-coded by specialty
- Specialty summary table
- Detailed scorecard with color gradients (green = good quality, red = high TAT)

#### Tab 3: Scribe Productivity
- Quality bar chart color-coded by performance tier (green/blue/red)
- Scatter plot: experience vs quality (bubble size = notes completed)
- Full leaderboard table

#### Tab 4: Trends & Alerts
- Daily quality with 7-day rolling average (anomalies marked with red X)
- Daily TAT with 7-day rolling average
- Anomaly count summary

#### Tab 5: Statistical Analysis
- Expandable cards for each of 4 statistical tests
- Green badge for significant results, yellow for non-significant
- p-value displayed as a metric
- Scatter plot with manual trendline for experience-quality correlation

---

### SQLite Database (`02_sql_analytics/load_to_sqlite.py`)

**What it does:** Creates a real SQLite database and executes all 10 SQL queries against it.

**Why this matters:** You can demo live SQL execution in your video:
```bash
python project/02_sql_analytics/load_to_sqlite.py
```

This creates `output/healthflow.db` (312 KB) with all 8 tables loaded.

---

## The 10 SQL Queries Explained

All queries are in `02_sql_analytics/kpi_queries.sql`. Each demonstrates different advanced SQL techniques:

### Q1: Executive Summary KPIs
```
Techniques: CTE (WITH clause), conditional aggregation (SUM CASE WHEN), ROUND, COUNT DISTINCT
Business: Monthly dashboard overview for leadership
```

### Q2: Provider Performance Scorecard
```
Techniques: RANK() OVER (PARTITION BY specialty), composite scoring formula, CTE
Business: Rank providers within their specialty by a weighted score
```

### Q3: Month-over-Month Trends with Alerts
```
Techniques: LAG() window function, percentage change calculation, CASE WHEN alert flags
Business: Detect quality drops or TAT spikes early
```

### Q4: Scribe Productivity Leaderboard
```
Techniques: Multi-table JOIN, NTILE(5) for quintile ranking, JULIANDAY for duration
Business: Identify scribes needing training vs top performers
```

### Q5: Specialty x Month Pivot
```
Techniques: Manual pivot using COUNT(CASE WHEN strftime(...) THEN 1 END)
Business: Capacity planning — which specialties need more scribes in which months?
```

### Q6: TAT SLA Compliance by Provider
```
Techniques: CTE with UNION ALL for targets, JOIN, AVG() OVER (PARTITION BY department)
Business: Which providers consistently miss their specialty's TAT target?
```

### Q7: Patient Visit Gap Analysis
```
Techniques: LEAD() OVER (PARTITION BY patient_id), date arithmetic, risk classification
Business: Identify chronic patients who haven't visited in 90+ days (churn risk)
```

### Q8: Rolling 7-Day Quality Anomaly Detection
```
Techniques: Window frame clause (ROWS BETWEEN 6 PRECEDING AND CURRENT ROW), anomaly flagging
Business: Real-time quality monitoring — flag days with unusual quality drops
```

### Q9: Telehealth Adoption Trend by Specialty
```
Techniques: 3 chained CTEs, moving average, LAG for trend detection
Business: Which specialties are adopting telehealth fastest?
```

### Q10: QA Audit Impact Analysis
```
Techniques: JOIN to audit log, GROUP BY with HAVING, correlated subquery, before/after comparison
Business: Which types of quality issues cause the biggest score drops?
```

---

## How to Run Everything

### Option 1: Full Pipeline (generates all artifacts)
```bash
cd ~/healthflow-analytics
source venv/bin/activate
python project/run_all.py
```
This runs all 7 steps in ~2 seconds and generates everything in `output/`.

### Option 2: Web Dashboard (for video demo)
```bash
streamlit run project/06_web_dashboard/app.py
```
Open `http://localhost:8501` in your browser.

### Option 3: Individual Components
```bash
# Just generate data
python project/01_data_generation/generate_dataset.py

# Just clean data
python project/03_python_pipeline/data_cleaning.py

# Just compute KPIs
python project/03_python_pipeline/kpi_engine.py

# Just run statistics
python project/03_python_pipeline/statistical_analysis.py

# Just build Excel dashboard
python project/04_excel_dashboard/build_dashboard.py

# Just export Power BI data
python project/05_powerbi_prep/export_star_schema.py

# Just load SQLite + run SQL queries
python project/02_sql_analytics/load_to_sqlite.py
```

---

## What to Say in Your 5-Minute Video

### Minute 0-1: Introduction + Motivation
- "Hi, I'm Sheikh Rahat Mahmud, final year CSE student at BUET."
- "I'm passionate about AI-powered healthcare documentation and how data analytics can improve it."
- "I built a healthcare analytics project to demonstrate my SQL, Python, and data visualization skills."

### Minute 1-2: Show the Web Dashboard
- Open the Streamlit dashboard in browser
- Walk through the KPI cards, show filtering by specialty
- Show the provider performance tab with the ranking chart
- "I built this interactive dashboard using Streamlit and Plotly"

### Minute 2-3: Highlight SQL + Python Skills
- Show `kpi_queries.sql` — scroll through and highlight:
  - "Here I use window functions like RANK and LAG"
  - "This query detects anomalies using rolling averages"
  - "This pivot query reshapes data by specialty and month"
- "I also wrote the same analytics in pandas — showing I can work in both SQL and Python"

### Minute 3-4: Show Excel Dashboard + Power BI Prep
- Open `HealthFlow_Dashboard.xlsx` in Excel/LibreOffice
- Show the KPI scorecards, conditional formatting, charts
- "I generated this programmatically using openpyxl"
- Show the Power BI star schema CSVs and DAX measures
- "These are ready to import into Power BI with pre-built DAX measures"

### Minute 4-5: Data Pipeline + Statistical Findings
- Run `python project/run_all.py` to show the pipeline
- "The pipeline cleans 1,505 messy records down to 1,420 clean records"
- "My statistical analysis found that scribe experience strongly correlates with quality (r=0.73)"
- "This suggests investing in scribe training and retention — a key operational insight for any medical documentation company"

---

## Technical Skills This Project Demonstrates

| Skill Area | What You Can Point To |
|-----------|----------------------|
| **SQL** | 10 complex queries with CTEs, window functions (RANK, LAG, LEAD, NTILE), pivots, anomaly detection, correlated subqueries |
| **Python** | Full ETL pipeline, pandas (groupby, merge, pivot_table, rolling, transform, qcut), scipy (ttest_ind, pearsonr) |
| **Data Cleaning** | Null imputation (provider/specialty median), duplicate removal, data validation, referential integrity checks |
| **Excel / Office 365** | 5-sheet workbook with charts (bar, line, pie), conditional formatting, KPI scorecards, data bars — all built with openpyxl |
| **Power BI** | Star schema dimensional model, 15 DAX measures, proper fact/dimension table design |
| **Data Visualization** | Interactive Streamlit dashboard with Plotly charts, filtered views, statistical annotations |
| **Statistics** | Hypothesis testing (t-test), anomaly detection (Z-score, IQR), regression analysis, correlation |
| **Healthcare Domain** | Industry-standard metrics (TAT, NQS, scribe productivity), ICD-10 codes, encounter workflows, QA auditing |
