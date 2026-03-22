"""
EduTwin — Teacher View
=======================
Four tabs:
  1. Class Overview  — all students table with GPA + risk
  2. At-Risk         — filtered high/medium risk students
  3. Student Deep Dive — full twin report for one student
  4. Class Analytics   — mastery gaps across all students
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import json
import pandas as pd
import streamlit as st
from core.profile_builder import build_llp
from twin.twin_engine import TwinEngine


# ── Data loader ───────────────────────────────────────────────────────────

@st.cache_data
def load_students():
    path = Path("data/raw/students.json")
    if not path.exists():
        return []
    with open(path) as f:
        return json.load(f)


@st.cache_data
def build_class_df(records: list) -> pd.DataFrame:
    """Build a summary DataFrame for all students."""
    rows = []
    for r in records:
        llp = build_llp(r)
        scores  = llp["academic"]["scores"]
        mastery = llp["academic"]["mastery"]["mastery_map"]
        avg_m   = round(sum(mastery.values()) / len(mastery) * 100, 1) if mastery else 0
        weak    = llp["academic"]["mastery"]["weak_topics"]

        rows.append({
            "ID":          llp["identity"]["student_id"],
            "Name":        llp["identity"]["name"],
            "Major":       llp["identity"]["major"],
            "Year":        llp["identity"]["year_level"],
            "GPA":         scores["overall_gpa"],
            "Quiz":        round(scores["quiz_avg"], 1),
            "Exam":        round(scores["exam_avg"], 1),
            "Avg Mastery": avg_m,
            "Trend":       llp["academic"]["history"]["score_trend"],
            "Weak Topics": ", ".join(weak) if weak else "—",
            "Submissions": f"{int(llp['behavioral']['habits']['submission_rate']*100)}%",
            "Anxiety":     f"{int(llp['self_reported']['confidence']['anxiety_level']*100)}%",
        })
    return pd.DataFrame(rows)


@st.cache_data
def build_risk_df(records: list) -> pd.DataFrame:
    """Build risk predictions for all students (mock only for speed)."""
    rows = []
    for r in records:
        llp    = build_llp(r)
        engine = TwinEngine(provider="mock")
        engine.load_student(llp)
        pred = engine.predict()
        rows.append({
            "ID":            llp["identity"]["student_id"],
            "Name":          llp["identity"]["name"],
            "Major":         llp["identity"]["major"],
            "GPA":           llp["academic"]["scores"]["overall_gpa"],
            "Predicted Exam": pred["predicted_next_exam_score"],
            "Risk":          pred["risk_level"],
            "Top Risk Factor": pred["key_risk_factors"][0] if pred["key_risk_factors"] else "—",
        })
    return pd.DataFrame(rows)


def get_engine(llp: dict, provider: str) -> TwinEngine:
    key = f"t_engine_{llp['identity']['student_id']}_{provider}"
    if key not in st.session_state:
        engine = TwinEngine(provider=provider)
        engine.load_student(llp)
        st.session_state[key] = engine
    return st.session_state[key]


# ── Main render ───────────────────────────────────────────────────────────

def render_teacher_view(provider: str = "mock"):
    records = load_students()
    if not records:
        st.error("No student data found. Run: python data/generate_data.py")
        return

    st.markdown("## 🏫 Teacher Dashboard")
    st.markdown(
        f"<span style='opacity:0.5;font-size:0.82rem'>"
        f"{len(records)} students · EduTwin Digital Twin System"
        f"</span>",
        unsafe_allow_html=True,
    )

    tab1, tab2, tab3, tab4 = st.tabs([
        "📋 Class Overview", "⚠️ At-Risk Students", "🔬 Student Deep Dive", "📊 Class Analytics"
    ])

    # ─────────────────────────────────────────────────────────────────
    # TAB 1 — CLASS OVERVIEW
    # ─────────────────────────────────────────────────────────────────
    with tab1:
        df = build_class_df(records)

        # Class-wide KPIs
        c1, c2, c3, c4, c5 = st.columns(5)
        with c1:
            st.markdown(
                f"<div class='kpi-card'><div class='kpi-value'>{len(df)}</div>"
                f"<div class='kpi-label'>Total Students</div></div>",
                unsafe_allow_html=True,
            )
        with c2:
            st.markdown(
                f"<div class='kpi-card'><div class='kpi-value'>{df['GPA'].mean():.2f}</div>"
                f"<div class='kpi-label'>Avg GPA</div></div>",
                unsafe_allow_html=True,
            )
        with c3:
            st.markdown(
                f"<div class='kpi-card'><div class='kpi-value'>{df['Exam'].mean():.1f}</div>"
                f"<div class='kpi-label'>Avg Exam Score</div></div>",
                unsafe_allow_html=True,
            )
        with c4:
            declining = (df["Trend"] == "declining").sum()
            st.markdown(
                f"<div class='kpi-card'>"
                f"<div class='kpi-value risk-high'>{declining}</div>"
                f"<div class='kpi-label'>Declining Trend</div></div>",
                unsafe_allow_html=True,
            )
        with c5:
            st.markdown(
                f"<div class='kpi-card'><div class='kpi-value'>{df['Avg Mastery'].mean():.1f}%</div>"
                f"<div class='kpi-label'>Avg Mastery</div></div>",
                unsafe_allow_html=True,
            )

        st.markdown("")

        # Filters
        col1, col2, col3 = st.columns(3)
        with col1:
            major_filter = st.multiselect(
                "Filter by major", df["Major"].unique().tolist(), default=[]
            )
        with col2:
            trend_filter = st.multiselect(
                "Filter by trend", ["improving", "stable", "declining"], default=[]
            )
        with col3:
            gpa_min = st.slider("Min GPA", 0.0, 4.0, 0.0, 0.1)

        filtered = df.copy()
        if major_filter:
            filtered = filtered[filtered["Major"].isin(major_filter)]
        if trend_filter:
            filtered = filtered[filtered["Trend"].isin(trend_filter)]
        filtered = filtered[filtered["GPA"] >= gpa_min]

        st.markdown(
            f"<div class='section-title'>Showing {len(filtered)} students</div>",
            unsafe_allow_html=True,
        )
        st.dataframe(
            filtered,
            use_container_width=True,
            hide_index=True,
            column_config={
                "GPA":         st.column_config.NumberColumn(format="%.2f"),
                "Avg Mastery": st.column_config.NumberColumn(format="%.1f"),
            },
        )

    # ─────────────────────────────────────────────────────────────────
    # TAB 2 — AT-RISK
    # ─────────────────────────────────────────────────────────────────
    with tab2:
        st.markdown("<div class='section-title'>Risk Prediction — All Students</div>", unsafe_allow_html=True)

        with st.spinner("Running risk predictions..."):
            risk_df = build_risk_df(records)

        risk_filter = st.radio(
            "Show", ["All", "High", "Medium", "Low"],
            horizontal=True, index=1
        )

        display_risk = risk_df if risk_filter == "All" else risk_df[risk_df["Risk"] == risk_filter]

        # Summary counts
        c1, c2, c3 = st.columns(3)
        with c1:
            n = (risk_df["Risk"] == "High").sum()
            st.markdown(
                f"<div class='kpi-card'><div class='kpi-value risk-high'>{n}</div>"
                f"<div class='kpi-label'>High Risk</div></div>",
                unsafe_allow_html=True,
            )
        with c2:
            n = (risk_df["Risk"] == "Medium").sum()
            st.markdown(
                f"<div class='kpi-card'><div class='kpi-value risk-medium'>{n}</div>"
                f"<div class='kpi-label'>Medium Risk</div></div>",
                unsafe_allow_html=True,
            )
        with c3:
            n = (risk_df["Risk"] == "Low").sum()
            st.markdown(
                f"<div class='kpi-card'><div class='kpi-value risk-low'>{n}</div>"
                f"<div class='kpi-label'>Low Risk</div></div>",
                unsafe_allow_html=True,
            )

        st.markdown("")
        st.dataframe(
            display_risk.sort_values("GPA"),
            use_container_width=True,
            hide_index=True,
        )

    # ─────────────────────────────────────────────────────────────────
    # TAB 3 — STUDENT DEEP DIVE
    # ─────────────────────────────────────────────────────────────────
    with tab3:
        names   = [f"{r['name']} ({r['student_id']})" for r in records]
        sel_idx = st.selectbox("Select student", names, key="teacher_student_select")
        idx     = names.index(sel_idx)

        raw    = records[idx]
        llp    = build_llp(raw)
        engine = get_engine(llp, provider)
        name   = llp["identity"]["name"]

        col1, col2 = st.columns([1, 1])
        with col1:
            st.markdown(f"### {name}")
            st.markdown(
                f"**Major:** {llp['identity']['major']}  \n"
                f"**Year:** {llp['identity']['year_level']}  \n"
                f"**GPA:** {llp['academic']['scores']['overall_gpa']:.2f}  \n"
                f"**Trend:** {llp['academic']['history']['score_trend'].capitalize()}"
            )

            st.markdown("<div class='section-title'>Topic Mastery</div>", unsafe_allow_html=True)
            mastery  = llp["academic"]["mastery"]["mastery_map"]
            sorted_m = sorted(mastery.items(), key=lambda x: x[1])
            bars_html = ""
            for topic, score in sorted_m:
                pct   = int(score * 100)
                color = "#ff6b6b" if pct < 40 else "#ffd93d" if pct < 65 else "#6bcb77"
                bars_html += (
                    f"<div class='mastery-row'>"
                    f"<div class='mastery-label'>{topic}</div>"
                    f"<div class='mastery-bar-bg'>"
                    f"<div class='mastery-bar-fill' style='width:{pct}%;background:{color}'></div>"
                    f"</div>"
                    f"<div class='mastery-pct'>{pct}%</div>"
                    f"</div>"
                )
            st.markdown(bars_html, unsafe_allow_html=True)

        with col2:
            st.markdown("<div class='section-title'>Weakness Diagnosis</div>", unsafe_allow_html=True)
            with st.spinner("Diagnosing..."):
                diagnosis = engine.diagnose()

            for item in diagnosis:
                sev  = item.get("severity", "Minor")
                css  = {"Critical": "diag-critical", "Moderate": "diag-moderate", "Minor": "diag-minor"}.get(sev, "diag-minor")
                icon = {"Critical": "🔴", "Moderate": "🟡", "Minor": "🟢"}.get(sev, "⚪")
                st.markdown(
                    f"<div class='diag-card {css}'>"
                    f"<strong>{icon} {item.get('topic','?')}</strong> · {sev}<br>"
                    f"<span style='font-size:0.82rem;opacity:0.7'>{item.get('root_cause','')}</span><br>"
                    f"<em style='font-size:0.82rem'>{item.get('intervention','')}</em>"
                    f"</div>",
                    unsafe_allow_html=True,
                )

            pred = engine.predict()
            st.markdown("<div class='section-title'>Prediction</div>", unsafe_allow_html=True)
            risk_color = {"High": "#ff6b6b", "Medium": "#ffd93d", "Low": "#6bcb77"}.get(pred["risk_level"], "#fff")
            st.markdown(
                f"Predicted exam: **{pred['predicted_next_exam_score']}** · "
                f"Predicted GPA: **{pred['predicted_end_of_term_gpa']}** · "
                f"Risk: <span style='color:{risk_color}'><strong>{pred['risk_level']}</strong></span>",
                unsafe_allow_html=True,
            )
            st.markdown("**Actions:**")
            for a in pred.get("recommended_actions", []):
                st.markdown(f"→ {a}")

    # ─────────────────────────────────────────────────────────────────
    # TAB 4 — CLASS ANALYTICS
    # ─────────────────────────────────────────────────────────────────
    with tab4:
        st.markdown("<div class='section-title'>Class-Wide Mastery Gaps</div>", unsafe_allow_html=True)

        # Collect all topic mastery across students
        topic_data: dict[str, list] = {}
        for r in records:
            llp     = build_llp(r)
            mastery = llp["academic"]["mastery"]["mastery_map"]
            for topic, score in mastery.items():
                topic_data.setdefault(topic, []).append(score * 100)

        # Average mastery per topic
        topic_avgs = {t: round(sum(v)/len(v), 1) for t, v in topic_data.items()}
        sorted_avgs = sorted(topic_avgs.items(), key=lambda x: x[1])

        bars_html = "<div style='max-width:600px'>"
        for topic, avg in sorted_avgs:
            color = "#ff6b6b" if avg < 40 else "#ffd93d" if avg < 65 else "#6bcb77"
            bars_html += (
                f"<div class='mastery-row'>"
                f"<div class='mastery-label'>{topic}</div>"
                f"<div class='mastery-bar-bg'>"
                f"<div class='mastery-bar-fill' style='width:{avg}%;background:{color}'></div>"
                f"</div>"
                f"<div class='mastery-pct'>{avg}%</div>"
                f"</div>"
            )
        bars_html += "</div>"
        st.markdown(bars_html, unsafe_allow_html=True)

        # GPA distribution
        st.markdown("<div class='section-title'>GPA Distribution</div>", unsafe_allow_html=True)
        df    = build_class_df(records)
        bins  = [0, 1.0, 2.0, 2.5, 3.0, 3.5, 4.0]
        labels = ["<1.0", "1-2", "2-2.5", "2.5-3", "3-3.5", "3.5-4"]
        df["GPA Band"] = pd.cut(df["GPA"], bins=bins, labels=labels, include_lowest=True)
        band_counts = df["GPA Band"].value_counts().sort_index()
        st.bar_chart(band_counts)

        # Score trend breakdown
        st.markdown("<div class='section-title'>Score Trend Breakdown</div>", unsafe_allow_html=True)
        trend_counts = df["Trend"].value_counts()
        c1, c2, c3 = st.columns(3)
        with c1:
            n = trend_counts.get("improving", 0)
            st.markdown(
                f"<div class='kpi-card'><div class='kpi-value risk-low'>{n}</div>"
                f"<div class='kpi-label'>📈 Improving</div></div>",
                unsafe_allow_html=True,
            )
        with c2:
            n = trend_counts.get("stable", 0)
            st.markdown(
                f"<div class='kpi-card'><div class='kpi-value'>{n}</div>"
                f"<div class='kpi-label'>➡️ Stable</div></div>",
                unsafe_allow_html=True,
            )
        with c3:
            n = trend_counts.get("declining", 0)
            st.markdown(
                f"<div class='kpi-card'><div class='kpi-value risk-high'>{n}</div>"
                f"<div class='kpi-label'>📉 Declining</div></div>",
                unsafe_allow_html=True,
            )
