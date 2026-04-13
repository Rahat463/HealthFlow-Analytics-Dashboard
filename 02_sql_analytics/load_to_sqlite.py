"""
HealthFlow Analytics — SQLite Database Loader
=============================================
Creates a SQLite database from generated CSVs and runs all 10 KPI queries.
"""

import sqlite3
import pandas as pd
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
OUTPUT_DIR = BASE_DIR / "output"
SQL_DIR = Path(__file__).resolve().parent
DB_PATH = OUTPUT_DIR / "healthflow.db"


def create_database():
    """Create SQLite database and load schema."""
    DB_PATH.unlink(missing_ok=True)
    conn = sqlite3.connect(DB_PATH)

    schema_sql = (SQL_DIR / "schema.sql").read_text()
    conn.executescript(schema_sql)
    print(f"  Created database at {DB_PATH}")
    return conn


def load_data(conn):
    """Load cleaned CSVs into SQLite tables."""
    tables = {
        "patients":          "raw_patients.csv",
        "providers":         "raw_providers.csv",
        "scribes":           "raw_scribes.csv",
        "diagnoses":         "raw_diagnoses.csv",
        "encounters":        "reference_clean_encounters.csv",  # Use clean version for DB
        "prescriptions":     "raw_prescriptions.csv",
        "scribe_activity":   "raw_scribe_activity.csv",
        "quality_audit_log": "raw_quality_audit_log.csv",
    }

    for table, csv_file in tables.items():
        csv_path = OUTPUT_DIR / csv_file
        if csv_path.exists():
            df = pd.read_csv(csv_path)
            df.to_sql(table, conn, if_exists="replace", index=False)
            print(f"  Loaded {table}: {len(df)} rows")
        else:
            print(f"  WARNING: {csv_file} not found, skipping {table}")

    conn.commit()


def run_kpi_queries(conn):
    """Execute all 10 KPI queries and print results."""
    kpi_sql = (SQL_DIR / "kpi_queries.sql").read_text()

    # Split on the Q-number header pattern to get each query block
    import re
    # Each query starts with a block like:
    # -- =============================================
    # -- Q1: EXECUTIVE SUMMARY KPIs
    blocks = re.split(r'(?=-- =====+\n-- Q\d+:)', kpi_sql)
    queries = []
    for block in blocks:
        block = block.strip()
        if not block or '-- Q' not in block[:200]:
            continue
        # Extract only up to the final semicolon (strip trailing comments)
        last_semi = block.rfind(';')
        if last_semi == -1:
            continue
        sql = block[:last_semi + 1]
        queries.append(sql)

    query_names = [
        "Q1: Executive Summary KPIs",
        "Q2: Provider Performance Scorecard",
        "Q3: Month-over-Month Trends",
        "Q4: Scribe Productivity Leaderboard",
        "Q5: Specialty x Month Pivot",
        "Q6: TAT SLA Compliance",
        "Q7: Patient Visit Gap Analysis",
        "Q8: Rolling 7-Day Quality Anomaly",
        "Q9: Telehealth Adoption Trend",
        "Q10: QA Audit Impact Analysis",
    ]

    results = {}
    for i, (name, query) in enumerate(zip(query_names, queries)):
        try:
            df = pd.read_sql_query(query, conn)
            results[name] = df
            print(f"\n  {name} — {len(df)} rows")
            print(f"  {'-' * 50}")
            print(f"  {df.head(5).to_string(index=False)}")
        except Exception as e:
            print(f"\n  {name} — ERROR: {e}")
            # Try to extract just the final SELECT from the query block
            # (some blocks have comments mixed in)

    return results


def main():
    """Create DB, load data, run queries."""
    print("\n[SQLite] Creating database...")
    conn = create_database()

    print("\n[SQLite] Loading data...")
    load_data(conn)

    print("\n[SQLite] Running 10 KPI queries...")
    results = run_kpi_queries(conn)

    conn.close()
    print(f"\n[SQLite] Database saved: {DB_PATH}")
    print(f"  Total size: {DB_PATH.stat().st_size / 1024:.1f} KB")
    return results


if __name__ == "__main__":
    main()
