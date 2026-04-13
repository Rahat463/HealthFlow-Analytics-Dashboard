# Power BI DAX Measures — HealthFlow Analytics

## How to Import into Power BI
1. Open Power BI Desktop → Get Data → CSV
2. Import all files from `output/powerbi/`:
   - `dim_dates.csv`, `dim_providers.csv`, `dim_patients.csv`, `dim_diagnoses.csv`, `dim_scribes.csv`
   - `fact_encounters.csv`, `fact_scribe_activity.csv`
3. In Model View, create relationships:
   - `fact_encounters[date_key]` → `dim_dates[date_key]`
   - `fact_encounters[provider_id]` → `dim_providers[provider_id]`
   - `fact_encounters[patient_id]` → `dim_patients[patient_id]`
   - `fact_encounters[diagnosis_code]` → `dim_diagnoses[icd_code]`
   - `fact_scribe_activity[scribe_id]` → `dim_scribes[scribe_id]`
   - `fact_scribe_activity[encounter_id]` → `fact_encounters[encounter_id]`
4. Add the measures below to the `fact_encounters` table

---

## Core KPI Measures

```dax
// 1. Total Encounters
Total Encounters =
    COUNTROWS(fact_encounters)

// 2. Average Quality Score
Avg Quality Score =
    AVERAGE(fact_encounters[note_quality_score])

// 3. Average Turnaround Time
Avg TAT =
    AVERAGE(fact_encounters[note_turnaround_minutes])

// 4. SLA Compliance Rate
SLA Compliance % =
    DIVIDE(
        CALCULATE(COUNTROWS(fact_encounters), fact_encounters[sla_met] = TRUE()),
        COUNTROWS(fact_encounters),
        0
    )

// 5. Telehealth Percentage
Telehealth % =
    DIVIDE(
        CALCULATE(COUNTROWS(fact_encounters), fact_encounters[encounter_type] = "Telehealth"),
        COUNTROWS(fact_encounters),
        0
    )

// 6. Completion Rate
Completion Rate =
    DIVIDE(
        CALCULATE(COUNTROWS(fact_encounters), fact_encounters[notes_status] = "Completed"),
        COUNTROWS(fact_encounters),
        0
    )

// 7. Unique Patients
Unique Patients =
    DISTINCTCOUNT(fact_encounters[patient_id])
```

## Trend & Comparison Measures

```dax
// 8. Month-over-Month Encounter Growth
MoM Encounter Growth =
    VAR CurrentMonth = [Total Encounters]
    VAR PrevMonth =
        CALCULATE(
            [Total Encounters],
            DATEADD(dim_dates[full_date], -1, MONTH)
        )
    RETURN
        DIVIDE(CurrentMonth - PrevMonth, PrevMonth, 0)

// 9. Quality vs Prior Month
Quality vs Prior Month =
    VAR CurrentQuality = [Avg Quality Score]
    VAR PriorQuality =
        CALCULATE(
            [Avg Quality Score],
            DATEADD(dim_dates[full_date], -1, MONTH)
        )
    RETURN
        CurrentQuality - PriorQuality

// 10. Year-to-Date Running Total
YTD Encounters =
    CALCULATE(
        [Total Encounters],
        DATESYTD(dim_dates[full_date])
    )

// 11. 7-Day Rolling Average Quality
Rolling 7D Quality =
    AVERAGEX(
        DATESINPERIOD(dim_dates[full_date], MAX(dim_dates[full_date]), -7, DAY),
        CALCULATE(AVERAGE(fact_encounters[note_quality_score]))
    )
```

## Ranking & Segmentation Measures

```dax
// 12. Provider Rank by Quality
Provider Quality Rank =
    RANKX(
        ALL(dim_providers),
        [Avg Quality Score],
        ,
        DESC,
        Dense
    )

// 13. Top N Provider Filter
Is Top 5 Provider =
    IF([Provider Quality Rank] <= 5, 1, 0)

// 14. Scribe Productivity (Notes per Active Day)
Scribe Notes Per Day =
    DIVIDE(
        COUNTROWS(fact_scribe_activity),
        DISTINCTCOUNT(fact_scribe_activity[date_key]),
        0
    )

// 15. Diagnosis Category Mix
Chronic % =
    DIVIDE(
        CALCULATE(
            COUNTROWS(fact_encounters),
            dim_diagnoses[category] = "Chronic"
        ),
        COUNTROWS(fact_encounters),
        0
    )
```

## Suggested Visuals

| Visual Type | Measures | Dimensions |
|-------------|----------|------------|
| KPI Card | Total Encounters, Avg Quality, Avg TAT | — |
| Line Chart | Avg Quality Score, Rolling 7D Quality | dim_dates[month_name] |
| Bar Chart | Total Encounters | dim_providers[name] |
| Stacked Bar | Total Encounters | dim_providers[specialty], dim_dates[month_name] |
| Donut Chart | Total Encounters | dim_diagnoses[category] |
| Table | Provider Quality Rank, Avg Quality, Avg TAT | dim_providers[name, specialty] |
| Scatter Plot | Scribe Notes Per Day vs Avg Quality | dim_scribes[name] |
| Matrix | Total Encounters, SLA Compliance % | dim_providers[specialty] (rows), dim_dates[month_name] (cols) |
