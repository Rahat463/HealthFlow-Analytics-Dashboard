-- =============================================================
-- HealthFlow Analytics Dashboard — 10 Production KPI Queries
-- SQLite-compatible | PostgreSQL equivalents noted in comments
-- =============================================================


-- =============================================
-- Q1: EXECUTIVE SUMMARY KPIs
-- Technique: CTE + conditional aggregation
-- Business: Monthly dashboard for leadership
-- =============================================
WITH monthly AS (
    SELECT
        strftime('%Y-%m', encounter_date)       AS month,
        -- PostgreSQL: DATE_TRUNC('month', encounter_date)
        COUNT(*)                                AS total_encounters,
        ROUND(AVG(note_turnaround_minutes), 1)  AS avg_tat,
        ROUND(AVG(note_quality_score), 3)       AS avg_quality,
        ROUND(100.0 * SUM(CASE WHEN notes_status = 'Completed' THEN 1 ELSE 0 END)
              / COUNT(*), 1)                    AS completion_rate_pct,
        ROUND(100.0 * SUM(CASE WHEN encounter_type = 'Telehealth' THEN 1 ELSE 0 END)
              / COUNT(*), 1)                    AS telehealth_pct,
        COUNT(DISTINCT patient_id)              AS unique_patients,
        COUNT(DISTINCT provider_id)             AS unique_providers
    FROM encounters
    WHERE note_quality_score IS NOT NULL
      AND note_turnaround_minutes IS NOT NULL
      AND note_turnaround_minutes > 0
    GROUP BY strftime('%Y-%m', encounter_date)
)
SELECT * FROM monthly ORDER BY month;


-- =============================================
-- Q2: PROVIDER PERFORMANCE SCORECARD
-- Technique: RANK() OVER (PARTITION BY) + composite scoring
-- Business: Identify top/bottom performers per specialty
-- =============================================
WITH provider_stats AS (
    SELECT
        p.provider_id,
        p.name,
        p.specialty,
        p.department,
        COUNT(*)                                AS total_encounters,
        ROUND(AVG(e.note_quality_score), 3)     AS avg_quality,
        ROUND(AVG(e.note_turnaround_minutes), 1) AS avg_tat,
        ROUND(100.0 * SUM(CASE WHEN e.notes_status = 'Completed' THEN 1 ELSE 0 END)
              / COUNT(*), 1)                    AS completion_rate,
        COUNT(DISTINCT e.patient_id)            AS unique_patients
    FROM encounters e
    JOIN providers p ON e.provider_id = p.provider_id
    WHERE e.note_quality_score IS NOT NULL
      AND e.note_turnaround_minutes > 0
    GROUP BY p.provider_id, p.name, p.specialty, p.department
),
scored AS (
    SELECT *,
        ROUND(
            0.4 * avg_quality +
            0.3 * (1.0 - MIN(avg_tat, 120.0) / 120.0) +
            0.3 * (completion_rate / 100.0),
        3) AS composite_score
    FROM provider_stats
)
SELECT
    scored.*,
    RANK() OVER (PARTITION BY specialty ORDER BY composite_score DESC) AS rank_in_specialty
FROM scored
ORDER BY specialty, rank_in_specialty;


-- =============================================
-- Q3: MONTH-OVER-MONTH TRENDS WITH ALERTS
-- Technique: LAG() window function + growth rate
-- Business: Detect quality drops early
-- =============================================
WITH monthly AS (
    SELECT
        strftime('%Y-%m', encounter_date)       AS month,
        COUNT(*)                                AS encounters,
        ROUND(AVG(note_quality_score), 3)       AS avg_quality,
        ROUND(AVG(note_turnaround_minutes), 1)  AS avg_tat
    FROM encounters
    WHERE note_quality_score IS NOT NULL
      AND note_turnaround_minutes > 0
    GROUP BY strftime('%Y-%m', encounter_date)
)
SELECT
    month,
    encounters,
    avg_quality,
    avg_tat,
    LAG(encounters) OVER (ORDER BY month)       AS prev_encounters,
    LAG(avg_quality) OVER (ORDER BY month)      AS prev_quality,
    ROUND(100.0 * (encounters - LAG(encounters) OVER (ORDER BY month))
          / LAG(encounters) OVER (ORDER BY month), 1) AS encounter_growth_pct,
    ROUND(100.0 * (avg_quality - LAG(avg_quality) OVER (ORDER BY month))
          / LAG(avg_quality) OVER (ORDER BY month), 2) AS quality_change_pct,
    CASE
        WHEN avg_quality < LAG(avg_quality) OVER (ORDER BY month) * 0.95
        THEN 'ALERT: Quality dropped >5%'
        WHEN avg_tat > LAG(avg_tat) OVER (ORDER BY month) * 1.10
        THEN 'ALERT: TAT increased >10%'
        ELSE 'OK'
    END AS status_flag
