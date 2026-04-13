"""
HealthFlow Analytics — Statistical Analysis
===========================================
Hypothesis tests, anomaly detection, and correlation analysis
on healthcare documentation data.
"""

import pandas as pd
import numpy as np
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
OUTPUT_DIR = BASE_DIR / "output"

try:
    from scipy import stats as scipy_stats
    HAS_SCIPY = True
except ImportError:
    HAS_SCIPY = False


def telehealth_vs_inperson_quality(encounters_df):
    """
    Two-sample t-test: Is telehealth documentation quality
    significantly different from in-person?

    H0: mean quality (telehealth) = mean quality (in-person)
    H1: mean quality (telehealth) != mean quality (in-person)
    """
    print("\n  Test 1: Telehealth vs In-Person Quality")
    print("  " + "-" * 45)

    df = encounters_df[encounters_df["note_quality_score"].notna()].copy()
    telehealth = df[df["encounter_type"] == "Telehealth"]["note_quality_score"]
    inperson = df[df["encounter_type"] == "In-Person"]["note_quality_score"]

    print(f"  Telehealth: n={len(telehealth)}, mean={telehealth.mean():.4f}, std={telehealth.std():.4f}")
    print(f"  In-Person:  n={len(inperson)}, mean={inperson.mean():.4f}, std={inperson.std():.4f}")

    if HAS_SCIPY:
        t_stat, p_value = scipy_stats.ttest_ind(telehealth, inperson, equal_var=False)
    else:
        # Manual Welch's t-test
        n1, n2 = len(telehealth), len(inperson)
        m1, m2 = telehealth.mean(), inperson.mean()
        s1, s2 = telehealth.std(), inperson.std()
        se = np.sqrt(s1**2/n1 + s2**2/n2)
        t_stat = (m1 - m2) / se
        # Approximate p-value using normal distribution for large n
        p_value = 2 * (1 - 0.5 * (1 + np.sign(abs(t_stat)) *
                   (1 - np.exp(-2 * abs(t_stat)**2 / np.pi))))

    # Cohen's d effect size
    pooled_std = np.sqrt((telehealth.std()**2 + inperson.std()**2) / 2)
    cohens_d = (telehealth.mean() - inperson.mean()) / pooled_std if pooled_std > 0 else 0

    print(f"  t-statistic: {t_stat:.4f}")
    print(f"  p-value: {p_value:.4f}")
    print(f"  Cohen's d: {cohens_d:.4f}")
    print(f"  Significant at alpha=0.05? {'Yes' if p_value < 0.05 else 'No'}")

    effect = "negligible" if abs(cohens_d) < 0.2 else \
             "small" if abs(cohens_d) < 0.5 else \
             "medium" if abs(cohens_d) < 0.8 else "large"
    print(f"  Effect size: {effect}")

    return {
        "test": "Telehealth vs In-Person Quality",
        "t_statistic": round(t_stat, 4),
        "p_value": round(p_value, 4),
        "cohens_d": round(cohens_d, 4),
        "effect_size": effect,
        "significant": p_value < 0.05,
        "interpretation": f"{'Significant' if p_value < 0.05 else 'No significant'} difference in quality between telehealth and in-person encounters (p={p_value:.4f}, d={cohens_d:.4f})"
    }


