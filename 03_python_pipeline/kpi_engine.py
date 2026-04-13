"""
HealthFlow Analytics — KPI Computation Engine
=============================================
Mirrors the 10 SQL queries in pandas, producing DataFrames
that feed the Excel dashboard and Power BI exports.
"""

import pandas as pd
import numpy as np
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
OUTPUT_DIR = BASE_DIR / "output"

# SLA targets by specialty (minutes)
SLA_TARGETS = {
    "General Practice": 40, "Internal Medicine": 45, "Cardiology": 60,
    "Orthopedics": 55, "Neurology": 55, "Dermatology": 35,
    "Pediatrics": 38, "Obstetrics": 50, "Other": 45,
}


def compute_monthly_kpis(encounters_df):
    """Q1 equivalent: Monthly executive summary KPIs with MoM growth."""
    df = encounters_df[
        encounters_df["note_quality_score"].notna() &
        (encounters_df["note_turnaround_minutes"] > 0)
    ].copy()

    monthly = df.groupby("month").agg(
        total_encounters=("encounter_id", "count"),
        avg_tat=("note_turnaround_minutes", "mean"),
        avg_quality=("note_quality_score", "mean"),
        completion_rate=("notes_status", lambda x: 100.0 * (x == "Completed").sum() / len(x)),
        telehealth_pct=("encounter_type", lambda x: 100.0 * (x == "Telehealth").sum() / len(x)),
        unique_patients=("patient_id", "nunique"),
        unique_providers=("provider_id", "nunique"),
    ).reset_index()

    monthly["avg_tat"] = monthly["avg_tat"].round(1)
    monthly["avg_quality"] = monthly["avg_quality"].round(3)
    monthly["completion_rate"] = monthly["completion_rate"].round(1)
    monthly["telehealth_pct"] = monthly["telehealth_pct"].round(1)

    # MoM growth
    monthly["encounter_growth_pct"] = monthly["total_encounters"].pct_change().mul(100).round(1)
    monthly["quality_change_pct"] = monthly["avg_quality"].pct_change().mul(100).round(2)

    return monthly


def compute_provider_scorecard(encounters_df, providers_df):
    """Q2 equivalent: Provider performance with composite score and ranking."""
    df = encounters_df.merge(providers_df, on="provider_id", how="left")
    df = df[df["note_quality_score"].notna() & (df["note_turnaround_minutes"] > 0)]

    stats = df.groupby(["provider_id", "name", "specialty", "department"]).agg(
        total_encounters=("encounter_id", "count"),
        avg_quality=("note_quality_score", "mean"),
        avg_tat=("note_turnaround_minutes", "mean"),
        completion_rate=("notes_status", lambda x: 100.0 * (x == "Completed").sum() / len(x)),
        unique_patients=("patient_id", "nunique"),
    ).reset_index()

    stats["avg_quality"] = stats["avg_quality"].round(3)
    stats["avg_tat"] = stats["avg_tat"].round(1)
    stats["completion_rate"] = stats["completion_rate"].round(1)

    # Composite score: 0.4*quality + 0.3*(1 - normalized TAT) + 0.3*completion
    stats["composite_score"] = (
        0.4 * stats["avg_quality"] +
        0.3 * (1.0 - stats["avg_tat"].clip(upper=120) / 120.0) +
        0.3 * (stats["completion_rate"] / 100.0)
    ).round(3)

    # Rank within specialty
    stats["rank_in_specialty"] = stats.groupby("specialty")["composite_score"].rank(
        ascending=False, method="min"
    ).astype(int)

    return stats.sort_values(["specialty", "rank_in_specialty"])


def compute_scribe_leaderboard(scribe_activity_df, scribes_df):
    """Q4 equivalent: Scribe productivity with quintile ranking."""
    sa = scribe_activity_df.copy()
    sa["start_time"] = pd.to_datetime(sa["start_time"])
    sa["end_time"] = pd.to_datetime(sa["end_time"])
    sa["duration_min"] = (sa["end_time"] - sa["start_time"]).dt.total_seconds() / 60
    sa["date"] = sa["start_time"].dt.date

    stats = sa.groupby("scribe_id").agg(
        notes_completed=("activity_id", "count"),
        active_days=("date", "nunique"),
        avg_quality=("quality_score", "mean"),
        avg_edits=("edits_count", "mean"),
        avg_duration_min=("duration_min", "mean"),
    ).reset_index()

    stats["notes_per_day"] = (stats["notes_completed"] / stats["active_days"]).round(1)
    stats["avg_quality"] = stats["avg_quality"].round(3)
    stats["avg_edits"] = stats["avg_edits"].round(1)
    stats["avg_duration_min"] = stats["avg_duration_min"].round(1)

    # Merge scribe details
    stats = stats.merge(scribes_df[["scribe_id", "name", "experience_months", "shift"]],
                        on="scribe_id", how="left")

    # Quintile ranking
    stats["productivity_quintile"] = pd.qcut(
        stats["notes_per_day"].rank(method="first"), q=5, labels=[1, 2, 3, 4, 5]
    )

    # Performance tier
    stats["performance_tier"] = "On Track"
    bottom_20 = stats["avg_quality"].quantile(0.2)
    top_20 = stats["avg_quality"].quantile(0.8)
    stats.loc[stats["avg_quality"] <= bottom_20, "performance_tier"] = "Needs Training"
    stats.loc[stats["avg_quality"] >= top_20, "performance_tier"] = "Top Performer"

    return stats.sort_values("avg_quality", ascending=False)


