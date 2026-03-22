"""
EduTwin — Student View
=======================
Four tabs:
  1. My Profile   — LLP summary + KPI cards + mastery chart
  2. Weaknesses   — diagnosis cards with severity + interventions
  3. Explainer    — personalised topic explanation
  4. Exam Sim     — simulate your answer to a question
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import json
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


def get_engine(llp: dict, provider: str) -> TwinEngine:
    key = f"engine_{llp['identity']['student_id']}_{provider}"
    if key not in st.session_state:
        engine = TwinEngine(provider=provider)
        engine.load_student(llp)
        st.session_state[key] = engine
    return st.session_state[key]


# ── Main render ───────────────────────────────────────────────────────────

def render_student_view(provider: str = "mock"):
    records = load_students()
    if not records:
        st.error("No student data found. Run: python data/generate_data.py")
        return

    # ── Student selector ──────────────────────────────────────────────
    with st.sidebar:
        st.markdown("<div class='section-title'>Select Student</div>", unsafe_allow_html=True)
        names = [f"{r['name']} ({r['student_id']})" for r in records]
        idx   = st.selectbox("Student", names, label_visibility="collapsed")
        sel_idx = names.index(idx)

    raw    = records[sel_idx]
    llp    = build_llp(raw)
    engine = get_engine(llp, provider)
    name   = llp["identity"]["name"]

    st.markdown(f"## 👤 {name}")
    st.markdown(
        f"<span style='opacity:0.5;font-size:0.82rem'>"
        f"{llp['identity']['student_id']} · "
        f"{llp['identity']['major']} · "
        f"Year {llp['identity']['year_level']}"
        f"</span>",
        unsafe_allow_html=True,
    )

    # ── Tabs ──────────────────────────────────────────────────────────
    tab1, tab2, tab3, tab4 = st.tabs([
        "📊 My Profile", "🔍 Weaknesses", "💡 Explainer", "📝 Exam Sim"
    ])

    # ─────────────────────────────────────────────────────────────────
    # TAB 1 — PROFILE
    # ─────────────────────────────────────────────────────────────────
    with tab1:
        scores  = llp["academic"]["scores"]
        pred    = engine.predict()
        self_r  = llp["self_reported"]
        beh     = llp["behavioral"]

        # KPI row
        risk_class = {
            "High": "risk-high", "Medium": "risk-medium", "Low": "risk-low"
        }.get(pred["risk_level"], "")

        c1, c2, c3, c4, c5 = st.columns(5)
        with c1:
            st.markdown(
                f"<div class='kpi-card'>"
                f"<div class='kpi-value'>{scores['overall_gpa']:.2f}</div>"
                f"<div class='kpi-label'>Current GPA</div></div>",
                unsafe_allow_html=True,
            )
        with c2:
            st.markdown(
                f"<div class='kpi-card'>"
                f"<div class='kpi-value'>{scores['quiz_avg']:.0f}</div>"
                f"<div class='kpi-label'>Quiz Avg</div></div>",
                unsafe_allow_html=True,
            )
        with c3:
            st.markdown(
                f"<div class='kpi-card'>"
                f"<div class='kpi-value'>{scores['exam_avg']:.0f}</div>"
                f"<div class='kpi-label'>Exam Avg</div></div>",
                unsafe_allow_html=True,
            )
        with c4:
            st.markdown(
                f"<div class='kpi-card'>"
                f"<div class='kpi-value'>{pred['predicted_next_exam_score']:.0f}</div>"
                f"<div class='kpi-label'>Predicted Exam</div></div>",
                unsafe_allow_html=True,
            )
        with c5:
            st.markdown(
                f"<div class='kpi-card'>"
                f"<div class='kpi-value {risk_class}'>{pred['risk_level']}</div>"
                f"<div class='kpi-label'>Risk Level</div></div>",
                unsafe_allow_html=True,
            )

        st.markdown("")

        # Mastery chart + profile details
        col_left, col_right = st.columns([3, 2])

        with col_left:
            st.markdown("<div class='section-title'>Topic Mastery</div>", unsafe_allow_html=True)
            mastery = llp["academic"]["mastery"]["mastery_map"]
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

        with col_right:
            st.markdown("<div class='section-title'>Learning Profile</div>", unsafe_allow_html=True)
            cog = llp["cognitive"]
            st.markdown(f"**Style:** {cog['learning_style'].capitalize()}")
            st.markdown(f"**Speed:** {cog['processing_speed'].capitalize()}")
            st.markdown(f"**Retention:** {int(cog['retention_score']*100)}%")
            st.markdown(f"**Attention span:** {cog['attention_span_min']} min")
            st.markdown(f"**Prefers:** {self_r['preferences']['preferred_explanation']}")

            st.markdown("<div class='section-title'>Goals</div>", unsafe_allow_html=True)
            st.markdown(f"**Target grade:** {self_r['goals']['target_grade']}")
            st.markdown(f"**Study hrs/day:** {self_r['goals']['study_hours_per_day']:.1f}")
            st.markdown(f"**Motivation:** {int(self_r['goals']['motivation_score']*100)}%")
            st.markdown(f"**Anxiety:** {int(self_r['confidence']['anxiety_level']*100)}%")

            trend = llp["academic"]["history"]["score_trend"]
            trend_icon = {"improving": "📈", "stable": "➡️", "declining": "📉"}.get(trend, "")
            st.markdown(f"**Trend:** {trend_icon} {trend.capitalize()}")

    # ─────────────────────────────────────────────────────────────────
    # TAB 2 — WEAKNESSES
    # ─────────────────────────────────────────────────────────────────
    with tab2:
        st.markdown("<div class='section-title'>Weakness Diagnosis</div>", unsafe_allow_html=True)

        with st.spinner("Diagnosing weak areas..."):
            diagnosis = engine.diagnose()

        if not diagnosis:
            st.success("No significant weaknesses detected!")
        else:
            for item in diagnosis:
                sev   = item.get("severity", "Minor")
                css   = {"Critical": "diag-critical", "Moderate": "diag-moderate", "Minor": "diag-minor"}.get(sev, "diag-minor")
                icon  = {"Critical": "🔴", "Moderate": "🟡", "Minor": "🟢"}.get(sev, "⚪")
                st.markdown(
                    f"<div class='diag-card {css}'>"
                    f"<strong>{icon} {item.get('topic','?')}</strong> "
                    f"<span style='opacity:0.5;font-size:0.8rem'>— {sev} · {item.get('mastery_pct','?')}% mastery</span><br>"
                    f"<span style='opacity:0.7;font-size:0.85rem'>📌 {item.get('root_cause','')}</span><br>"
                    f"<span style='font-size:0.85rem'>💊 <em>{item.get('intervention','')}</em></span>"
                    f"</div>",
                    unsafe_allow_html=True,
                )

        st.markdown("<div class='section-title'>Predicted Performance</div>", unsafe_allow_html=True)
        pred = engine.predict()
        c1, c2 = st.columns(2)
        with c1:
            st.markdown("**Key risk factors:**")
            for rf in pred.get("key_risk_factors", []):
                st.markdown(f"- {rf}")
        with c2:
            st.markdown("**Protective factors:**")
            for pf in pred.get("key_protective_factors", []):
                st.markdown(f"+ {pf}")

        st.markdown("**Recommended actions:**")
        for i, a in enumerate(pred.get("recommended_actions", []), 1):
            st.markdown(f"{i}. {a}")

    # ─────────────────────────────────────────────────────────────────
    # TAB 3 — EXPLAINER
    # ─────────────────────────────────────────────────────────────────
    with tab3:
        st.markdown("<div class='section-title'>Personalised Explanation</div>", unsafe_allow_html=True)

        mastery  = llp["academic"]["mastery"]["mastery_map"]
        topics   = list(mastery.keys()) if mastery else [llp["identity"]["major"]]
        weak     = llp["academic"]["mastery"]["weak_topics"]
        default  = topics.index(weak[0]) if weak and weak[0] in topics else 0

        col1, col2 = st.columns([2, 1])
        with col1:
            topic = st.selectbox("Choose a topic to explain", topics, index=default)
        with col2:
            extra = st.text_input("Extra focus (optional)", placeholder="e.g. focus on examples")

        if st.button("Generate Explanation", type="primary"):
            with st.spinner(f"Generating explanation for {topic}..."):
                result = engine.explain(topic=topic, extra_context=extra, force=True)

            pct   = result["mastery_pct"]
            color = "#ff6b6b" if pct < 40 else "#ffd93d" if pct < 65 else "#6bcb77"

            st.markdown(
                f"<div style='font-size:0.8rem;opacity:0.5;margin-bottom:0.8rem'>"
                f"Style: <strong>{result['style_used']}</strong> · "
                f"Tone: <strong>{result['tone']}</strong> · "
                f"Mastery: <strong style='color:{color}'>{pct}%</strong>"
                f"</div>",
                unsafe_allow_html=True,
            )
            st.markdown(
                f"<div class='explanation-box'>{result['explanation']}</div>",
                unsafe_allow_html=True,
            )
            if result.get("check_question"):
                st.markdown(
                    f"<div class='check-question'>✏️ {result['check_question']}</div>",
                    unsafe_allow_html=True,
                )

    # ─────────────────────────────────────────────────────────────────
    # TAB 4 — EXAM SIMULATOR
    # ─────────────────────────────────────────────────────────────────
    with tab4:
        st.markdown("<div class='section-title'>Exam Answer Simulator</div>", unsafe_allow_html=True)
        st.markdown(
            "<span style='opacity:0.55;font-size:0.85rem'>"
            "See how you would likely answer an exam question at your current level."
            "</span>",
            unsafe_allow_html=True,
        )

        mastery = llp["academic"]["mastery"]["mastery_map"]
        topics  = list(mastery.keys()) if mastery else [llp["identity"]["major"]]
        weak    = llp["academic"]["mastery"]["weak_topics"]
        default = topics.index(weak[0]) if weak and weak[0] in topics else 0

        sim_topic = st.selectbox("Topic area", topics, index=default, key="sim_topic")
        question  = st.text_area(
            "Enter exam question",
            value=f"Explain the core concept of {sim_topic} and give a real-world example.",
            height=80,
        )

        if st.button("Simulate My Answer", type="primary"):
            with st.spinner("Simulating your answer..."):
                result = engine.simulate(question=question, topic=sim_topic, force=True)

            quality = result["quality_estimate"]
            q_color = {"Excellent": "#6bcb77", "Good": "#4ecdc4",
                       "Partial": "#ffd93d", "Poor": "#ff6b6b"}.get(quality, "#fff")

            st.markdown(
                f"<div style='font-size:0.8rem;opacity:0.5;margin-bottom:0.8rem'>"
                f"Topic mastery: <strong style='color:{q_color}'>{result['mastery_pct']}%</strong> · "
                f"Estimated quality: <strong style='color:{q_color}'>{quality}</strong>"
                f"</div>",
                unsafe_allow_html=True,
            )

            st.markdown("**Your simulated answer:**")
            st.markdown(
                f"<div class='explanation-box'>{result['simulated_answer']}</div>",
                unsafe_allow_html=True,
            )

            st.markdown("")
            st.markdown("**Tutor note:**")
            st.info(result["tutor_note"])