def tat_anomaly_detection(encounters_df, providers_df):
    """
    Z-score anomaly detection on TAT by provider.
    Flags encounters > 2 standard deviations above provider mean.
    """
    print("\n  Test 2: TAT Anomaly Detection (Z-score)")
    print("  " + "-" * 45)

    df = encounters_df.merge(
        providers_df[["provider_id", "name", "specialty"]], on="provider_id"
    )
    df = df[df["note_turnaround_minutes"].notna() & (df["note_turnaround_minutes"] > 0)]

    # Compute Z-scores per provider
    df["provider_mean_tat"] = df.groupby("provider_id")["note_turnaround_minutes"].transform("mean")
    df["provider_std_tat"] = df.groupby("provider_id")["note_turnaround_minutes"].transform("std")
    df["z_score"] = (df["note_turnaround_minutes"] - df["provider_mean_tat"]) / df["provider_std_tat"]

    # Also compute IQR method for comparison
    df["provider_q1"] = df.groupby("provider_id")["note_turnaround_minutes"].transform(
        lambda x: x.quantile(0.25))
    df["provider_q3"] = df.groupby("provider_id")["note_turnaround_minutes"].transform(
        lambda x: x.quantile(0.75))
    df["iqr"] = df["provider_q3"] - df["provider_q1"]
    df["iqr_upper"] = df["provider_q3"] + 1.5 * df["iqr"]

    zscore_anomalies = df[df["z_score"].abs() > 2]
    iqr_anomalies = df[df["note_turnaround_minutes"] > df["iqr_upper"]]

    print(f"  Total encounters analyzed: {len(df)}")
    print(f"  Z-score anomalies (|z| > 2): {len(zscore_anomalies)} ({100*len(zscore_anomalies)/len(df):.1f}%)")
    print(f"  IQR anomalies: {len(iqr_anomalies)} ({100*len(iqr_anomalies)/len(df):.1f}%)")

    # Anomaly breakdown by specialty
    anomaly_by_spec = zscore_anomalies.groupby("specialty").size().reset_index(name="anomaly_count")
    total_by_spec = df.groupby("specialty").size().reset_index(name="total")
    spec_summary = anomaly_by_spec.merge(total_by_spec, on="specialty")
    spec_summary["anomaly_rate_pct"] = (100 * spec_summary["anomaly_count"] / spec_summary["total"]).round(1)
    print(f"\n  Anomalies by specialty:")
    for _, row in spec_summary.iterrows():
        print(f"    {row['specialty']}: {row['anomaly_count']}/{row['total']} ({row['anomaly_rate_pct']}%)")

    return {
        "test": "TAT Anomaly Detection",
        "method": "Z-score (threshold=2)",
        "total_analyzed": len(df),
        "zscore_anomalies": len(zscore_anomalies),
        "iqr_anomalies": len(iqr_anomalies),
        "anomaly_rate_pct": round(100 * len(zscore_anomalies) / len(df), 1),
        "anomaly_encounters": zscore_anomalies[
            ["encounter_id", "name", "specialty", "note_turnaround_minutes", "z_score"]
        ].head(20),
    }


def quality_trend_regression(monthly_kpis_df):
    """
    Linear regression on monthly quality scores.
    Is quality trending up or down over time?
    """
    print("\n  Test 3: Quality Trend Regression")
    print("  " + "-" * 45)

    df = monthly_kpis_df.copy()
    df = df.sort_values("month").reset_index(drop=True)
    x = np.arange(len(df))
    y = df["avg_quality"].values

    # numpy polyfit (degree 1 = linear)
    slope, intercept = np.polyfit(x, y, 1)

    # R-squared
    y_pred = slope * x + intercept
    ss_res = np.sum((y - y_pred) ** 2)
    ss_tot = np.sum((y - y.mean()) ** 2)
    r_squared = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0

    # Significance of slope (manual t-test on slope)
    n = len(x)
    if n > 2:
        se_slope = np.sqrt(ss_res / (n - 2)) / np.sqrt(np.sum((x - x.mean()) ** 2))
        t_stat = slope / se_slope if se_slope > 0 else 0
        if HAS_SCIPY:
            p_value = 2 * scipy_stats.t.sf(abs(t_stat), df=n-2)
        else:
            p_value = 0.05  # Placeholder
    else:
        t_stat, p_value = 0, 1

    direction = "upward" if slope > 0 else "downward"
    print(f"  Months analyzed: {n}")
    print(f"  Slope: {slope:.6f} per month")
    print(f"  Direction: {direction}")
    print(f"  R-squared: {r_squared:.4f}")
    print(f"  t-statistic: {t_stat:.4f}")
    print(f"  p-value: {p_value:.4f}")
    print(f"  Significant trend? {'Yes' if p_value < 0.05 else 'No'}")

    return {
        "test": "Quality Trend Regression",
        "slope": round(slope, 6),
        "intercept": round(intercept, 4),
        "r_squared": round(r_squared, 4),
        "direction": direction,
        "p_value": round(p_value, 4),
        "significant": p_value < 0.05,
        "interpretation": f"Quality shows {'significant' if p_value < 0.05 else 'no significant'} {direction} trend (slope={slope:.6f}/month, R²={r_squared:.4f})"
    }


