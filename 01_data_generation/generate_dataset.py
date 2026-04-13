"""
HealthFlow Analytics Dashboard — Data Generation
=================================================
Loads real Synthea healthcare data and augments it with synthetic
medical scribe columns (scribe activity, TAT, quality scores, audit log).

Real data source: Synthea Synthetic Patient Population
https://synthetichealth.github.io/synthea-sample-data/
"""

import os
import numpy as np
import pandas as pd
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
SYNTHEA_DIR = BASE_DIR / "synthea_raw"
OUTPUT_DIR = BASE_DIR / "output"

np.random.seed(42)

# ---------------------------------------------------------------------------
# Healthcare documentation domain mappings
# ---------------------------------------------------------------------------

SPECIALTY_TAT = {
    "General Practice": {"mean": 35, "std": 10},
    "Internal Medicine": {"mean": 40, "std": 12},
    "Cardiology":        {"mean": 55, "std": 14},
    "Orthopedics":       {"mean": 50, "std": 13},
    "Neurology":         {"mean": 52, "std": 13},
    "Dermatology":       {"mean": 30, "std": 8},
    "Pediatrics":        {"mean": 32, "std": 9},
    "Obstetrics":        {"mean": 45, "std": 11},
    "Other":             {"mean": 42, "std": 12},
}

SPECIALTY_QUALITY = {
    "General Practice": {"mean": 0.88, "std": 0.06},
    "Internal Medicine": {"mean": 0.87, "std": 0.07},
    "Cardiology":        {"mean": 0.84, "std": 0.08},
    "Orthopedics":       {"mean": 0.85, "std": 0.07},
    "Neurology":         {"mean": 0.83, "std": 0.08},
    "Dermatology":       {"mean": 0.90, "std": 0.05},
    "Pediatrics":        {"mean": 0.89, "std": 0.06},
    "Obstetrics":        {"mean": 0.86, "std": 0.07},
    "Other":             {"mean": 0.86, "std": 0.07},
}

ICD10_MAPPING = {
    "Hypertension":                "I10",
    "Diabetes":                    "E11",
    "Hyperlipidemia":              "E78",
    "Coronary Heart Disease":      "I25",
    "Atrial Fibrillation":         "I48",
    "Heart Failure":               "I50",
    "Chronic Obstructive":         "J44",
    "Asthma":                      "J45",
    "Acute bronchitis":            "J20",
    "Sinusitis":                   "J01",
    "Pharyngitis":                 "J02",
    "Viral sinusitis":             "J01",
    "Otitis media":                "H66",
    "Osteoarthritis":              "M19",
    "Low back pain":               "M54",
    "Fracture":                    "S42",
    "Laceration":                  "T14",
    "Sprain":                      "S93",
    "Migraine":                    "G43",
    "Seizure":                     "G40",
    "Stroke":                      "I63",
    "Anemia":                      "D64",
    "Anxiety":                     "F41",
    "Depression":                  "F32",
    "Obesity":                     "E66",
    "Urinary tract infection":     "N39",
    "Pneumonia":                   "J18",
    "Contact dermatitis":          "L25",
    "Eczema":                      "L30",
    "Pregnancy":                   "Z34",
    "Normal pregnancy":            "Z34",
    "Immunization":                "Z23",
    "General examination":         "Z00",
}

DIAGNOSIS_CATEGORIES = {
    "I10": "Chronic", "E11": "Chronic", "E78": "Chronic", "I25": "Chronic",
    "I48": "Chronic", "I50": "Chronic", "J44": "Chronic", "J45": "Chronic",
    "M19": "Chronic", "G43": "Chronic", "G40": "Chronic", "D64": "Chronic",
    "F41": "Chronic", "F32": "Chronic", "E66": "Chronic",
    "J20": "Acute", "J01": "Acute", "J02": "Acute", "H66": "Acute",
    "M54": "Acute", "S42": "Acute", "T14": "Acute", "S93": "Acute",
    "I63": "Acute", "N39": "Acute", "J18": "Acute", "L25": "Acute",
    "L30": "Acute",
    "Z23": "Preventive", "Z00": "Preventive", "Z34": "Preventive",
}