FROM monthly
ORDER BY month;


-- =============================================
-- Q4: SCRIBE PRODUCTIVITY LEADERBOARD
-- Technique: Multi-JOIN + NTILE window function
-- Business: Identify scribes needing training
-- =============================================
WITH scribe_stats AS (
    SELECT
        s.scribe_id,
        s.name AS scribe_name,
        s.experience_months,
        s.shift,
        COUNT(sa.activity_id)                   AS notes_completed,
        COUNT(DISTINCT DATE(sa.start_time))     AS active_days,
        ROUND(1.0 * COUNT(sa.activity_id) /
              MAX(1, COUNT(DISTINCT DATE(sa.start_time))), 1) AS notes_per_day,
        ROUND(AVG(sa.quality_score), 3)         AS avg_quality,
        ROUND(AVG(sa.edits_count), 1)           AS avg_edits,
        ROUND(AVG(
            (JULIANDAY(sa.end_time) - JULIANDAY(sa.start_time)) * 24 * 60
        ), 1)                                   AS avg_duration_min
        -- PostgreSQL: EXTRACT(EPOCH FROM (end_time - start_time)) / 60
    FROM scribes s
    LEFT JOIN scribe_activity sa ON s.scribe_id = sa.scribe_id
    GROUP BY s.scribe_id, s.name, s.experience_months, s.shift
)
SELECT
    scribe_stats.*,
    NTILE(5) OVER (ORDER BY notes_per_day DESC) AS productivity_quintile,
    CASE
        WHEN NTILE(5) OVER (ORDER BY avg_quality ASC) = 1 THEN 'Needs Training'
        WHEN NTILE(5) OVER (ORDER BY avg_quality DESC) = 1 THEN 'Top Performer'
        ELSE 'On Track'
    END AS performance_tier
FROM scribe_stats
ORDER BY avg_quality DESC;


-- =============================================
-- Q5: SPECIALTY x MONTH ENCOUNTER PIVOT
-- Technique: Manual pivot with COUNT(CASE WHEN)
-- Business: Capacity planning by specialty
-- =============================================
SELECT
    p.specialty,
    COUNT(CASE WHEN strftime('%m', e.encounter_date) = '01' THEN 1 END) AS jan,
    COUNT(CASE WHEN strftime('%m', e.encounter_date) = '02' THEN 1 END) AS feb,
    COUNT(CASE WHEN strftime('%m', e.encounter_date) = '03' THEN 1 END) AS mar,
    COUNT(CASE WHEN strftime('%m', e.encounter_date) = '04' THEN 1 END) AS apr,
    COUNT(CASE WHEN strftime('%m', e.encounter_date) = '05' THEN 1 END) AS may,
    COUNT(CASE WHEN strftime('%m', e.encounter_date) = '06' THEN 1 END) AS jun,
    COUNT(CASE WHEN strftime('%m', e.encounter_date) = '07' THEN 1 END) AS jul,
    COUNT(CASE WHEN strftime('%m', e.encounter_date) = '08' THEN 1 END) AS aug,
    COUNT(CASE WHEN strftime('%m', e.encounter_date) = '09' THEN 1 END) AS sep,
    COUNT(CASE WHEN strftime('%m', e.encounter_date) = '10' THEN 1 END) AS oct,
    COUNT(CASE WHEN strftime('%m', e.encounter_date) = '11' THEN 1 END) AS nov,
    COUNT(CASE WHEN strftime('%m', e.encounter_date) = '12' THEN 1 END) AS dec_,
    COUNT(*)                                                             AS total
FROM encounters e
JOIN providers p ON e.provider_id = p.provider_id
GROUP BY p.specialty
ORDER BY total DESC;
-- PostgreSQL: Use CROSSTAB() from tablefunc extension


