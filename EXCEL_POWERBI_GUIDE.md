# Excel & Power BI — Complete Beginner Guide

This guide assumes you have ZERO experience with Excel dashboards and Power BI.
Follow step by step and you'll be able to demo both in your video.

---

# PART 1: MICROSOFT EXCEL

## 1.1 What is Excel (in the context of data analytics)?

Excel is not just a spreadsheet. In data analytics, it's used for:
- **Dashboards** — visual summaries with charts and KPI cards
- **Pivot Tables** — summarize large datasets by grouping/aggregating
- **Conditional Formatting** — color cells based on rules (green = good, red = bad)
- **Charts** — bar, line, pie, scatter plots embedded in sheets
- **Data Analysis** — VLOOKUP, INDEX/MATCH, SUMIFS, etc.

In healthcare data operations, analysts use Excel daily to:
- Build weekly/monthly reports for leadership
- Share data summaries with non-technical stakeholders
- Quick ad-hoc analysis before building a full dashboard

---

## 1.2 Opening Your Dashboard

### On Linux (LibreOffice Calc):
```bash
libreoffice --calc project/output/HealthFlow_Dashboard.xlsx
```

### On Windows:
Double-click `HealthFlow_Dashboard.xlsx` — it opens in Microsoft Excel.

### On Google Sheets (for sharing):
1. Go to https://sheets.google.com
2. Click **Blank spreadsheet**
3. Click **File → Import → Upload**
4. Upload `HealthFlow_Dashboard.xlsx`
5. Choose "Replace spreadsheet"
6. Charts and formatting will mostly transfer

---

## 1.3 Understanding Your 5 Sheets

When you open the file, you'll see **5 tabs at the bottom**:

### Sheet 1: "Executive Summary"
```
┌──────────────────────────────────────────────────────────┐
│              HealthFlow Analytics Dashboard                │  ← Title bar (dark blue)
├──────────────────────────────────────────────────────────┤
│  [1,420]    [0.875]    [38.4]    [66.4%]   [13.0%]  [47]│  ← KPI cards (colored boxes)
│  Encounters  Quality    TAT     Completion  Telehealth Pts│
├──────────────────────────────────────────────────────────┤
│  Month | Encounters | Quality | TAT | Completion | ...   │  ← Monthly trend table
│  2025-07 |    28    | 0.890   | 36.2|   72.1%   | ...   │     (with colored cells)
│  2025-08 |    31    | 0.876   | 38.5|   68.3%   | ...   │
├──────────────────────────────────────────────────────────┤
│  [BAR + LINE CHART: Monthly Volume & Quality]            │  ← Charts below the table
│  [LINE CHART: Monthly TAT Trend]                         │
└──────────────────────────────────────────────────────────┘
```

**What to notice:**
- **KPI cards** at the top: large numbers with colored backgrounds
- **Conditional formatting** on the table:
  - Green cells = quality >= 0.88 (good)
  - Red cells = quality < 0.85 (bad)
  - Blue data bars inside the "Encounters" column (visual bar in each cell)
- **Two charts** below the table

### Sheet 2: "Provider Performance"
- Table of all 18 providers with their scores
- Green highlight on rank = 1 (best in specialty)
- Red highlight on TAT > 50 minutes
- Horizontal bar chart showing ranking

### Sheet 3: "Scribe Productivity"
- 10 scribes ranked by quality
- Entire rows colored:
  - Green rows = "Top Performer"
  - Red rows = "Needs Training"
- Bar charts comparing scribes

### Sheet 4: "Specialty Analysis"
- Pivot table: specialties vs months
- Stacked bar chart
- Pie chart of diagnosis categories (Chronic/Acute/Preventive)

### Sheet 5: "Trends & Alerts"
- Daily quality data with rolling averages
- Anomaly rows highlighted in red
- Line chart: actual vs rolling average
- Statistical findings table at the bottom

---

## 1.4 Key Excel Concepts You Should Know (for the interview)

### Conditional Formatting
**What:** Automatically color cells based on rules.
**Example:** "If quality < 0.85, make the cell red"
**How we did it in code:**
```python
ws.conditional_formatting.add("C10:C22", CellIsRule(
    operator="lessThan", formula=["0.85"],
    fill=PatternFill(start_color="FADBD8", fill_type="solid")
))
```
**What to say:** "I used conditional formatting to highlight quality scores below 0.85 in red, making it easy for stakeholders to spot problems at a glance."

### Data Bars
**What:** Tiny bar charts inside cells — the bar length represents the value.
**Where:** The "Encounters" column in Sheet 1 has blue bars.
**What to say:** "I added data bars to the encounter count column so you can visually compare months without looking at numbers."