def map_specialty(raw_specialty):
    """Map Synthea specialty strings to clean categories."""
    if pd.isna(raw_specialty):
        return "Other"
    s = raw_specialty.lower()
    if "general" in s or "family" in s or "primary" in s:
        return "General Practice"
    if "internal" in s:
        return "Internal Medicine"
    if "cardio" in s or "heart" in s:
        return "Cardiology"
    if "ortho" in s or "bone" in s:
        return "Orthopedics"
    if "neuro" in s:
        return "Neurology"
    if "derma" in s or "skin" in s:
        return "Dermatology"
    if "pediat" in s:
        return "Pediatrics"
    if "obstet" in s or "gynec" in s:
        return "Obstetrics"
    return "Other"


def map_icd10(description):
    """Map encounter/condition description to ICD-10 code."""
    if pd.isna(description):
        return "Z00"
    desc = description.lower()
    for keyword, code in ICD10_MAPPING.items():
        if keyword.lower() in desc:
            return code
    if "well" in desc or "exam" in desc or "check" in desc:
        return "Z00"
    return "Z00"


def load_synthea():
    """Load core Synthea CSVs."""
    print("  Loading Synthea encounters...")
    encounters = pd.read_csv(SYNTHEA_DIR / "encounters.csv")
    print(f"    {len(encounters)} raw encounters")

    print("  Loading Synthea patients...")
    patients = pd.read_csv(SYNTHEA_DIR / "patients.csv")
    print(f"    {len(patients)} patients")

    print("  Loading Synthea providers...")
    providers = pd.read_csv(SYNTHEA_DIR / "providers.csv")
    print(f"    {len(providers)} providers")

    print("  Loading Synthea conditions...")
    conditions = pd.read_csv(SYNTHEA_DIR / "conditions.csv")
    print(f"    {len(conditions)} conditions")

    print("  Loading Synthea medications...")
    medications = pd.read_csv(SYNTHEA_DIR / "medications.csv")
    print(f"    {len(medications)} medications")

    return encounters, patients, providers, conditions, medications


def build_patients(raw_patients):
    """Build clean patients table from Synthea data."""
    df = raw_patients.copy()
    df["patient_id"] = range(1, len(df) + 1)
    df["name"] = df["FIRST"].str.strip() + " " + df["LAST"].str.strip()
    df["date_of_birth"] = pd.to_datetime(df["BIRTHDATE"])
    df["gender"] = df["GENDER"].str.capitalize()
    df["zip_code"] = df["ZIP"].astype(str)
    df["city"] = df["CITY"]
    df["state"] = df["STATE"]

    insurance_types = ["Private", "Medicare", "Medicaid", "Uninsured"]
    weights = [0.50, 0.25, 0.18, 0.07]
    df["insurance_type"] = np.random.choice(insurance_types, size=len(df), p=weights)

    df["registered_date"] = pd.to_datetime("2023-01-01") + pd.to_timedelta(
        np.random.randint(0, 365, size=len(df)), unit="D"
    )

    # UUID → int mapping for joins
    uuid_map = dict(zip(df["Id"], df["patient_id"]))

    result = df[["patient_id", "name", "date_of_birth", "gender",
                  "insurance_type", "registered_date", "zip_code",
                  "city", "state"]].copy()
    return result, uuid_map