-- =============================================
-- Q6: TAT SLA COMPLIANCE BY PROVIDER
-- Technique: Window function comparison to dept avg
-- Business: Which providers consistently miss SLA?
-- =============================================
WITH sla_targets AS (
    -- Industry SLA: TAT targets by specialty
    SELECT 'General Practice'  AS specialty, 40 AS target_tat UNION ALL
    SELECT 'Internal Medicine', 45 UNION ALL
    SELECT 'Cardiology',       60 UNION ALL
    SELECT 'Orthopedics',      55 UNION ALL
    SELECT 'Neurology',        55 UNION ALL
    SELECT 'Dermatology',      35 UNION ALL
    SELECT 'Pediatrics',       38 UNION ALL
    SELECT 'Obstetrics',       50 UNION ALL
    SELECT 'Other',            45
),
provider_sla AS (
    SELECT
        p.provider_id,
        p.name,
        p.specialty,
        p.department,
        COUNT(*)                                AS total_notes,
        ROUND(100.0 * SUM(CASE
            WHEN e.note_turnaround_minutes <= t.target_tat THEN 1 ELSE 0
        END) / COUNT(*), 1)                     AS sla_compliance_pct,
        ROUND(AVG(e.note_turnaround_minutes), 1) AS avg_tat,
        t.target_tat
    FROM encounters e
    JOIN providers p ON e.provider_id = p.provider_id
    JOIN sla_targets t ON p.specialty = t.specialty
    WHERE e.note_turnaround_minutes IS NOT NULL
      AND e.note_turnaround_minutes > 0
    GROUP BY p.provider_id, p.name, p.specialty, p.department, t.target_tat
)
SELECT
    provider_sla.*,
    ROUND(AVG(sla_compliance_pct) OVER (PARTITION BY department), 1) AS dept_avg_compliance,
    CASE
        WHEN sla_compliance_pct < AVG(sla_compliance_pct) OVER (PARTITION BY department) - 10
        THEN 'Below Dept Avg'
        ELSE 'Meets Standard'
    END AS compliance_flag
FROM provider_sla
ORDER BY sla_compliance_pct ASC;


-- =============================================
-- Q7: PATIENT VISIT GAP ANALYSIS
-- Technique: LEAD() + date arithmetic
-- Business: Identify patients at risk of churn
-- =============================================
WITH patient_visits AS (
    SELECT
        e.patient_id,
        pat.name AS patient_name,
        e.encounter_date,
        d.description AS diagnosis,
        d.category AS diagnosis_category,
        LEAD(e.encounter_date) OVER (
            PARTITION BY e.patient_id ORDER BY e.encounter_date
        ) AS next_visit_date
    FROM encounters e
    JOIN patients pat ON e.patient_id = pat.patient_id
    LEFT JOIN diagnoses d ON e.diagnosis_code = d.icd_code
    WHERE e.notes_status IN ('Completed', 'Reviewed')
),
gaps AS (
    SELECT *,
        ROUND(JULIANDAY(next_visit_date) - JULIANDAY(encounter_date)) AS days_to_next
        -- PostgreSQL: EXTRACT(DAY FROM next_visit_date - encounter_date)
    FROM patient_visits
    WHERE next_visit_date IS NOT NULL
)
SELECT
    patient_id,
    patient_name,
    encounter_date,
    next_visit_date,
    days_to_next,
    diagnosis,
    diagnosis_category,
    CASE
        WHEN days_to_next > 90 AND diagnosis_category = 'Chronic'
        THEN 'HIGH RISK: Chronic patient, 90+ day gap'
        WHEN days_to_next > 90
        THEN 'MEDIUM RISK: 90+ day gap'
        WHEN days_to_next > 60
        THEN 'LOW RISK: 60-90 day gap'
        ELSE 'Normal'
    END AS risk_level
FROM gaps
WHERE days_to_next > 60
ORDER BY days_to_next DESC
LIMIT 50;


-- =============================================
-- Q8: ROLLING 7-DAY QUALITY ANOMALY DETECTION
-- Technique: Window frame clause + CASE WHEN flag
-- Business: Real-time quality monitoring
-- =============================================
WITH daily AS (
    SELECT
        DATE(encounter_date) AS day,
        COUNT(*)                                AS encounter_count,
        ROUND(AVG(note_quality_score), 3)       AS avg_quality,
        ROUND(AVG(note_turnaround_minutes), 1)  AS avg_tat
    FROM encounters
    WHERE note_quality_score IS NOT NULL
      AND note_turnaround_minutes > 0
    GROUP BY DATE(encounter_date)
),
rolling AS (
    SELECT
        day,
        encounter_count,
        avg_quality,
        avg_tat,
        ROUND(AVG(avg_quality) OVER (
            ORDER BY day ROWS BETWEEN 6 PRECEDING AND CURRENT ROW
        ), 3) AS rolling_7d_quality,
        ROUND(AVG(avg_tat) OVER (
            ORDER BY day ROWS BETWEEN 6 PRECEDING AND CURRENT ROW
        ), 1) AS rolling_7d_tat,
        ROW_NUMBER() OVER (ORDER BY day) AS day_num
    FROM daily
)
SELECT
    day,
    encounter_count,
    avg_quality,
    rolling_7d_quality,
    avg_tat,
    rolling_7d_tat,
    CASE
        WHEN day_num >= 7 AND avg_quality < rolling_7d_quality * 0.85
        THEN 'ANOMALY: Quality 15%+ below rolling avg'
        WHEN day_num >= 7 AND avg_tat > rolling_7d_tat * 1.20
        THEN 'ANOMALY: TAT 20%+ above rolling avg'
        ELSE 'Normal'
    END AS anomaly_flag