### Pivot Tables
**What:** A way to summarize data by grouping rows and columns.
**Where:** Sheet 4 — Specialty × Month grid.
**What to say:** "This pivot table shows encounter volume by specialty per month — useful for capacity planning."

### Charts
**What:** Visual representations of data embedded in the sheet.
**Types we used:**
| Chart Type | Where | What It Shows |
|-----------|-------|---------------|
| Bar Chart | Sheet 1, 2, 3 | Compare values across categories |
| Line Chart | Sheet 1, 5 | Show trends over time |
| Pie Chart | Sheet 4 | Show proportions (Chronic/Acute/Preventive) |
| Dual-Axis | Sheet 1 | Two different metrics on the same chart |

### VLOOKUP (know this for the interview)
**What:** Looks up a value in one table and returns a matching value from another.
**Syntax:** `=VLOOKUP(lookup_value, table_array, col_index, FALSE)`
**Example:** Find a provider's specialty given their ID:
```
=VLOOKUP(101, providers_table, 3, FALSE)  → "Cardiology"
```
We didn't use VLOOKUP in this project (we used Python merges instead), but you should know what it is.

### Other Excel Functions to Know:
| Function | What It Does | Example |
|----------|-------------|---------|
| `SUMIF` | Sum values where condition is met | `=SUMIF(B:B, "Cardiology", D:D)` |
| `COUNTIF` | Count rows where condition is met | `=COUNTIF(C:C, ">0.9")` |
| `AVERAGEIF` | Average where condition is met | `=AVERAGEIF(B:B, "Telehealth", E:E)` |
| `INDEX/MATCH` | More flexible VLOOKUP | `=INDEX(C:C, MATCH(101, A:A, 0))` |
| `IF` | Conditional logic | `=IF(C2>0.9, "Good", "Needs Work")` |
| `TEXT` | Format dates/numbers | `=TEXT(A2, "YYYY-MM")` |

---

## 1.5 How to Talk About Excel in Your Video

**Good things to say:**
- "I built this dashboard programmatically using Python's openpyxl library — so it can be regenerated automatically whenever new data arrives."
- "I used conditional formatting to create a traffic-light system — green for good metrics, red for concerning ones."
- "The dual-axis chart on Sheet 1 shows both volume and quality on the same view, so leadership can see if quality drops when volume increases."
- "This pivot table breaks down encounters by specialty per month — it answers the question: which specialties need more scribe support?"

**If asked "Can you do this in Excel manually?"**
Say: "Yes — I can also build pivot tables, charts, and conditional formatting directly in Excel. I chose to generate this programmatically because it makes the dashboard reproducible and automated."

---

# PART 2: POWER BI

## 2.1 What is Power BI?

Power BI is Microsoft's business intelligence tool. It's like Excel dashboards on steroids:
- **Interactive** — click a bar in a chart to filter everything else
- **Connects to databases** — SQL Server, PostgreSQL, CSV files, APIs
- **DAX formulas** — like Excel formulas but for aggregating across related tables
- **Star Schema** — the standard way to organize data in Power BI
- **Published dashboards** — share with your team via web browser

In healthcare analytics teams, Power BI is used for:
- Real-time operational dashboards
- Provider performance tracking
- Quality metrics monitoring
- Executive reporting

---

## 2.2 Installing Power BI

### Option A: Power BI Desktop (Windows only — FREE)
1. Go to https://powerbi.microsoft.com/desktop/
2. Download and install "Power BI Desktop"
3. It's completely free — no license needed for desktop use

### Option B: Power BI in Browser (needs Microsoft account)
1. Go to https://app.powerbi.com
2. Sign in with a Microsoft account
3. Limited features but works on Linux/Mac

### Option C: If you're on Linux (your case)
Power BI Desktop doesn't run on Linux. Your options:
- **Use a Windows VM** or a friend's Windows laptop to demo
- **Use the browser version** at app.powerbi.com
- **Just show the star schema CSVs and DAX measures** in your video and explain what you would build — this is still impressive

---

## 2.3 How the Star Schema Works

Our data is organized as a **star schema** — this is THE standard for Power BI:

```
                    dim_dates
                       │
                       │ date_key
                       │
dim_providers ────── fact_encounters ────── dim_patients
  provider_id          │                     patient_id
                       │ diagnosis_code
                       │
                    dim_diagnoses


dim_scribes ────── fact_scribe_activity
  scribe_id            │ encounter_id
                       │
                    fact_encounters
```

