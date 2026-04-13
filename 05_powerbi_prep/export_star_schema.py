"""
HealthFlow Analytics — Power BI Star Schema Export
==================================================
Exports data as a dimensional model (star schema) for Power BI import.
Creates dimension and fact tables as CSVs.
"""

import pandas as pd
import numpy as np
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
OUTPUT_DIR = BASE_DIR / "output"
PBI_DIR = OUTPUT_DIR / "powerbi"


def build_dim_dates(start_date, end_date):
    """Generate a complete date dimension table."""
    dates = pd.date_range(start=start_date, end=end_date, freq="D")
    dim = pd.DataFrame({
        "date_key": dates.strftime("%Y%m%d").astype(int),
        "full_date": dates.date,
        "year": dates.year,
        "quarter": dates.quarter,
        "month_num": dates.month,
        "month_name": dates.month_name(),
        "week_of_year": dates.isocalendar().week.astype(int),
        "day_of_week": dates.dayofweek,
        "day_name": dates.day_name(),
        "is_weekend": dates.dayofweek >= 5,
        "is_month_start": dates.is_month_start,
        "is_month_end": dates.is_month_end,
    })
    return dim


def build_dim_providers(providers_df):
    """Dimension: Providers."""
    return providers_df[["provider_id", "name", "specialty", "department"]].copy()


def build_dim_patients(patients_df):
    """Dimension: Patients with derived age group."""
    df = patients_df.copy()
    today = pd.Timestamp("2025-06-30")
    df["date_of_birth"] = pd.to_datetime(df["date_of_birth"])
    df["age"] = ((today - df["date_of_birth"]).dt.days / 365.25).astype(int)
    df["age_group"] = pd.cut(df["age"], bins=[0, 17, 40, 65, 120],
                              labels=["0-17", "18-40", "41-65", "65+"])
    return df[["patient_id", "name", "gender", "insurance_type",
               "age", "age_group", "city", "state"]].copy()


def build_dim_diagnoses(diagnoses_df):
    """Dimension: Diagnoses."""
    return diagnoses_df[["icd_code", "description", "category"]].copy()


def build_dim_scribes(scribes_df):
    """Dimension: Scribes with experience tier."""
    df = scribes_df.copy()
    df["experience_tier"] = pd.cut(df["experience_months"],
                                     bins=[0, 6, 18, 100],
                                     labels=["Junior", "Mid", "Senior"])
    return df[["scribe_id", "name", "experience_months", "shift",
               "experience_tier"]].copy()


def build_fact_encounters(encounters_df, providers_df):
    """Fact table: Encounters with foreign keys and SLA flag."""
    SLA_TARGETS = {
        "General Practice": 40, "Internal Medicine": 45, "Cardiology": 60,
        "Orthopedics": 55, "Neurology": 55, "Dermatology": 35,
        "Pediatrics": 38, "Obstetrics": 50, "Other": 45,
    }

    df = encounters_df.copy()
    df["encounter_date"] = pd.to_datetime(df["encounter_date"])
    df["date_key"] = df["encounter_date"].dt.strftime("%Y%m%d").astype(int)

    # Add SLA met flag
    df = df.merge(providers_df[["provider_id", "specialty"]], on="provider_id", how="left")
    df["target_tat"] = df["specialty"].map(SLA_TARGETS).fillna(45)
    df["sla_met"] = df["note_turnaround_minutes"] <= df["target_tat"]
    df = df.drop(columns=["specialty", "target_tat"])

    return df[["encounter_id", "date_key", "patient_id", "provider_id",
               "diagnosis_code", "encounter_type", "notes_status",
               "note_turnaround_minutes", "note_quality_score", "sla_met"]].copy()


def build_fact_scribe_activity(scribe_activity_df):
    """Fact table: Scribe activity with date key."""
    df = scribe_activity_df.copy()
    df["start_time"] = pd.to_datetime(df["start_time"])
    df["date_key"] = df["start_time"].dt.strftime("%Y%m%d").astype(int)
    df["duration_minutes"] = (
        (pd.to_datetime(df["end_time"]) - df["start_time"]).dt.total_seconds() / 60
    ).round(1)

    return df[["activity_id", "encounter_id", "scribe_id", "date_key",
               "duration_minutes", "edits_count", "quality_score"]].copy()


def main(data=None):
    """Export all star schema tables."""
    PBI_DIR.mkdir(parents=True, exist_ok=True)

    if data is None:
        print("\n[Power BI] Loading data...")
        encounters = pd.read_csv(OUTPUT_DIR / "cleaned_encounters.csv")
        patients = pd.read_csv(OUTPUT_DIR / "raw_patients.csv")
        providers = pd.read_csv(OUTPUT_DIR / "raw_providers.csv")
        scribes = pd.read_csv(OUTPUT_DIR / "raw_scribes.csv")
        diagnoses = pd.read_csv(OUTPUT_DIR / "raw_diagnoses.csv")
        scribe_activity = pd.read_csv(OUTPUT_DIR / "raw_scribe_activity.csv")
    else:
        encounters = data["encounters"]
        patients = data["patients"]
        providers = data["providers"]
        scribes = data["scribes"]
        diagnoses = data["diagnoses"]
        scribe_activity = data["scribe_activity"]

    print("\n[Power BI] Building dimension tables...")

    enc_dates = pd.to_datetime(encounters["encounter_date"])
    dim_dates = build_dim_dates(enc_dates.min(), enc_dates.max())
    dim_dates.to_csv(PBI_DIR / "dim_dates.csv", index=False)
    print(f"  dim_dates: {len(dim_dates)} rows")

    dim_providers = build_dim_providers(providers)
    dim_providers.to_csv(PBI_DIR / "dim_providers.csv", index=False)
    print(f"  dim_providers: {len(dim_providers)} rows")

    dim_patients = build_dim_patients(patients)
    dim_patients.to_csv(PBI_DIR / "dim_patients.csv", index=False)
    print(f"  dim_patients: {len(dim_patients)} rows")

    dim_diagnoses = build_dim_diagnoses(diagnoses)
    dim_diagnoses.to_csv(PBI_DIR / "dim_diagnoses.csv", index=False)
    print(f"  dim_diagnoses: {len(dim_diagnoses)} rows")

    dim_scribes = build_dim_scribes(scribes)
    dim_scribes.to_csv(PBI_DIR / "dim_scribes.csv", index=False)
    print(f"  dim_scribes: {len(dim_scribes)} rows")

    print("\n[Power BI] Building fact tables...")

    fact_encounters = build_fact_encounters(encounters, providers)
    fact_encounters.to_csv(PBI_DIR / "fact_encounters.csv", index=False)
    print(f"  fact_encounters: {len(fact_encounters)} rows")

    fact_scribe = build_fact_scribe_activity(scribe_activity)
    fact_scribe.to_csv(PBI_DIR / "fact_scribe_activity.csv", index=False)
    print(f"  fact_scribe_activity: {len(fact_scribe)} rows")

    print(f"\n[Power BI] Star schema exported to {PBI_DIR}/")
    print(f"  Total files: {len(list(PBI_DIR.glob('*.csv')))}")

    return PBI_DIR


if __name__ == "__main__":
    main()