FROM rolling
ORDER BY day;


-- =============================================
-- Q9: TELEHEALTH ADOPTION TREND BY SPECIALTY
-- Technique: 3 CTEs + moving average
-- Business: Track telehealth growth for strategic planning
-- =============================================
WITH monthly_by_spec AS (
    SELECT
        strftime('%Y-%m', e.encounter_date)     AS month,
        p.specialty,
        COUNT(*)                                AS total,
        SUM(CASE WHEN e.encounter_type = 'Telehealth' THEN 1 ELSE 0 END) AS telehealth_count,
        ROUND(100.0 * SUM(CASE WHEN e.encounter_type = 'Telehealth' THEN 1 ELSE 0 END)
              / COUNT(*), 1)                    AS telehealth_pct
    FROM encounters e
    JOIN providers p ON e.provider_id = p.provider_id
    GROUP BY strftime('%Y-%m', e.encounter_date), p.specialty
),
with_moving_avg AS (
    SELECT *,
        ROUND(AVG(telehealth_pct) OVER (
            PARTITION BY specialty
            ORDER BY month
            ROWS BETWEEN 2 PRECEDING AND CURRENT ROW
        ), 1) AS moving_avg_3m
    FROM monthly_by_spec
),
with_trend AS (
    SELECT *,
        telehealth_pct - LAG(telehealth_pct) OVER (
            PARTITION BY specialty ORDER BY month
        ) AS pct_change,
        CASE
            WHEN telehealth_pct > LAG(telehealth_pct) OVER (PARTITION BY specialty ORDER BY month)
             AND LAG(telehealth_pct) OVER (PARTITION BY specialty ORDER BY month) >
                 LAG(telehealth_pct, 2) OVER (PARTITION BY specialty ORDER BY month)
            THEN 'Uptrend (3 consecutive months)'
            ELSE NULL
        END AS trend_signal
    FROM with_moving_avg
)
SELECT * FROM with_trend
ORDER BY specialty, month;


-- =============================================
-- Q10: QA AUDIT IMPACT ANALYSIS
-- Technique: JOIN + GROUP BY + HAVING + before/after
-- Business: Which quality issues have biggest impact?
-- =============================================
WITH audit_impact AS (
    SELECT
        q.finding_category,
        COUNT(*)                                    AS audits_count,
        ROUND(AVG(q.original_score), 3)             AS avg_original_score,
        ROUND(AVG(q.revised_score), 3)              AS avg_revised_score,
        ROUND(AVG(q.revised_score - q.original_score), 3) AS avg_score_change,
        ROUND(AVG(CASE
            WHEN q.revised_score < q.original_score
            THEN q.original_score - q.revised_score
            ELSE 0
        END), 3)                                    AS avg_downgrade_amount,
        SUM(CASE WHEN q.revised_score < q.original_score THEN 1 ELSE 0 END) AS downgrades,
        SUM(CASE WHEN q.revised_score >= q.original_score THEN 1 ELSE 0 END) AS upgrades_or_same
    FROM quality_audit_log q
    GROUP BY q.finding_category
    HAVING COUNT(*) >= 3
),
with_specialty AS (
    SELECT
        q.finding_category,
        p.specialty,
        COUNT(*) AS occurrences
    FROM quality_audit_log q
    JOIN encounters e ON q.encounter_id = e.encounter_id
    JOIN providers p ON e.provider_id = p.provider_id
    GROUP BY q.finding_category, p.specialty
)
SELECT
    a.*,
    ROUND(100.0 * a.downgrades / a.audits_count, 1) AS downgrade_rate_pct,
    (
        SELECT ws.specialty
        FROM with_specialty ws
        WHERE ws.finding_category = a.finding_category
        ORDER BY ws.occurrences DESC
        LIMIT 1
    ) AS most_affected_specialty
FROM audit_impact a
ORDER BY avg_downgrade_amount DESC;
