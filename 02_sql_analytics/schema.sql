-- =============================================================
-- HealthFlow Analytics Dashboard — Database Schema
-- 8 tables modeling healthcare documentation workflow
-- Compatible with: SQLite, PostgreSQL
-- =============================================================

DROP TABLE IF EXISTS quality_audit_log;
DROP TABLE IF EXISTS scribe_activity;
DROP TABLE IF EXISTS prescriptions;
DROP TABLE IF EXISTS encounters;
DROP TABLE IF EXISTS scribes;
DROP TABLE IF EXISTS diagnoses;
DROP TABLE IF EXISTS providers;
DROP TABLE IF EXISTS patients;

-- 1. Patients
CREATE TABLE patients (
    patient_id      INTEGER PRIMARY KEY,
    name            TEXT NOT NULL,
    date_of_birth   DATE,
    gender          TEXT,           -- 'Male','Female'
    insurance_type  TEXT,           -- 'Private','Medicare','Medicaid','Uninsured'
    registered_date DATE,
    zip_code        TEXT,
    city            TEXT,
    state           TEXT
);

-- 2. Providers (physicians)
CREATE TABLE providers (
    provider_id     INTEGER PRIMARY KEY,
    name            TEXT NOT NULL,
    specialty       TEXT,           -- 'Cardiology','General Practice','Internal Medicine', etc.
    department      TEXT,
    hire_date       DATE
);

-- 3. Scribes (medical documentation specialists)
CREATE TABLE scribes (
    scribe_id           INTEGER PRIMARY KEY,
    name                TEXT NOT NULL,
    experience_months   INTEGER,
    shift               TEXT,       -- 'Morning','Afternoon','Evening'
    hire_date           DATE
);

-- 4. Diagnoses (ICD-10 reference table)
CREATE TABLE diagnoses (
    diagnosis_id    INTEGER PRIMARY KEY,
    icd_code        TEXT UNIQUE,
    description     TEXT,
    category        TEXT            -- 'Chronic','Acute','Preventive'
);

-- 5. Encounters (core fact table)
CREATE TABLE encounters (
    encounter_id            INTEGER PRIMARY KEY,
    patient_id              INTEGER REFERENCES patients(patient_id),
    provider_id             INTEGER REFERENCES providers(provider_id),
    encounter_date          DATETIME,
    encounter_type          TEXT,    -- 'In-Person','Telehealth'
    diagnosis_code          TEXT,    -- ICD-10 code
    procedure_code          TEXT,    -- CPT code
    notes_status            TEXT,    -- 'Draft','Completed','Reviewed','Pending'
    note_turnaround_minutes REAL,   -- time to complete documentation (TAT)
    note_quality_score      REAL    -- 0.00 to 1.00 (NQS)
);

-- 6. Prescriptions
CREATE TABLE prescriptions (
    prescription_id INTEGER PRIMARY KEY,
    encounter_id    INTEGER REFERENCES encounters(encounter_id),
    patient_id      INTEGER REFERENCES patients(patient_id),
    medication_name TEXT,
    dosage          TEXT,
    prescribed_date DATE,
    duration_days   INTEGER
);

-- 7. Scribe Activity (one row per completed encounter)
CREATE TABLE scribe_activity (
    activity_id     INTEGER PRIMARY KEY,
    scribe_id       INTEGER REFERENCES scribes(scribe_id),
    encounter_id    INTEGER REFERENCES encounters(encounter_id),
    start_time      DATETIME,
    end_time        DATETIME,
    edits_count     INTEGER,
    quality_score   REAL
);

-- 8. Quality Audit Log (QA review records)
CREATE TABLE quality_audit_log (
    audit_id            INTEGER PRIMARY KEY,
    encounter_id        INTEGER REFERENCES encounters(encounter_id),
    auditor_id          INTEGER,
    original_score      REAL,
    revised_score       REAL,
    audit_date          DATE,
    finding_category    TEXT        -- 'Missing HPI Details','Incomplete ROS', etc.
);