def build_providers(raw_providers):
    """Build clean providers table from Synthea data. Keep top 20 by encounter count."""
    df = raw_providers.copy()
    df["encounter_count"] = pd.to_numeric(df["ENCOUNTERS"], errors="coerce").fillna(0)
    df = df.nlargest(20, "encounter_count").reset_index(drop=True)

    df["provider_id"] = range(101, 101 + len(df))
    df["name"] = "Dr. " + df["NAME"].str.strip()

    # Synthea sample only has "GENERAL PRACTICE" — assign realistic specialty mix
    specialty_assignments = [
        "General Practice", "General Practice", "General Practice", "General Practice",
        "Internal Medicine", "Internal Medicine", "Internal Medicine",
        "Cardiology", "Cardiology", "Cardiology",
        "Orthopedics", "Orthopedics",
        "Neurology", "Neurology",
        "Dermatology", "Dermatology",
        "Pediatrics", "Pediatrics",
        "Obstetrics", "Obstetrics",
    ]
    np.random.shuffle(specialty_assignments)
    df["specialty"] = specialty_assignments[:len(df)]

    dept_map = {
        "General Practice": "Primary Care",
        "Internal Medicine": "Internal Medicine",
        "Cardiology": "Heart Center",
        "Orthopedics": "Musculoskeletal",
        "Neurology": "Neuro Center",
        "Dermatology": "Skin & Allergy",
        "Pediatrics": "Pediatrics",
        "Obstetrics": "Women's Health",
        "Other": "General",
    }
    df["department"] = df["specialty"].map(dept_map)
    df["hire_date"] = pd.to_datetime("2018-01-01") + pd.to_timedelta(
        np.random.randint(0, 1800, size=len(df)), unit="D"
    )

    uuid_map = dict(zip(df["Id"], df["provider_id"]))

    result = df[["provider_id", "name", "specialty", "department", "hire_date"]].copy()
    return result, uuid_map


def build_scribes(n=10):
    """Generate synthetic scribe data."""
    scribe_names = [
        "Ayesha Khan", "Tanvir Hossain", "Nusrat Jahan", "Farhan Ahmed",
        "Sadia Rahman", "Imran Ali", "Tasnim Akter", "Rafiq Islam",
        "Maliha Sultana", "Karim Uddin"
    ]
    shifts = ["Morning", "Afternoon", "Evening"]
    shift_assign = [shifts[i % 3] for i in range(n)]
    experience = np.random.randint(1, 37, size=n)

    return pd.DataFrame({
        "scribe_id": range(201, 201 + n),
        "name": scribe_names[:n],
        "experience_months": experience,
        "shift": shift_assign,
        "hire_date": pd.to_datetime("2023-06-01") - pd.to_timedelta(
            experience * 30, unit="D"
        ),
    })


