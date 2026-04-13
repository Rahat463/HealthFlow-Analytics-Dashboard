"""
HealthFlow Analytics — Data Cleaning Pipeline
=============================================
Loads messy raw CSVs, audits quality, cleans systematically,
and outputs clean datasets ready for analysis.
"""

import pandas as pd
import numpy as np
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
OUTPUT_DIR = BASE_DIR / "output"


def load_raw_data():
    """Load all raw CSVs into a dict of DataFrames."""
    files = {
        "encounters":        "raw_encounters.csv",
        "patients":          "raw_patients.csv",
        "providers":         "raw_providers.csv",
        "scribes":           "raw_scribes.csv",
        "diagnoses":         "raw_diagnoses.csv",
        "prescriptions":     "raw_prescriptions.csv",
        "scribe_activity":   "raw_scribe_activity.csv",
        "quality_audit_log": "raw_quality_audit_log.csv",
    }
    data = {}
    for name, filename in files.items():
        df = pd.read_csv(OUTPUT_DIR / filename)
        data[name] = df
        print(f"  {name}: {df.shape[0]} rows x {df.shape[1]} cols")
    return data


def audit_data_quality(df, name):
    """Generate a data quality report for a DataFrame."""
    report = {"table": name, "total_rows": len(df)}

    # Null counts
    null_counts = df.isnull().sum()
    report["null_columns"] = {col: int(cnt) for col, cnt in null_counts.items() if cnt > 0}
    report["total_nulls"] = int(null_counts.sum())

    # Duplicates
    report["duplicate_rows"] = int(df.duplicated().sum())

    print(f"\n  Quality audit for '{name}':")
    print(f"    Rows: {report['total_rows']}")
    print(f"    Total nulls: {report['total_nulls']}")
    if report["null_columns"]:
        for col, cnt in report["null_columns"].items():
            print(f"      - {col}: {cnt} nulls ({100*cnt/len(df):.1f}%)")
    print(f"    Duplicate rows: {report['duplicate_rows']}")

    return report


def clean_encounters(encounters_df, providers_df):
    """
    Clean encounters with systematic steps:
    1. Fix inconsistent casing
    2. Remove true duplicates
    3. Remove impossible values
    4. Fill missing quality with provider-level median
    5. Fill missing TAT with specialty-level median
    6. Add derived date columns
    """
    df = encounters_df.copy()
    log = []
    initial_count = len(df)

    # Step 1: Fix inconsistent casing in encounter_type
    before_types = df["encounter_type"].unique()
    df["encounter_type"] = df["encounter_type"].str.strip().str.title()
    after_types = df["encounter_type"].unique()
    fixed_casing = len(before_types) - len(after_types)
    log.append({"step": "Fix casing", "detail": f"Standardized encounter_type values",
                "rows_affected": int((encounters_df["encounter_type"] != df["encounter_type"]).sum())})
    print(f"    [1] Fixed casing: {log[-1]['rows_affected']} rows")

    # Step 2: Remove true duplicates (same patient+provider+date, keep lowest encounter_id)
    df["encounter_date"] = pd.to_datetime(df["encounter_date"])
    df["_date_only"] = df["encounter_date"].dt.date
    before_dedup = len(df)
    df = df.sort_values("encounter_id").drop_duplicates(
        subset=["patient_id", "provider_id", "_date_only"], keep="first"
    )
    removed_dupes = before_dedup - len(df)
    df = df.drop(columns=["_date_only"])
    log.append({"step": "Remove duplicates", "detail": f"Removed {removed_dupes} duplicate encounters",
                "rows_affected": removed_dupes})
    print(f"    [2] Removed duplicates: {removed_dupes} rows")

    # Step 3: Remove impossible TAT values (negative or > 300)
    bad_tat_mask = (df["note_turnaround_minutes"] < 0) | (df["note_turnaround_minutes"] > 300)
    bad_tat_count = bad_tat_mask.sum()
    df.loc[bad_tat_mask, "note_turnaround_minutes"] = np.nan
    log.append({"step": "Remove bad TAT", "detail": f"Set {bad_tat_count} impossible TAT values to NaN",
                "rows_affected": int(bad_tat_count)})
    print(f"    [3] Flagged bad TAT: {bad_tat_count} rows set to NaN")

    # Step 4: Fill missing quality_score with provider-level median
    null_quality_before = df["note_quality_score"].isnull().sum()
    provider_median_quality = df.groupby("provider_id")["note_quality_score"].transform("median")
    df["note_quality_score"] = df["note_quality_score"].fillna(provider_median_quality)
    # If still null (provider has no quality data), use global median
    global_median_quality = df["note_quality_score"].median()
    df["note_quality_score"] = df["note_quality_score"].fillna(global_median_quality)
    null_quality_after = df["note_quality_score"].isnull().sum()
    filled_quality = null_quality_before - null_quality_after
    log.append({"step": "Fill quality nulls", "detail": f"Filled {filled_quality} nulls with provider median",
                "rows_affected": int(filled_quality)})
    print(f"    [4] Filled quality nulls: {filled_quality} (provider median)")

    # Step 5: Fill missing TAT with specialty-level median
    null_tat_before = df["note_turnaround_minutes"].isnull().sum()
    df = df.merge(providers_df[["provider_id", "specialty"]], on="provider_id", how="left")
    specialty_median_tat = df.groupby("specialty")["note_turnaround_minutes"].transform("median")
    df["note_turnaround_minutes"] = df["note_turnaround_minutes"].fillna(specialty_median_tat)
    global_median_tat = df["note_turnaround_minutes"].median()
    df["note_turnaround_minutes"] = df["note_turnaround_minutes"].fillna(global_median_tat)
    null_tat_after = df["note_turnaround_minutes"].isnull().sum()
    filled_tat = null_tat_before - null_tat_after
    df = df.drop(columns=["specialty"])
    log.append({"step": "Fill TAT nulls", "detail": f"Filled {filled_tat} nulls with specialty median",
                "rows_affected": int(filled_tat)})
    print(f"    [5] Filled TAT nulls: {filled_tat} (specialty median)")

    # Step 6: Add derived date columns
    df["month"] = df["encounter_date"].dt.to_period("M").astype(str)
    df["day_of_week"] = df["encounter_date"].dt.day_name()
    df["is_weekend"] = df["encounter_date"].dt.dayofweek >= 5
    df["hour"] = df["encounter_date"].dt.hour

    final_count = len(df)
    log.append({"step": "Final", "detail": f"Cleaned {initial_count} -> {final_count} rows",
                "rows_affected": initial_count - final_count})
    print(f"    [Final] {initial_count} -> {final_count} rows ({initial_count - final_count} removed)")

    cleaning_log = pd.DataFrame(log)
    return df, cleaning_log