def compute_specialty_pivot(encounters_df, providers_df):
    """Q5 equivalent: Specialty x Month encounter count pivot."""
    df = encounters_df.merge(providers_df[["provider_id", "specialty"]], on="provider_id")
    pivot = pd.pivot_table(
        df, index="specialty", columns="month",
        values="encounter_id", aggfunc="count", fill_value=0
    )
    pivot["Total"] = pivot.sum(axis=1)
    return pivot.sort_values("Total", ascending=False)


def compute_sla_analysis(encounters_df, providers_df):
    """Q6 equivalent: TAT SLA compliance by provider."""
    df = encounters_df.merge(providers_df, on="provider_id", how="left")
    df = df[df["note_turnaround_minutes"].notna() & (df["note_turnaround_minutes"] > 0)]
    df["target_tat"] = df["specialty"].map(SLA_TARGETS).fillna(45)
    df["sla_met"] = df["note_turnaround_minutes"] <= df["target_tat"]

    stats = df.groupby(["provider_id", "name", "specialty", "department"]).agg(
        total_notes=("encounter_id", "count"),
        sla_compliance_pct=("sla_met", lambda x: round(100.0 * x.sum() / len(x), 1)),
        avg_tat=("note_turnaround_minutes", "mean"),
        target_tat=("target_tat", "first"),
    ).reset_index()

    stats["avg_tat"] = stats["avg_tat"].round(1)

    # Department average
    stats["dept_avg_compliance"] = stats.groupby("department")["sla_compliance_pct"].transform("mean").round(1)
    stats["compliance_flag"] = np.where(
        stats["sla_compliance_pct"] < stats["dept_avg_compliance"] - 10,
        "Below Dept Avg", "Meets Standard"
    )

    return stats.sort_values("sla_compliance_pct")


def compute_daily_trends(encounters_df):
    """Q8 equivalent: Daily trends with rolling 7-day averages and anomaly detection."""
    df = encounters_df.copy()
    df["date"] = pd.to_datetime(df["encounter_date"]).dt.date

    daily = df.groupby("date").agg(
        encounter_count=("encounter_id", "count"),
        avg_quality=("note_quality_score", "mean"),
        avg_tat=("note_turnaround_minutes", "mean"),
    ).reset_index()

    daily["avg_quality"] = daily["avg_quality"].round(3)
    daily["avg_tat"] = daily["avg_tat"].round(1)

    # Rolling 7-day averages
    daily["rolling_7d_quality"] = daily["avg_quality"].rolling(7, min_periods=1).mean().round(3)
    daily["rolling_7d_tat"] = daily["avg_tat"].rolling(7, min_periods=1).mean().round(1)

    # Anomaly flags
    daily["anomaly_flag"] = "Normal"
    mask_quality = (daily.index >= 6) & (daily["avg_quality"] < daily["rolling_7d_quality"] * 0.85)
    mask_tat = (daily.index >= 6) & (daily["avg_tat"] > daily["rolling_7d_tat"] * 1.20)
    daily.loc[mask_quality, "anomaly_flag"] = "Quality Anomaly"
    daily.loc[mask_tat, "anomaly_flag"] = "TAT Anomaly"

    return daily


def compute_telehealth_trends(encounters_df, providers_df):
    """Q9 equivalent: Telehealth adoption % by specialty over time."""
    df = encounters_df.merge(providers_df[["provider_id", "specialty"]], on="provider_id")

    monthly = df.groupby(["month", "specialty"]).agg(
        total=("encounter_id", "count"),
        telehealth_count=("encounter_type", lambda x: (x == "Telehealth").sum()),
    ).reset_index()

    monthly["telehealth_pct"] = (100.0 * monthly["telehealth_count"] / monthly["total"]).round(1)

    # 3-month moving average per specialty
    monthly = monthly.sort_values(["specialty", "month"])
    monthly["moving_avg_3m"] = monthly.groupby("specialty")["telehealth_pct"].transform(
        lambda x: x.rolling(3, min_periods=1).mean()
    ).round(1)

    return monthly