def scribe_experience_correlation(scribe_activity_df, scribes_df):
    """
    Pearson correlation between scribe experience (months)
    and average quality score.
    """
    print("\n  Test 4: Scribe Experience vs Quality Correlation")
    print("  " + "-" * 45)

    sa = scribe_activity_df.groupby("scribe_id").agg(
        avg_quality=("quality_score", "mean")
    ).reset_index()

    sa = sa.merge(scribes_df[["scribe_id", "name", "experience_months"]], on="scribe_id")

    x = sa["experience_months"].values
    y = sa["avg_quality"].values

    if HAS_SCIPY:
        r, p_value = scipy_stats.pearsonr(x, y)
    else:
        # Manual Pearson r
        n = len(x)
        mx, my = x.mean(), y.mean()
        r = np.sum((x - mx) * (y - my)) / (np.sqrt(np.sum((x - mx)**2)) * np.sqrt(np.sum((y - my)**2)))
        p_value = 0.05  # Placeholder

    strength = "weak" if abs(r) < 0.3 else \
               "moderate" if abs(r) < 0.7 else "strong"
    direction = "positive" if r > 0 else "negative"

    print(f"  Scribes analyzed: {len(sa)}")
    print(f"  Pearson r: {r:.4f}")
    print(f"  p-value: {p_value:.4f}")
    print(f"  Correlation: {strength} {direction}")

    for _, row in sa.sort_values("experience_months").iterrows():
        print(f"    {row['name']}: {row['experience_months']}mo exp -> {row['avg_quality']:.3f} quality")

    return {
        "test": "Scribe Experience vs Quality",
        "pearson_r": round(r, 4),
        "p_value": round(p_value, 4),
        "strength": strength,
        "direction": direction,
        "significant": p_value < 0.05,
        "interpretation": f"{strength.capitalize()} {direction} correlation between experience and quality (r={r:.4f}, p={p_value:.4f})"
    }


def main(data=None):
    """Run all statistical analyses."""
    if data is None:
        print("\n[Stats] Loading data...")
        encounters = pd.read_csv(OUTPUT_DIR / "cleaned_encounters.csv")
        providers = pd.read_csv(OUTPUT_DIR / "raw_providers.csv")
        scribes = pd.read_csv(OUTPUT_DIR / "raw_scribes.csv")
        scribe_activity = pd.read_csv(OUTPUT_DIR / "raw_scribe_activity.csv")
        monthly_kpis = pd.read_csv(OUTPUT_DIR / "kpi_monthly.csv")
    else:
        encounters = data.get("encounters")
        providers = data.get("providers")
        scribes = data.get("scribes")
        scribe_activity = data.get("scribe_activity")
        monthly_kpis = data.get("monthly_kpis")

    print("\n[Stats] Running statistical analyses...")
    findings = []

    result1 = telehealth_vs_inperson_quality(encounters)
    findings.append(result1)

    result2 = tat_anomaly_detection(encounters, providers)
    findings.append({k: v for k, v in result2.items() if k != "anomaly_encounters"})

    result3 = quality_trend_regression(monthly_kpis)
    findings.append(result3)

    result4 = scribe_experience_correlation(scribe_activity, scribes)
    findings.append(result4)

    # Save findings
    summary = pd.DataFrame([{
        "test": f["test"],
        "key_metric": list(f.values())[1] if len(f) > 1 else "",
        "p_value": f.get("p_value", ""),
        "significant": f.get("significant", ""),
        "interpretation": f.get("interpretation", ""),
    } for f in findings])

    summary.to_csv(OUTPUT_DIR / "statistical_findings.csv", index=False)
    print(f"\n[Stats] Saved statistical_findings.csv")

    return findings


if __name__ == "__main__":
    main()
