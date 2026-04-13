#!/usr/bin/env python3
"""
HealthFlow Analytics Dashboard — Full Pipeline Orchestrator
===========================================================
Runs the complete analytics pipeline end-to-end:
  1. Generate synthetic dataset (Synthea + HealthFlow layer)
  2. Clean and validate data
  3. Compute KPIs in pandas
  4. Run statistical analyses
  5. Build Excel dashboard (5 sheets)
  6. Export Power BI star schema
  7. Load data into SQLite database

Usage: python project/run_all.py
"""

import sys
import time
import importlib.util
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent


def load_module(name, path):
    """Dynamically import a module from file path."""
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def main():
    start_time = time.time()

    print("=" * 60)
    print("  HealthFlow Analytics Dashboard — Full Pipeline")
    print("  Healthcare Documentation Analytics Platform")
    print("=" * 60)

    # Step 1: Generate synthetic dataset
    print("\n" + "=" * 60)
    print("  [1/7] GENERATING SYNTHETIC DATASET")
    print("=" * 60)
    gen = load_module("generate_dataset", BASE_DIR / "01_data_generation" / "generate_dataset.py")
    raw_data = gen.main()

    # Step 2: Clean and validate data
    print("\n" + "=" * 60)
    print("  [2/7] CLEANING AND VALIDATING DATA")
    print("=" * 60)
    clean = load_module("data_cleaning", BASE_DIR / "03_python_pipeline" / "data_cleaning.py")
    clean_data = clean.main()

    # Step 3: Compute KPIs
    print("\n" + "=" * 60)
    print("  [3/7] COMPUTING KPIs")
    print("=" * 60)
    kpi = load_module("kpi_engine", BASE_DIR / "03_python_pipeline" / "kpi_engine.py")
    kpi_results = kpi.main(clean_data)

    # Step 4: Statistical analysis
    print("\n" + "=" * 60)
    print("  [4/7] RUNNING STATISTICAL ANALYSES")
    print("=" * 60)
    stats = load_module("statistical_analysis", BASE_DIR / "03_python_pipeline" / "statistical_analysis.py")
    stat_data = {**clean_data, "monthly_kpis": kpi_results["monthly_kpis"]}
    stat_findings = stats.main(stat_data)

    # Step 5: Build Excel dashboard
    print("\n" + "=" * 60)
    print("  [5/7] BUILDING EXCEL DASHBOARD")
    print("=" * 60)
    excel = load_module("build_dashboard", BASE_DIR / "04_excel_dashboard" / "build_dashboard.py")
    excel.main(kpi_results, stat_findings)

    # Step 6: Export Power BI star schema
    print("\n" + "=" * 60)
    print("  [6/7] EXPORTING POWER BI STAR SCHEMA")
    print("=" * 60)
    pbi = load_module("export_star_schema", BASE_DIR / "05_powerbi_prep" / "export_star_schema.py")
    pbi.main(clean_data)

    # Step 7: Load SQLite database
    print("\n" + "=" * 60)
    print("  [7/7] LOADING SQLITE DATABASE")
    print("=" * 60)
    sqlite = load_module("load_to_sqlite", BASE_DIR / "02_sql_analytics" / "load_to_sqlite.py")
    sqlite.main()

    elapsed = time.time() - start_time

    # Final summary
    output_dir = BASE_DIR / "output"
    print("\n" + "=" * 60)
    print("  PIPELINE COMPLETE!")
    print("=" * 60)
    print(f"\n  Time elapsed: {elapsed:.1f} seconds")
    print(f"\n  Generated artifacts in {output_dir}/:")
    print(f"  {'─' * 50}")

    for f in sorted(output_dir.glob("*")):
        if f.is_file():
            size = f.stat().st_size / 1024
            print(f"    {f.name:<40s} {size:>8.1f} KB")

    pbi_dir = output_dir / "powerbi"
    if pbi_dir.exists():
        print(f"\n    powerbi/")
        for f in sorted(pbi_dir.glob("*.csv")):
            size = f.stat().st_size / 1024
            print(f"      {f.name:<38s} {size:>8.1f} KB")

    print(f"\n  Key outputs:")
    print(f"    Excel Dashboard: output/HealthFlow_Dashboard.xlsx")
    print(f"    SQLite Database: output/healthflow.db")
    print(f"    Power BI CSVs:   output/powerbi/ (7 files)")
    print(f"    SQL Queries:     02_sql_analytics/kpi_queries.sql (10 queries)")
    print()


if __name__ == "__main__":
    main()