def validate_referential_integrity(data):
    """Check that all foreign keys match."""
    issues = []

    enc = data["encounters"]
    pat_ids = set(data["patients"]["patient_id"])
    prov_ids = set(data["providers"]["provider_id"])

    orphan_patients = enc[~enc["patient_id"].isin(pat_ids)]
    if len(orphan_patients) > 0:
        issues.append(f"  {len(orphan_patients)} encounters with unknown patient_id")

    orphan_providers = enc[~enc["provider_id"].isin(prov_ids)]
    if len(orphan_providers) > 0:
        issues.append(f"  {len(orphan_providers)} encounters with unknown provider_id")

    sa = data["scribe_activity"]
    enc_ids = set(enc["encounter_id"])
    orphan_encounters = sa[~sa["encounter_id"].isin(enc_ids)]
    if len(orphan_encounters) > 0:
        issues.append(f"  {len(orphan_encounters)} scribe activities with unknown encounter_id")

    if issues:
        print("\n  Referential integrity issues:")
        for issue in issues:
            print(f"    {issue}")
    else:
        print("\n  Referential integrity: ALL OK")

    return issues


def main():
    """Run the full cleaning pipeline."""
    print("\n[Cleaning] Loading raw data...")
    data = load_raw_data()

    print("\n[Cleaning] Auditing data quality...")
    reports = {}
    for name, df in data.items():
        reports[name] = audit_data_quality(df, name)

    print("\n[Cleaning] Cleaning encounters...")
    cleaned_encounters, cleaning_log = clean_encounters(
        data["encounters"], data["providers"]
    )

    print("\n[Cleaning] Validating referential integrity...")
    data["encounters"] = cleaned_encounters
    validate_referential_integrity(data)

    # Save cleaned data
    print("\n[Cleaning] Saving cleaned data...")
    cleaned_encounters.to_csv(OUTPUT_DIR / "cleaned_encounters.csv", index=False)
    cleaning_log.to_csv(OUTPUT_DIR / "cleaning_report.csv", index=False)
    print(f"  saved cleaned_encounters.csv: {len(cleaned_encounters)} rows")
    print(f"  saved cleaning_report.csv: {len(cleaning_log)} steps")

    # Return for pipeline use
    data["encounters"] = cleaned_encounters
    data["cleaning_log"] = cleaning_log
    return data


if __name__ == "__main__":
    main()