def build_encounters(raw_encounters, patient_map, provider_map, providers_df,
                     raw_conditions):
    """
    Build encounters table from Synthea data.
    - Filter to recent 1500 encounters
    - Map patient/provider UUIDs to integer IDs
    - Add documentation-specific columns: TAT, quality, notes_status, ICD codes
    """
    df = raw_encounters.copy()
    df["encounter_date"] = pd.to_datetime(df["START"])

    # Filter to encounters with known patients and providers
    df = df[df["PATIENT"].isin(patient_map) & df["PROVIDER"].isin(provider_map)]

    # Take most recent 1500
    df = df.nlargest(1500, "encounter_date").reset_index(drop=True)
    print(f"    Selected {len(df)} encounters after filtering")

    df["encounter_id"] = range(1001, 1001 + len(df))
    df["patient_id"] = df["PATIENT"].map(patient_map)
    df["provider_id"] = df["PROVIDER"].map(provider_map)

    # Map encounter class to type
    telehealth_classes = {"virtual", "telehealth", "phone"}
    df["encounter_type"] = df["ENCOUNTERCLASS"].apply(
        lambda x: "Telehealth" if str(x).lower() in telehealth_classes else "In-Person"
    )

    # Increase telehealth ratio over time (simulate adoption trend)
    months = df["encounter_date"].dt.month
    for idx in df.index:
        m = months[idx]
        telehealth_prob = 0.25 + 0.03 * m  # ~25% in Jan to ~43% in Jun
        if df.at[idx, "encounter_type"] == "In-Person" and np.random.random() < telehealth_prob * 0.3:
            df.at[idx, "encounter_type"] = "Telehealth"

    # Map ICD-10 codes from reason descriptions
    condition_map = {}
    for _, row in raw_conditions.iterrows():
        enc_id = row.get("ENCOUNTER")
        if pd.notna(enc_id):
            condition_map[enc_id] = row.get("DESCRIPTION", "")

    df["_reason"] = df["Id"].map(condition_map).fillna(df["REASONDESCRIPTION"]).fillna(df["DESCRIPTION"])
    df["diagnosis_code"] = df["_reason"].apply(map_icd10)

    # CPT codes based on encounter class
    cpt_map = {
        "wellness": "99395", "ambulatory": "99214", "outpatient": "99213",
        "inpatient": "99223", "emergency": "99285", "urgentcare": "99214",
    }
    df["procedure_code"] = df["ENCOUNTERCLASS"].map(cpt_map).fillna("99213")

    # Merge specialty for TAT/quality generation
    df = df.merge(providers_df[["provider_id", "specialty"]], on="provider_id", how="left")

    # Generate TAT based on specialty
    def gen_tat(specialty):
        params = SPECIALTY_TAT.get(specialty, SPECIALTY_TAT["Other"])
        return max(15, min(120, int(np.random.normal(params["mean"], params["std"]))))
    df["note_turnaround_minutes"] = df["specialty"].apply(gen_tat)

    # Generate quality scores based on specialty
    def gen_quality(specialty):
        params = SPECIALTY_QUALITY.get(specialty, SPECIALTY_QUALITY["Other"])
        return round(max(0.60, min(1.00, np.random.normal(params["mean"], params["std"]))), 2)
    df["note_quality_score"] = df["specialty"].apply(gen_quality)

    # Notes status distribution
    status_choices = ["Completed", "Completed", "Completed", "Completed",
                      "Completed", "Completed", "Reviewed", "Draft", "Pending"]
    df["notes_status"] = np.random.choice(status_choices, size=len(df))

    # Store original encounter UUID for scribe activity linking
    uuid_map = dict(zip(df["Id"], df["encounter_id"]))

    result = df[["encounter_id", "patient_id", "provider_id", "encounter_date",
                  "encounter_type", "diagnosis_code", "procedure_code",
                  "notes_status", "note_turnaround_minutes", "note_quality_score"]].copy()

    return result, uuid_map


def build_diagnoses():
    """Build diagnosis reference table from our ICD-10 mapping."""
    rows = []
    seen = set()
    for desc, code in ICD10_MAPPING.items():
        if code not in seen:
            seen.add(code)
            rows.append({
                "diagnosis_id": len(rows) + 1,
                "icd_code": code,
                "description": desc,
                "category": DIAGNOSIS_CATEGORIES.get(code, "Other"),
            })
    return pd.DataFrame(rows)


def build_prescriptions(encounters_df, raw_medications, patient_map, encounter_uuid_map):
    """Build prescriptions from Synthea medications data."""
    df = raw_medications.copy()

    # Filter to encounters we kept
    df = df[df["ENCOUNTER"].isin(encounter_uuid_map)]
    df = df.head(500).reset_index(drop=True)

    df["prescription_id"] = range(1, len(df) + 1)
    df["encounter_id"] = df["ENCOUNTER"].map(encounter_uuid_map)
    df["patient_id"] = df["PATIENT"].map(patient_map)
    df["medication_name"] = df["DESCRIPTION"].str[:80]
    df["dosage"] = "Standard dose"
    df["prescribed_date"] = pd.to_datetime(df["START"]).dt.date
    df["duration_days"] = np.random.choice([7, 10, 14, 30, 60, 90], size=len(df),
                                            p=[0.10, 0.10, 0.15, 0.30, 0.15, 0.20])

    result = df[["prescription_id", "encounter_id", "patient_id",
                  "medication_name", "dosage", "prescribed_date", "duration_days"]].copy()
    result = result.dropna(subset=["encounter_id", "patient_id"])
    result["encounter_id"] = result["encounter_id"].astype(int)
    result["patient_id"] = result["patient_id"].astype(int)
    return result