**Why star schema?**
- **Fact tables** (center) hold measurements: encounter counts, quality scores, TAT
- **Dimension tables** (points of the star) hold descriptive attributes: provider name, patient age, date details
- Power BI can efficiently aggregate facts by slicing through any dimension
- Example: "Show me average quality BY specialty BY month" = fact_encounters sliced by dim_providers.specialty and dim_dates.month_name

---

## 2.4 Step-by-Step: Building a Power BI Dashboard

If you have access to Power BI Desktop (Windows), follow these exact steps:

### Step 1: Import the Data
1. Open Power BI Desktop
2. Click **"Get Data"** (top-left button)
3. Select **"Text/CSV"**
4. Navigate to `project/output/powerbi/`
5. Import these files ONE BY ONE:
   - `dim_dates.csv`
   - `dim_providers.csv`
   - `dim_patients.csv`
   - `dim_diagnoses.csv`
   - `dim_scribes.csv`
   - `fact_encounters.csv`
   - `fact_scribe_activity.csv`
6. For each file: Click **"Load"** (not "Transform" — our data is already clean)

### Step 2: Create Relationships (Model View)
1. Click the **"Model"** icon on the left sidebar (looks like 3 connected boxes)
2. You'll see all 7 tables. Drag to create relationships:

| From (drag) | To (drop) | On Column |
|------------|-----------|-----------|
| `fact_encounters.date_key` | `dim_dates.date_key` | date_key |
| `fact_encounters.provider_id` | `dim_providers.provider_id` | provider_id |
| `fact_encounters.patient_id` | `dim_patients.patient_id` | patient_id |
| `fact_encounters.diagnosis_code` | `dim_diagnoses.icd_code` | diagnosis_code → icd_code |
| `fact_scribe_activity.scribe_id` | `dim_scribes.scribe_id` | scribe_id |
| `fact_scribe_activity.encounter_id` | `fact_encounters.encounter_id` | encounter_id |

3. For each relationship: make sure **Cardinality** is "Many to one" (fact → dimension)

### Step 3: Create DAX Measures
1. Click on `fact_encounters` in the Fields pane (right side)
2. Click **"New Measure"** in the top ribbon
3. Type each measure from `dax_measures.md`:

**Measure 1:**
```
Total Encounters = COUNTROWS(fact_encounters)
```

**Measure 2:**
```
Avg Quality Score = AVERAGE(fact_encounters[note_quality_score])
```

**Measure 3:**
```
Avg TAT = AVERAGE(fact_encounters[note_turnaround_minutes])
```

**Measure 4:**
```
SLA Compliance % = DIVIDE(
    CALCULATE(COUNTROWS(fact_encounters), fact_encounters[sla_met] = TRUE()),
    COUNTROWS(fact_encounters),
    0
)
```

**Measure 5:**
```
Telehealth % = DIVIDE(
    CALCULATE(COUNTROWS(fact_encounters), fact_encounters[encounter_type] = "Telehealth"),
    COUNTROWS(fact_encounters),
    0
)
```

(Add more from `dax_measures.md` as needed)

### Step 4: Build Visuals (Report View)
1. Click the **"Report"** icon (left sidebar, looks like a chart)
2. You now have a blank canvas. Build these visuals:

#### Visual 1: KPI Cards (top row)
1. Click **"Card"** visual from Visualizations pane
2. Drag `Total Encounters` measure to the "Fields" area
3. Resize and position at top-left
4. Repeat for: Avg Quality Score, Avg TAT, SLA Compliance %, Telehealth %
5. Format each: click the card → Format → set font size to 24, add title

#### Visual 2: Monthly Encounter Bar Chart
1. Click **"Clustered bar chart"** from Visualizations
2. Drag `dim_dates.month_name` to **X-axis**
3. Drag `Total Encounters` to **Y-axis**
4. Resize to fill middle area

#### Visual 3: Quality Line Chart
1. Click **"Line chart"**
2. X-axis: `dim_dates.month_name`
3. Y-axis: `Avg Quality Score`
4. Place next to the bar chart

#### Visual 4: Provider Performance Table
1. Click **"Table"** visual
2. Add columns: `dim_providers.name`, `dim_providers.specialty`, `Total Encounters`, `Avg Quality Score`, `Avg TAT`
3. Click **Format → Conditional formatting** on Quality column → Background color → Rules → Green above 0.9, Red below 0.85

#### Visual 5: Specialty Donut Chart
1. Click **"Donut chart"**
2. Legend: `dim_providers.specialty`
3. Values: `Total Encounters`

