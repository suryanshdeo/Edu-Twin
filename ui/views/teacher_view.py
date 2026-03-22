"""
EduTwin — Teacher View (Real Data)
====================================
Reads all real students from the database and shows
class-wide insights + individual deep dives.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import streamlit as st
import pandas as pd
from database.crud import get_all_students
from core.profile_builder import build_llp_from_db
from twin.twin_engine import TwinEngine


@st.cache_data(ttl=30)
def load_all_llps() -> list[dict]:
    """Load LLPs for all students. Cached for 30 seconds."""
    students = get_all_students()
    llps = []
    for s in students:
        try:
            llp = build_llp_from_db(s["id"])
            if llp["academic"]["mastery"]["mastery_map"]:
                llps.append(llp)
        except Exception:
            pass
    return llps


def build_class_df(llps: list[dict]) -> pd.DataFrame:
    rows = []
    for llp in llps:
        mastery = llp["academic"]["mastery"]["mastery_map"]
        avg_m   = round(sum(mastery.values()) / len(mastery) * 100, 1) if mastery else 0
        weak    = llp["academic"]["mastery"]["weak_topics"]
        scores  = llp["academic"]["scores"]
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
        })
    return pd.DataFrame(rows)


def render_teacher_view(provider: str = "mock"):
    st.markdown("## 🏫 Teacher Dashboard")

    llps = load_all_llps()

    if not llps:
        st.warning("No students with complete profiles found yet.")
        st.info("Students need to sign up and fill in their profile data before they appear here.")
        return

    st.markdown(
        f"<span style='opacity:0.5;font-size:0.82rem'>"
        f"{len(llps)} students with complete profiles</span>",
        unsafe_allow_html=True,
    )

    tab1, tab2, tab3, tab4 = st.tabs([
        "📋 Class Overview", "⚠️ At-Risk", "🔬 Student Deep Dive", "📊 Analytics"
    ])

    # ── TAB 1: CLASS OVERVIEW ─────────────────────────────────────────
    with tab1:
        df = build_class_df(llps)

        c1, c2, c3, c4, c5 = st.columns(5)
        with c1:
            st.markdown(f"<div class='kpi-card'><div class='kpi-value'>{len(df)}</div><div class='kpi-label'>Students</div></div>", unsafe_allow_html=True)
        with c2:
            st.markdown(f"<div class='kpi-card'><div class='kpi-value'>{df['GPA'].mean():.2f}</div><div class='kpi-label'>Avg GPA</div></div>", unsafe_allow_html=True)
        with c3:
            st.markdown(f"<div class='kpi-card'><div class='kpi-value'>{df['Exam'].mean():.1f}</div><div class='kpi-label'>Avg Exam</div></div>", unsafe_allow_html=True)
        with c4:
            n = (df["Trend"] == "declining").sum()
            st.markdown(f"<div class='kpi-card'><div class='kpi-value risk-high'>{n}</div><div class='kpi-label'>Declining</div></div>", unsafe_allow_html=True)
        with c5:
            st.markdown(f"<div class='kpi-card'><div class='kpi-value'>{df['Avg Mastery'].mean():.1f}%</div><div class='kpi-label'>Avg Mastery</div></div>", unsafe_allow_html=True)

        st.markdown("")
        col1, col2 = st.columns(2)
        with col1:
            major_filter = st.multiselect("Filter by major", df["Major"].unique().tolist())
        with col2:
            trend_filter = st.multiselect("Filter by trend", ["improving", "stable", "declining"])

        filtered = df.copy()
        if major_filter:
            filtered = filtered[filtered["Major"].isin(major_filter)]
        if trend_filter:
            filtered = filtered[filtered["Trend"].isin(trend_filter)]

        st.dataframe(filtered, use_container_width=True, hide_index=True)

    # ── TAB 2: AT-RISK ────────────────────────────────────────────────
    with tab2:
        st.markdown("<div class='section-title'>Risk Assessment</div>", unsafe_allow_html=True)

        risk_rows = []
        for llp in llps:
            engine = TwinEngine(provider="mock")
            engine.load_student(llp)
            pred = engine.predict()
            risk_rows.append({
                "Name":           llp["identity"]["name"],
                "Major":          llp["identity"]["major"],
                "GPA":            llp["academic"]["scores"]["overall_gpa"],
                "Predicted Exam": pred["predicted_next_exam_score"],
                "Risk":           pred["risk_level"],
                "Top Risk Factor": pred["key_risk_factors"][0] if pred["key_risk_factors"] else "—",
            })

        risk_df = pd.DataFrame(risk_rows)

        c1, c2, c3 = st.columns(3)
        with c1:
            n = (risk_df["Risk"] == "High").sum()
            st.markdown(f"<div class='kpi-card'><div class='kpi-value risk-high'>{n}</div><div class='kpi-label'>High Risk</div></div>", unsafe_allow_html=True)
        with c2:
            n = (risk_df["Risk"] == "Medium").sum()
            st.markdown(f"<div class='kpi-card'><div class='kpi-value risk-medium'>{n}</div><div class='kpi-label'>Medium Risk</div></div>", unsafe_allow_html=True)
        with c3:
            n = (risk_df["Risk"] == "Low").sum()
            st.markdown(f"<div class='kpi-card'><div class='kpi-value risk-low'>{n}</div><div class='kpi-label'>Low Risk</div></div>", unsafe_allow_html=True)

        st.markdown("")
        risk_filter = st.radio("Show", ["All", "High", "Medium", "Low"], horizontal=True, index=1)
        display = risk_df if risk_filter == "All" else risk_df[risk_df["Risk"] == risk_filter]
        st.dataframe(display.sort_values("GPA"), use_container_width=True, hide_index=True)

    # ── TAB 3: STUDENT DEEP DIVE ──────────────────────────────────────
    with tab3:
        names   = [llp["identity"]["name"] for llp in llps]
        sel     = st.selectbox("Select student", names)
        llp     = llps[names.index(sel)]
        engine  = TwinEngine(provider=provider)
        engine.load_student(llp)

        col1, col2 = st.columns(2)
        with col1:
            st.markdown(f"### {llp['identity']['name']}")
            st.markdown(
                f"**Major:** {llp['identity']['major']}  \n"
                f"**Year:** {llp['identity']['year_level']}  \n"
                f"**GPA:** {llp['academic']['scores']['overall_gpa']:.2f}  \n"
                f"**Trend:** {llp['academic']['history']['score_trend'].capitalize()}"
            )
            st.markdown("<div class='section-title'>Topic Mastery</div>", unsafe_allow_html=True)
            mastery  = llp["academic"]["mastery"]["mastery_map"]
            sorted_m = sorted(mastery.items(), key=lambda x: x[1])
            bars = ""
            for topic, score in sorted_m:
                pct   = int(score * 100)
                color = "#ff6b6b" if pct < 40 else "#ffd93d" if pct < 65 else "#6bcb77"
                bars += (
                    f"<div class='mastery-row'>"
                    f"<div class='mastery-label'>{topic}</div>"
                    f"<div class='mastery-bar-bg'><div class='mastery-bar-fill' style='width:{pct}%;background:{color}'></div></div>"
                    f"<div class='mastery-pct'>{pct}%</div></div>"
                )
            st.markdown(bars, unsafe_allow_html=True)

        with col2:
            st.markdown("<div class='section-title'>Weakness Diagnosis</div>", unsafe_allow_html=True)
            diagnosis = engine.diagnose()
            for item in diagnosis:
                sev  = item.get("severity", "Minor")
                css  = {"Critical":"diag-critical","Moderate":"diag-moderate","Minor":"diag-minor"}.get(sev,"diag-minor")
                icon = {"Critical":"🔴","Moderate":"🟡","Minor":"🟢"}.get(sev,"⚪")
                st.markdown(
                    f"<div class='diag-card {css}'>"
                    f"<strong>{icon} {item.get('topic','?')}</strong> · {sev}<br>"
                    f"<em style='font-size:0.82rem'>{item.get('intervention','')}</em>"
                    f"</div>",
                    unsafe_allow_html=True,
                )

            pred = engine.predict()
            st.markdown("<div class='section-title'>Prediction</div>", unsafe_allow_html=True)
            risk_color = {"High":"#ff6b6b","Medium":"#ffd93d","Low":"#6bcb77"}.get(pred["risk_level"],"#fff")
            st.markdown(
                f"Predicted exam: **{pred['predicted_next_exam_score']}** · "
                f"Risk: <span style='color:{risk_color}'><strong>{pred['risk_level']}</strong></span>",
                unsafe_allow_html=True,
            )
            for a in pred.get("recommended_actions", []):
                st.markdown(f"→ {a}")

    # ── TAB 4: ANALYTICS ──────────────────────────────────────────────
    with tab4:
        st.markdown("<div class='section-title'>Class-Wide Mastery Gaps</div>", unsafe_allow_html=True)
        topic_data: dict[str, list] = {}
        for llp in llps:
            for topic, score in llp["academic"]["mastery"]["mastery_map"].items():
                topic_data.setdefault(topic, []).append(score * 100)

        topic_avgs = {t: round(sum(v)/len(v), 1) for t, v in topic_data.items()}
        sorted_avgs = sorted(topic_avgs.items(), key=lambda x: x[1])

        bars = "<div style='max-width:600px'>"
        for topic, avg in sorted_avgs:
            color = "#ff6b6b" if avg < 40 else "#ffd93d" if avg < 65 else "#6bcb77"
            bars += (
                f"<div class='mastery-row'>"
                f"<div class='mastery-label'>{topic}</div>"
                f"<div class='mastery-bar-bg'><div class='mastery-bar-fill' style='width:{avg}%;background:{color}'></div></div>"
                f"<div class='mastery-pct'>{avg}%</div></div>"
            )
        bars += "</div>"
        st.markdown(bars, unsafe_allow_html=True)

        st.markdown("<div class='section-title'>GPA Distribution</div>", unsafe_allow_html=True)
        df    = build_class_df(llps)
        bins  = [0, 1.0, 2.0, 2.5, 3.0, 3.5, 4.0]
        labels = ["<1.0", "1-2", "2-2.5", "2.5-3", "3-3.5", "3.5-4"]
        df["GPA Band"] = pd.cut(df["GPA"], bins=bins, labels=labels, include_lowest=True)
        st.bar_chart(df["GPA Band"].value_counts().sort_index())