def build_scribe_activity(encounters_df, scribes_df):
    """Generate scribe activity records for completed/reviewed encounters."""
    completed = encounters_df[
        encounters_df["notes_status"].isin(["Completed", "Reviewed"])
    ].copy()

    scribe_ids = scribes_df["scribe_id"].tolist()
    experience = dict(zip(scribes_df["scribe_id"], scribes_df["experience_months"]))

    rows = []
    for i, (_, enc) in enumerate(completed.iterrows()):
        sid = scribe_ids[i % len(scribe_ids)]
        exp_factor = experience[sid] / 36.0  # Normalize 0-1

        start = enc["encounter_date"]
        tat = enc["note_turnaround_minutes"]
        noise = np.random.randint(-5, 10)
        duration = max(10, tat + noise)
        end = start + pd.Timedelta(minutes=duration)

        # More experienced scribes → fewer edits, higher quality
        base_edits = max(1, int(np.random.normal(6 - 3 * exp_factor, 2)))
        quality = round(min(1.0, max(0.60,
            enc["note_quality_score"] + np.random.normal(0.02 * exp_factor, 0.03)
        )), 2)

        rows.append({
            "activity_id": i + 1,
            "scribe_id": sid,
            "encounter_id": enc["encounter_id"],
            "start_time": start,
            "end_time": end,
            "edits_count": base_edits,
            "quality_score": quality,
        })

    return pd.DataFrame(rows)


def build_quality_audit_log(encounters_df, n_audits=150):
    """Generate synthetic QA audit records."""
    completed = encounters_df[
        encounters_df["notes_status"].isin(["Completed", "Reviewed"])
    ]
    audited = completed.sample(n=min(n_audits, len(completed)), random_state=42)

    finding_categories = [
        "Missing HPI Details", "Incomplete ROS", "Wrong ICD Code",
        "Missing Medication", "Incomplete Assessment", "Format Error",
        "Missing Follow-up", "Incorrect Vitals"
    ]

    rows = []
    for i, (_, enc) in enumerate(audited.iterrows()):
        original = enc["note_quality_score"]
        # Some audits find issues (score revised down), some confirm (revised up slightly)
        if np.random.random() < 0.6:
            delta = round(np.random.uniform(-0.15, -0.02), 2)
        else:
            delta = round(np.random.uniform(0.00, 0.05), 2)
        revised = round(max(0.50, min(1.00, original + delta)), 2)

        rows.append({
            "audit_id": i + 1,
            "encounter_id": enc["encounter_id"],
            "auditor_id": np.random.randint(301, 306),
            "original_score": original,
            "revised_score": revised,
            "audit_date": enc["encounter_date"].date() + pd.Timedelta(days=np.random.randint(1, 7)),
            "finding_category": np.random.choice(finding_categories),
        })

    return pd.DataFrame(rows)


def inject_messiness(encounters_df):
    """Inject controlled data quality issues for the cleaning step to fix."""
    df = encounters_df.copy()
    n = len(df)

    # ~3% null quality scores
    null_quality_idx = np.random.choice(n, size=int(n * 0.03), replace=False)
    df.loc[df.index[null_quality_idx], "note_quality_score"] = np.nan

    # ~2% null TAT
    null_tat_idx = np.random.choice(n, size=int(n * 0.02), replace=False)
    df.loc[df.index[null_tat_idx], "note_turnaround_minutes"] = np.nan

    # ~1% inconsistent casing in encounter_type
    case_idx = np.random.choice(n, size=int(n * 0.01), replace=False)
    df.loc[df.index[case_idx], "encounter_type"] = df.loc[
        df.index[case_idx], "encounter_type"
    ].str.lower()

    # 5 near-duplicate rows (same patient+provider+date, new encounter_id)
    dupes = df.sample(5, random_state=99).copy()
    dupes["encounter_id"] = range(df["encounter_id"].max() + 1,
                                   df["encounter_id"].max() + 6)
    df = pd.concat([df, dupes], ignore_index=True)

    # 3 impossible TAT values
    bad_idx = np.random.choice(len(df), size=3, replace=False)
    df.loc[df.index[bad_idx[0]], "note_turnaround_minutes"] = -15
    df.loc[df.index[bad_idx[1]], "note_turnaround_minutes"] = 350
    df.loc[df.index[bad_idx[2]], "note_turnaround_minutes"] = 400

    return df