#### Visual 6: Slicer (Filter)
1. Click **"Slicer"** visual
2. Drag `dim_providers.specialty` to it
3. Now clicking a specialty filters ALL other visuals on the page

### Step 5: Format and Polish
1. Click the background → Format → set background color to light gray (#F5F5F5)
2. Add a text box at the top: "HealthFlow Analytics Dashboard"
3. Add a second page (bottom) for Scribe Productivity if desired
4. File → Save as → `HealthFlow_Dashboard.pbix`

---

## 2.5 Key Power BI Concepts to Know (for the interview)

### DAX (Data Analysis Expressions)
**What:** Formula language for Power BI. Like Excel formulas but works across tables.
**Key difference from Excel:** DAX works on COLUMNS and TABLES, not individual cells.

| DAX Function | What It Does | Excel Equivalent |
|-------------|-------------|-----------------|
| `COUNTROWS()` | Count rows in a table | `COUNTA()` |
| `CALCULATE()` | Evaluate with a filter | `SUMIFS()` |
| `DIVIDE()` | Safe division (no #DIV/0!) | `=A/B` |
| `DATEADD()` | Shift dates for comparison | No direct equivalent |
| `RANKX()` | Rank values across a table | `RANK()` |
| `ALL()` | Remove filters for calculation | No equivalent |
| `DATESYTD()` | Year-to-date filter | No equivalent |

### Measures vs Calculated Columns
| | Measure | Calculated Column |
|---|---------|------------------|
| **When calculated** | At query time (dynamic) | At data refresh (static) |
| **Storage** | No storage (computed on fly) | Stored in table |
| **Use case** | Aggregations (SUM, AVG, COUNT) | Row-level calculations |
| **Example** | `Avg Quality = AVERAGE(...)` | `Age Group = IF(age>65, "Senior", "Adult")` |

**Rule:** Use measures for anything that should change when you filter. Use calculated columns for fixed row-level values.

### Filter Context
**What:** The set of filters active when a DAX measure is evaluated.
**Why it matters:** When you click "Cardiology" in a slicer, ALL measures automatically recalculate for Cardiology only. This is Power BI's killer feature.

**Example:**
```dax
Telehealth % = DIVIDE(
    CALCULATE(COUNTROWS(fact_encounters), fact_encounters[encounter_type] = "Telehealth"),
    COUNTROWS(fact_encounters)
)
```
- If no filter: calculates for ALL encounters
- If user clicks "Cardiology" slicer: calculates only for Cardiology encounters
- The formula doesn't change — the **filter context** does

### Relationships
**What:** Links between tables that allow Power BI to combine data.
**Direction:** Always from fact → dimension (many-to-one).
**Example:** `fact_encounters.provider_id` → `dim_providers.provider_id`
This means: "each encounter has one provider, but each provider has many encounters."

---

## 2.6 How to Talk About Power BI in Your Video

**If you CAN demo Power BI:**
- "I exported my data as a star schema with 5 dimension tables and 2 fact tables"
- "Here I've built an interactive dashboard — when I click Cardiology, everything filters automatically"
- "I wrote 15 DAX measures including MoM growth using DATEADD and provider ranking using RANKX"

**If you CANNOT demo Power BI (Linux):**
- "I designed a star schema data model for Power BI with proper dimension and fact tables"
- Show the CSV files: "Here are my 5 dimension tables and 2 fact tables"
- Show `dax_measures.md`: "I've prepared 15 DAX measures ready to import"
- "I understand concepts like filter context, measures vs calculated columns, and CALCULATE"
- Show the Streamlit dashboard: "And here's the same dashboard I built as a web app using Python, which demonstrates the same analytics"

---

## 2.7 Common Interview Questions About Power BI

**Q: What is the difference between Power BI Desktop and Power BI Service?**
A: Desktop is the free authoring tool (Windows app) where you build reports. Service is the cloud platform (app.powerbi.com) where you publish and share reports with your team.

**Q: What is a star schema?**
A: A data modeling pattern where a central fact table (with measurements) connects to multiple dimension tables (with descriptive attributes). It looks like a star. It's the standard for Power BI because it's fast to query and easy to understand.

**Q: What is DAX?**
A: Data Analysis Expressions — Power BI's formula language. It's similar to Excel formulas but works on entire tables and columns instead of individual cells. Key functions: CALCULATE, DIVIDE, DATEADD, RANKX, ALL.

**Q: What is the difference between a measure and a calculated column?**
A: A measure is calculated dynamically when the user interacts with the report (changes with filters). A calculated column is computed once when data loads and stored in the table. Use measures for aggregations, calculated columns for row-level values.

**Q: How do you handle relationships in Power BI?**
A: Create relationships between tables based on matching key columns. Typically many-to-one from fact tables to dimension tables. Power BI uses these to automatically filter and aggregate across tables.

---

## 2.8 Google Sheets Dashboard (Alternative for sharing)

Since your video submission needs a shareable link, Google Sheets is practical:

### How to Create a Google Sheets Dashboard:
1. Upload `HealthFlow_Dashboard.xlsx` to Google Drive
2. Right-click → Open with → Google Sheets
3. Most formatting and charts will transfer
4. To share: Click **Share** → **Anyone with the link** → **Viewer**
5. Copy the link for your application form

### Adding Interactive Features in Google Sheets:
Google Sheets has some features you can add manually:

**Dropdown filter:**
1. Go to a new cell (e.g., N1)
2. Data → Data Validation → List of items
3. Type: `All,Cardiology,Dermatology,General Practice,Internal Medicine`
4. Now use `FILTER()` function to filter your data based on this dropdown

**Sparklines (mini charts in cells):**
```
=SPARKLINE(B10:B21, {"charttype","bar";"color1","blue"})
```

**Conditional formatting (if not transferred):**
1. Select the quality column
2. Format → Conditional formatting
3. Add rule: "Less than 0.85" → Red background
4. Add rule: "Greater than 0.88" → Green background

---

# PART 3: QUICK REFERENCE CHEAT SHEET

## Excel Functions You Should Memorize

```
=VLOOKUP(101, A:D, 3, FALSE)           Find provider 101's specialty
=SUMIF(B:B, "Cardiology", D:D)         Sum encounters for Cardiology
=COUNTIF(C:C, ">0.9")                  Count high-quality notes
=AVERAGEIF(B:B, "Telehealth", E:E)     Avg TAT for telehealth
=IF(C2>0.9, "Good", "Needs Work")      Classify quality
=INDEX(C:C, MATCH(101, A:A, 0))        Flexible lookup (better than VLOOKUP)
=TEXT(A2, "YYYY-MM")                    Format date as year-month
```

## DAX Measures You Should Memorize

```dax
-- Count rows
Total Encounters = COUNTROWS(fact_encounters)

-- Average
Avg Quality = AVERAGE(fact_encounters[note_quality_score])

-- Percentage with safe division
Telehealth % = DIVIDE(
    CALCULATE(COUNTROWS(fact_encounters), 
              fact_encounters[encounter_type] = "Telehealth"),
    COUNTROWS(fact_encounters), 0)

-- Compare to previous month
MoM Growth = 
    VAR Current = [Total Encounters]
    VAR Previous = CALCULATE([Total Encounters], 
                             DATEADD(dim_dates[full_date], -1, MONTH))
    RETURN DIVIDE(Current - Previous, Previous, 0)

-- Rank
Provider Rank = RANKX(ALL(dim_providers), [Avg Quality], , DESC, Dense)
```

## Star Schema Design Rules

1. **Fact tables** hold NUMBERS (counts, amounts, scores, durations)
2. **Dimension tables** hold TEXT (names, categories, descriptions)
3. **Relationships** go from fact → dimension (many-to-one)
4. **Date dimension** is ALWAYS needed (one row per calendar day)
5. **Surrogate keys** (integer IDs) are better than natural keys (UUIDs, names)
6. **Avoid snowflaking** — keep dimensions flat, don't chain dim → dim → dim

---

# PART 4: WHAT TO PRACTICE BEFORE THE VIDEO

## 30-Minute Practice Plan

### 10 minutes: Excel
1. Open `HealthFlow_Dashboard.xlsx`
2. Navigate all 5 sheets — understand what each shows
3. Click on a chart — see how it highlights the data source
4. Try changing a number in the table — see the chart update
5. Look at conditional formatting rules: Home → Conditional Formatting → Manage Rules

### 10 minutes: Power BI Concepts
1. Read the DAX measures in `project/05_powerbi_prep/dax_measures.md`
2. Understand CALCULATE — it's the most important DAX function
3. Draw the star schema on paper — know which table connects where
4. Practice saying: "The star schema has 5 dimensions and 2 fact tables"

### 10 minutes: Demo Run
1. Run `python project/run_all.py` — make sure it works
2. Run `streamlit run project/06_web_dashboard/app.py`
3. Click through all 5 tabs in the web dashboard
4. Try the filters in the sidebar
5. Practice the 5-minute video flow (see PROJECT_GUIDE.md)
