"""
HealthFlow Analytics — Interactive Web Dashboard
================================================
Streamlit app showcasing healthcare documentation analytics.
Run: streamlit run project/06_web_dashboard/app.py
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
OUTPUT_DIR = BASE_DIR / "output"

# Page config
st.set_page_config(
    page_title="HealthFlow Analytics Dashboard",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded",
)


@st.cache_data
def load_data():
    """Load all generated data."""
    data = {}
    data["encounters"] = pd.read_csv(OUTPUT_DIR / "cleaned_encounters.csv")
    data["encounters"]["encounter_date"] = pd.to_datetime(
        data["encounters"]["encounter_date"], utc=True
    ).dt.tz_localize(None)
    data["providers"] = pd.read_csv(OUTPUT_DIR / "raw_providers.csv")
    data["scribes"] = pd.read_csv(OUTPUT_DIR / "raw_scribes.csv")
    data["scribe_activity"] = pd.read_csv(OUTPUT_DIR / "raw_scribe_activity.csv")
    data["diagnoses"] = pd.read_csv(OUTPUT_DIR / "raw_diagnoses.csv")
    data["monthly_kpis"] = pd.read_csv(OUTPUT_DIR / "kpi_monthly.csv")
    data["provider_scorecard"] = pd.read_csv(OUTPUT_DIR / "kpi_provider_scorecard.csv")
    data["scribe_leaderboard"] = pd.read_csv(OUTPUT_DIR / "kpi_scribe_leaderboard.csv")
    data["daily_trends"] = pd.read_csv(OUTPUT_DIR / "kpi_daily_trends.csv")
    data["stat_findings"] = pd.read_csv(OUTPUT_DIR / "statistical_findings.csv")
    return data


def render_sidebar(data):
    """Render sidebar filters."""
    st.sidebar.title("Filters")

    enc = data["encounters"].merge(
        data["providers"][["provider_id", "specialty"]], on="provider_id", how="left"
    )

    specialties = ["All"] + sorted(enc["specialty"].dropna().unique().tolist())
    selected_specialty = st.sidebar.selectbox("Specialty", specialties)

    enc_types = ["All"] + sorted(enc["encounter_type"].dropna().unique().tolist())
    selected_type = st.sidebar.selectbox("Encounter Type", enc_types)

    # Date range
    min_date = enc["encounter_date"].min().date()
    max_date = enc["encounter_date"].max().date()
    date_range = st.sidebar.date_input(
        "Date Range",
        value=(min_date, max_date),
        min_value=min_date,
        max_value=max_date,
    )

    st.sidebar.markdown("---")
    st.sidebar.markdown("**Data Source:** Synthea + HealthFlow Layer")
    st.sidebar.markdown("**Records:** {:,} encounters".format(len(data["encounters"])))
    st.sidebar.markdown("**Pipeline:** Python + SQL + Excel + Power BI")

    return selected_specialty, selected_type, date_range


def filter_data(encounters, providers, specialty, enc_type, date_range):
    """Apply sidebar filters to encounters."""
    df = encounters.merge(
        providers[["provider_id", "specialty", "name"]],
        on="provider_id", how="left", suffixes=("", "_provider")
    )

    if specialty != "All":
        df = df[df["specialty"] == specialty]
    if enc_type != "All":
        df = df[df["encounter_type"] == enc_type]
    if len(date_range) == 2:
        start, end = pd.Timestamp(date_range[0]), pd.Timestamp(date_range[1])
        df = df[(df["encounter_date"] >= start) & (df["encounter_date"] <= end)]

    return df


def render_kpi_cards(filtered_df):
    """Render top KPI cards."""
    col1, col2, col3, col4, col5, col6 = st.columns(6)

    total = len(filtered_df)
    avg_quality = filtered_df["note_quality_score"].mean()
    avg_tat = filtered_df["note_turnaround_minutes"].mean()
    completion = 100 * (filtered_df["notes_status"] == "Completed").sum() / max(total, 1)
    telehealth = 100 * (filtered_df["encounter_type"] == "Telehealth").sum() / max(total, 1)
    patients = filtered_df["patient_id"].nunique()

    col1.metric("Total Encounters", f"{total:,}")
    col2.metric("Avg Quality", f"{avg_quality:.3f}")
    col3.metric("Avg TAT (min)", f"{avg_tat:.1f}")
    col4.metric("Completion Rate", f"{completion:.1f}%")
    col5.metric("Telehealth %", f"{telehealth:.1f}%")
    col6.metric("Unique Patients", f"{patients:,}")


def render_overview_tab(filtered_df, data):
    """Tab 1: Overview with trend charts."""
    st.subheader("Monthly Trends")

    monthly = data["monthly_kpis"].copy()
    # Use last 12 months
    monthly = monthly.tail(12)

    col1, col2 = st.columns(2)

    with col1:
        fig = go.Figure()
        fig.add_trace(go.Bar(
            x=monthly["month"], y=monthly["total_encounters"],
            name="Encounters", marker_color="#2980B9"
        ))
        fig.add_trace(go.Scatter(
            x=monthly["month"], y=monthly["avg_quality"] * 100,
            name="Quality (%)", yaxis="y2",
            line=dict(color="#27AE60", width=3)
        ))
        fig.update_layout(
            title="Encounter Volume & Quality Score",
            yaxis=dict(title="Encounters"),
            yaxis2=dict(title="Quality (%)", overlaying="y", side="right",
                        range=[80, 100]),
            legend=dict(x=0.01, y=0.99),
            height=400,
        )
        st.plotly_chart(fig, width="stretch")

    with col2:
        fig = px.line(monthly, x="month", y="avg_tat",
                      title="Average Turnaround Time (TAT)",
                      labels={"avg_tat": "TAT (minutes)", "month": "Month"})
        fig.update_traces(line=dict(color="#E74C3C", width=3))
        fig.update_layout(height=400)
        st.plotly_chart(fig, width="stretch")

    # Encounter type distribution
    col3, col4 = st.columns(2)

    with col3:
        type_dist = filtered_df["encounter_type"].value_counts().reset_index()
        type_dist.columns = ["Type", "Count"]
        fig = px.pie(type_dist, values="Count", names="Type",
                     title="Encounter Type Distribution",
                     color_discrete_sequence=["#2980B9", "#27AE60"])
        fig.update_layout(height=350)
        st.plotly_chart(fig, width="stretch")

    with col4:
        diag_df = filtered_df.merge(
            data["diagnoses"], left_on="diagnosis_code", right_on="icd_code", how="left"
        )
        cat_dist = diag_df["category"].value_counts().reset_index()
        cat_dist.columns = ["Category", "Count"]
        fig = px.pie(cat_dist, values="Count", names="Category",
                     title="Diagnosis Category Distribution",
                     color_discrete_sequence=["#E74C3C", "#27AE60", "#2980B9"])
        fig.update_layout(height=350)
        st.plotly_chart(fig, width="stretch")


def render_providers_tab(data):
    """Tab 2: Provider Performance."""
    st.subheader("Provider Performance Scorecard")

    scorecard = data["provider_scorecard"].copy()

    col1, col2 = st.columns([2, 1])

    with col1:
        fig = px.bar(
            scorecard.sort_values("composite_score"),
            x="composite_score", y="name", orientation="h",
            color="specialty",
            title="Provider Composite Score Ranking",
            labels={"composite_score": "Composite Score", "name": "Provider"},
            height=500,
        )
        fig.update_layout(yaxis=dict(categoryorder="total ascending"))
        st.plotly_chart(fig, width="stretch")

    with col2:
        spec_avg = scorecard.groupby("specialty").agg(
            avg_quality=("avg_quality", "mean"),
            avg_tat=("avg_tat", "mean"),
            providers=("provider_id", "count"),
        ).reset_index()
        st.markdown("**Specialty Summary**")
        st.dataframe(spec_avg.round(3), width="stretch", hide_index=True)

    # Detailed table
    st.markdown("**Detailed Scorecard**")
    display_cols = ["name", "specialty", "total_encounters", "avg_quality",
                    "avg_tat", "completion_rate", "composite_score", "rank_in_specialty"]
    st.dataframe(
        scorecard[display_cols].style.background_gradient(
            subset=["avg_quality", "composite_score"], cmap="Greens"
        ).background_gradient(
            subset=["avg_tat"], cmap="Reds"
        ),
        width="stretch", hide_index=True
    )


def render_scribes_tab(data):
    """Tab 3: Scribe Productivity."""
    st.subheader("Scribe Productivity Leaderboard")

    lb = data["scribe_leaderboard"].copy()

    col1, col2 = st.columns(2)

    with col1:
        fig = px.bar(
            lb.sort_values("avg_quality"),
            x="avg_quality", y="name", orientation="h",
            color="performance_tier",
            color_discrete_map={
                "Top Performer": "#27AE60",
                "On Track": "#2980B9",
                "Needs Training": "#E74C3C",
            },
            title="Scribe Quality Score",
            labels={"avg_quality": "Avg Quality", "name": "Scribe"},
        )
        fig.update_layout(height=400, yaxis=dict(categoryorder="total ascending"))
        st.plotly_chart(fig, width="stretch")

    with col2:
        fig = px.scatter(
            lb, x="experience_months", y="avg_quality",
            size="notes_completed", color="performance_tier",
            hover_name="name",
            color_discrete_map={
                "Top Performer": "#27AE60",
                "On Track": "#2980B9",
                "Needs Training": "#E74C3C",
            },
            title="Experience vs Quality (bubble = notes completed)",
            labels={"experience_months": "Experience (months)", "avg_quality": "Avg Quality"},
        )
        fig.update_layout(height=400)
        st.plotly_chart(fig, width="stretch")

    # Table
    display_cols = ["name", "experience_months", "shift", "notes_completed",
                    "notes_per_day", "avg_quality", "avg_edits", "performance_tier"]
    st.dataframe(lb[display_cols], width="stretch", hide_index=True)


def render_trends_tab(data):
    """Tab 4: Trends & Anomaly Detection."""
    st.subheader("Daily Quality Trends & Anomaly Detection")

    daily = data["daily_trends"].copy()
    daily = daily.tail(90)  # Last 90 days

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=daily["date"], y=daily["avg_quality"],
        name="Daily Quality", mode="lines",
        line=dict(color="#2980B9", width=1.5),
    ))
    fig.add_trace(go.Scatter(
        x=daily["date"], y=daily["rolling_7d_quality"],
        name="7-Day Rolling Avg", mode="lines",
        line=dict(color="#E74C3C", width=3),
    ))

    # Mark anomalies
    anomalies = daily[daily["anomaly_flag"] != "Normal"]
    if len(anomalies) > 0:
        fig.add_trace(go.Scatter(
            x=anomalies["date"], y=anomalies["avg_quality"],
            name="Anomaly", mode="markers",
            marker=dict(color="red", size=12, symbol="x"),
        ))

    fig.update_layout(
        title="Daily Quality: Actual vs 7-Day Rolling Average",
        yaxis_title="Quality Score", xaxis_title="Date",
        height=450,
    )
    st.plotly_chart(fig, width="stretch")

    # TAT trend
    fig2 = go.Figure()
    fig2.add_trace(go.Scatter(
        x=daily["date"], y=daily["avg_tat"],
        name="Daily TAT", mode="lines",
        line=dict(color="#F39C12", width=1.5),
    ))
    fig2.add_trace(go.Scatter(
        x=daily["date"], y=daily["rolling_7d_tat"],
        name="7-Day Rolling Avg", mode="lines",
        line=dict(color="#8E44AD", width=3),
    ))
    fig2.update_layout(
        title="Daily TAT: Actual vs 7-Day Rolling Average",
        yaxis_title="TAT (minutes)", xaxis_title="Date",
        height=400,
    )
    st.plotly_chart(fig2, width="stretch")

    # Anomaly summary
    anomaly_count = (daily["anomaly_flag"] != "Normal").sum()
    st.info(f"Anomalies detected in last 90 days: **{anomaly_count}** "
            f"(quality drops >15% below rolling avg or TAT spikes >20% above)")


def render_stats_tab(data):
    """Tab 5: Statistical Findings."""
    st.subheader("Statistical Analysis Results")

    findings = data["stat_findings"]

    for _, row in findings.iterrows():
        with st.expander(f"**{row['test']}**", expanded=True):
            col1, col2 = st.columns([1, 2])
            with col1:
                significant = str(row.get("significant", ""))
                if significant == "True":
                    st.success("Statistically Significant")
                else:
                    st.warning("Not Significant")
                st.metric("p-value", row.get("p_value", "N/A"))
            with col2:
                st.markdown(f"**Interpretation:** {row.get('interpretation', 'N/A')}")

    # Scribe experience scatter with regression line
    st.markdown("---")
    st.subheader("Scribe Experience vs Quality Correlation")
    lb = data["scribe_leaderboard"]
    import numpy as np
    fig = px.scatter(
        lb, x="experience_months", y="avg_quality",
        hover_name="name",
        labels={"experience_months": "Experience (months)", "avg_quality": "Avg Quality Score"},
        title="Experience-Quality Correlation (r=0.73, p=0.02)",
    )
    fig.update_traces(marker=dict(size=12, color="#2980B9"))
    # Manual trendline using numpy polyfit (avoids statsmodels dependency)
    x = lb["experience_months"].values
    y = lb["avg_quality"].values
    slope, intercept = np.polyfit(x, y, 1)
    x_line = np.array([x.min(), x.max()])
    fig.add_trace(go.Scatter(
        x=x_line, y=slope * x_line + intercept,
        mode="lines", name="Trend",
        line=dict(color="red", dash="dash", width=2),
    ))
    fig.update_layout(height=400)
    st.plotly_chart(fig, width="stretch")


def main():
    """Main dashboard layout."""
    data = load_data()

    # Sidebar
    specialty, enc_type, date_range = render_sidebar(data)

    # Title
    st.title("HealthFlow Analytics Dashboard")
    st.caption("Healthcare Documentation Performance Analytics | Built with Python, SQL, Streamlit")

    # Filter data
    filtered = filter_data(data["encounters"], data["providers"],
                           specialty, enc_type, date_range)

    # KPI cards
    render_kpi_cards(filtered)
    st.markdown("---")

    # Tabs
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "Overview", "Provider Performance",
        "Scribe Productivity", "Trends & Alerts",
        "Statistical Analysis"
    ])

    with tab1:
        render_overview_tab(filtered, data)
    with tab2:
        render_providers_tab(data)
    with tab3:
        render_scribes_tab(data)
    with tab4:
        render_trends_tab(data)
    with tab5:
        render_stats_tab(data)

    # Footer
    st.markdown("---")
    st.markdown(
        """
        <div style="text-align: center; padding: 1rem 0; color: #666;">
            <p style="margin-bottom: 0.5rem;"><strong>Built by Sheikh Rahat Mahmud</strong></p>
            <p style="margin-bottom: 0.3rem;">
                <a href="mailto:sheikhrahatm@gmail.com">sheikhrahatm@gmail.com</a> &nbsp;|&nbsp;
                <a href="https://www.linkedin.com/in/sheikh-rahat-mahmud/" target="_blank">LinkedIn</a> &nbsp;|&nbsp;
                <a href="https://github.com/Rahat463" target="_blank">GitHub</a>
            </p>
            <p style="font-size: 0.85rem;">BSc in CSE, Bangladesh University of Engineering & Technology (BUET)</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


if __name__ == "__main__":
    main()