def main():
    """Generate complete dataset from Synthea + synthetic HealthFlow layer."""
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    print("\n[Step 1] Loading Synthea data...")
    raw_enc, raw_pat, raw_prov, raw_cond, raw_med = load_synthea()

    print("\n[Step 2] Building patients table...")
    patients_df, patient_map = build_patients(raw_pat)
    print(f"  -> {len(patients_df)} patients")

    print("\n[Step 3] Building providers table (top 20)...")
    providers_df, provider_map = build_providers(raw_prov)
    print(f"  -> {len(providers_df)} providers")

    print("\n[Step 4] Building scribes table...")
    scribes_df = build_scribes(10)
    print(f"  -> {len(scribes_df)} scribes")

    print("\n[Step 5] Building encounters table (1500 from Synthea)...")
    encounters_df, enc_uuid_map = build_encounters(
        raw_enc, patient_map, provider_map, providers_df, raw_cond
    )
    print(f"  -> {len(encounters_df)} encounters")

    print("\n[Step 6] Building diagnoses reference table...")
    diagnoses_df = build_diagnoses()
    print(f"  -> {len(diagnoses_df)} diagnosis codes")

    print("\n[Step 7] Building prescriptions from Synthea medications...")
    prescriptions_df = build_prescriptions(encounters_df, raw_med, patient_map, enc_uuid_map)
    print(f"  -> {len(prescriptions_df)} prescriptions")

    print("\n[Step 8] Building scribe activity records...")
    scribe_activity_df = build_scribe_activity(encounters_df, scribes_df)
    print(f"  -> {len(scribe_activity_df)} scribe activity records")

    print("\n[Step 9] Building quality audit log...")
    audit_log_df = build_quality_audit_log(encounters_df)
    print(f"  -> {len(audit_log_df)} audit records")

    print("\n[Step 10] Injecting controlled messiness into encounters...")
    encounters_messy = inject_messiness(encounters_df)
    print(f"  -> {len(encounters_messy)} encounters (with {len(encounters_messy) - len(encounters_df)} duplicates + dirty data)")

    # Save all CSVs
    print("\n[Step 11] Saving CSVs to output/...")
    patients_df.to_csv(OUTPUT_DIR / "raw_patients.csv", index=False)
    providers_df.to_csv(OUTPUT_DIR / "raw_providers.csv", index=False)
    scribes_df.to_csv(OUTPUT_DIR / "raw_scribes.csv", index=False)
    encounters_messy.to_csv(OUTPUT_DIR / "raw_encounters.csv", index=False)
    diagnoses_df.to_csv(OUTPUT_DIR / "raw_diagnoses.csv", index=False)
    prescriptions_df.to_csv(OUTPUT_DIR / "raw_prescriptions.csv", index=False)
    scribe_activity_df.to_csv(OUTPUT_DIR / "raw_scribe_activity.csv", index=False)
    audit_log_df.to_csv(OUTPUT_DIR / "raw_quality_audit_log.csv", index=False)

    # Also save clean encounters (pre-messiness) for reference
    encounters_df.to_csv(OUTPUT_DIR / "reference_clean_encounters.csv", index=False)

    print("\n  Saved files:")
    for f in sorted(OUTPUT_DIR.glob("raw_*.csv")):
        size = f.stat().st_size / 1024
        print(f"    {f.name}: {size:.1f} KB")

    return {
        "patients": patients_df,
        "providers": providers_df,
        "scribes": scribes_df,
        "encounters": encounters_df,
        "encounters_messy": encounters_messy,
        "diagnoses": diagnoses_df,
        "prescriptions": prescriptions_df,
        "scribe_activity": scribe_activity_df,
        "quality_audit_log": audit_log_df,
    }


if __name__ == "__main__":
    main()