def compute_diagnosis_distribution(encounters_df, diagnoses_df):
    """Diagnosis frequency and category breakdown."""
    df = encounters_df.merge(diagnoses_df, left_on="diagnosis_code", right_on="icd_code", how="left")

    dist = df.groupby(["diagnosis_code", "description", "category"]).agg(
        count=("encounter_id", "count")
    ).reset_index().sort_values("count", ascending=False)

    dist["pct"] = (100.0 * dist["count"] / dist["count"].sum()).round(1)
    return dist


def compute_overall_kpis(encounters_df):
    """Single-row summary of overall KPIs for dashboard header."""
    df = encounters_df[
        encounters_df["note_quality_score"].notna() &
        (encounters_df["note_turnaround_minutes"] > 0)
    ]
    return {
        "total_encounters": len(df),
        "avg_quality": round(df["note_quality_score"].mean(), 3),
        "avg_tat": round(df["note_turnaround_minutes"].mean(), 1),
        "completion_rate": round(100.0 * (df["notes_status"] == "Completed").sum() / len(df), 1),
        "telehealth_pct": round(100.0 * (df["encounter_type"] == "Telehealth").sum() / len(df), 1),
        "unique_patients": df["patient_id"].nunique(),
        "unique_providers": df["provider_id"].nunique(),
    }


def main(data=None):
    """Compute all KPIs. Accepts data dict or loads from CSVs."""
    if data is None:
        print("\n[KPIs] Loading cleaned data...")
        encounters = pd.read_csv(OUTPUT_DIR / "cleaned_encounters.csv")
        providers = pd.read_csv(OUTPUT_DIR / "raw_providers.csv")
        scribes = pd.read_csv(OUTPUT_DIR / "raw_scribes.csv")
        scribe_activity = pd.read_csv(OUTPUT_DIR / "raw_scribe_activity.csv")
        diagnoses = pd.read_csv(OUTPUT_DIR / "raw_diagnoses.csv")
    else:
        encounters = data["encounters"]
        providers = data["providers"]
        scribes = data["scribes"]
        scribe_activity = data["scribe_activity"]
        diagnoses = data["diagnoses"]

    results = {}

    print("\n[KPIs] Computing monthly KPIs...")
    results["monthly_kpis"] = compute_monthly_kpis(encounters)
    print(f"  -> {len(results['monthly_kpis'])} months")

    print("[KPIs] Computing provider scorecard...")
    results["provider_scorecard"] = compute_provider_scorecard(encounters, providers)
    print(f"  -> {len(results['provider_scorecard'])} providers")

    print("[KPIs] Computing scribe leaderboard...")
    results["scribe_leaderboard"] = compute_scribe_leaderboard(scribe_activity, scribes)
    print(f"  -> {len(results['scribe_leaderboard'])} scribes")

    print("[KPIs] Computing specialty pivot...")
    results["specialty_pivot"] = compute_specialty_pivot(encounters, providers)
    print(f"  -> {results['specialty_pivot'].shape}")

    print("[KPIs] Computing SLA analysis...")
    results["sla_analysis"] = compute_sla_analysis(encounters, providers)
    print(f"  -> {len(results['sla_analysis'])} providers")

    print("[KPIs] Computing daily trends...")
    results["daily_trends"] = compute_daily_trends(encounters)
    print(f"  -> {len(results['daily_trends'])} days")

    print("[KPIs] Computing telehealth trends...")
    results["telehealth_trends"] = compute_telehealth_trends(encounters, providers)
    print(f"  -> {len(results['telehealth_trends'])} rows")

    print("[KPIs] Computing diagnosis distribution...")
    results["diagnosis_dist"] = compute_diagnosis_distribution(encounters, diagnoses)
    print(f"  -> {len(results['diagnosis_dist'])} diagnoses")

    print("[KPIs] Computing overall KPIs...")
    results["overall_kpis"] = compute_overall_kpis(encounters)
    print(f"  -> {results['overall_kpis']}")

    # Save key results
    print("\n[KPIs] Saving KPI results...")
    results["monthly_kpis"].to_csv(OUTPUT_DIR / "kpi_monthly.csv", index=False)
    results["provider_scorecard"].to_csv(OUTPUT_DIR / "kpi_provider_scorecard.csv", index=False)
    results["scribe_leaderboard"].to_csv(OUTPUT_DIR / "kpi_scribe_leaderboard.csv", index=False)
    results["daily_trends"].to_csv(OUTPUT_DIR / "kpi_daily_trends.csv", index=False)

    return results


if __name__ == "__main__":
    main()
