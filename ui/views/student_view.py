"""
EduTwin — Student View (Real Data)
====================================
Builds LLP from database and runs all twin capabilities.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import streamlit as st
from core.profile_builder import build_llp_from_db, summarise_llp
from twin.twin_engine import TwinEngine
from database.crud import get_profile


def get_engine(user_id: int, provider: str) -> TwinEngine:
    key = f"engine_{user_id}_{provider}"
    if key not in st.session_state:
        llp    = build_llp_from_db(user_id)
        engine = TwinEngine(provider=provider)
        engine.load_student(llp)
        st.session_state[key] = engine
    return st.session_state[key]


def render_student_view(user: dict, provider: str = "mock"):
    user_id = user["id"]
    profile = get_profile(user_id)

    if not profile:
        st.warning("Your profile is incomplete.")
        st.info("Go to **Update Profile** in the sidebar to enter your academic data first.")
        return

    # Build LLP fresh each render (reflects latest saved data)
    try:
        llp = build_llp_from_db(user_id)
    except Exception as e:
        st.error(f"Could not build your profile: {e}")
        return

    engine = get_engine(user_id, provider)
    # Reload engine with latest LLP
    engine.load_student(llp)

    name = llp["identity"]["name"]
    st.markdown(f"## 👤 {name}")
    st.markdown(
        f"<span style='opacity:0.5;font-size:0.82rem'>"
        f"{llp['identity']['student_id']} · "
        f"{llp['identity']['major']} · "
        f"Year {llp['identity']['year_level']}"
        f"</span>",
        unsafe_allow_html=True,
    )

    if not llp["academic"]["mastery"]["mastery_map"]:
        st.warning("No subject scores found yet.")
        st.info("Go to **Update Profile → Subject Scores** to enter your grades.")
        return

    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📊 My Profile", "🔍 Weaknesses", "💡 Explainer", "📝 Exam Sim", "📋 LLP Summary"
    ])

    # ── TAB 1: PROFILE ────────────────────────────────────────────────
    with tab1:
        scores = llp["academic"]["scores"]
        pred   = engine.predict()
        self_r = llp["self_reported"]
        beh    = llp["behavioral"]

        risk_class = {"High": "risk-high", "Medium": "risk-medium", "Low": "risk-low"}.get(pred["risk_level"], "")
        c1, c2, c3, c4, c5 = st.columns(5)
        for col, val, label in zip(
            [c1, c2, c3, c4, c5],
            [f"{scores['overall_gpa']:.2f}", f"{scores['quiz_avg']:.0f}",
             f"{scores['exam_avg']:.0f}", f"{pred['predicted_next_exam_score']:.0f}",
             pred['risk_level']],
            ["Current GPA", "Quiz Avg", "Exam Avg", "Predicted Exam", "Risk Level"],
        ):
            css = risk_class if label == "Risk Level" else ""
            with col:
                st.markdown(
                    f"<div class='kpi-card'><div class='kpi-value {css}'>{val}</div>"
                    f"<div class='kpi-label'>{label}</div></div>",
                    unsafe_allow_html=True,
                )

        st.markdown("")
        col_left, col_right = st.columns([3, 2])

        with col_left:
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

        with col_right:
            st.markdown("<div class='section-title'>Learning Profile</div>", unsafe_allow_html=True)
            cog = llp["cognitive"]
            st.markdown(f"**Style:** {cog['learning_style'].capitalize()}")
            st.markdown(f"**Speed:** {cog['processing_speed'].capitalize()}")
            st.markdown(f"**Prefers:** {self_r['preferences']['preferred_explanation']}")
            st.markdown(f"**Attention:** {cog['attention_span_min']} min")
            st.markdown("<div class='section-title'>Goals</div>", unsafe_allow_html=True)
            st.markdown(f"**Target:** {self_r['goals']['target_grade']}")
            st.markdown(f"**Study:** {self_r['goals']['study_hours_per_day']:.1f} hr/day")
            st.markdown(f"**Motivation:** {int(self_r['goals']['motivation_score']*100)}%")
            st.markdown(f"**Anxiety:** {int(self_r['confidence']['anxiety_level']*100)}%")
            trend = llp["academic"]["history"]["score_trend"]
            st.markdown(f"**Trend:** {'📈' if trend=='improving' else '📉' if trend=='declining' else '➡️'} {trend.capitalize()}")

    # ── TAB 2: WEAKNESSES ─────────────────────────────────────────────
    with tab2:
        st.markdown("<div class='section-title'>Weakness Diagnosis</div>", unsafe_allow_html=True)
        with st.spinner("Diagnosing..."):
            diagnosis = engine.diagnose()

        if not diagnosis:
            st.success("No significant weaknesses detected!")
        else:
            for item in diagnosis:
                sev  = item.get("severity", "Minor")
                css  = {"Critical":"diag-critical","Moderate":"diag-moderate","Minor":"diag-minor"}.get(sev,"diag-minor")
                icon = {"Critical":"🔴","Moderate":"🟡","Minor":"🟢"}.get(sev,"⚪")
                st.markdown(
                    f"<div class='diag-card {css}'>"
                    f"<strong>{icon} {item.get('topic','?')}</strong> "
                    f"<span style='opacity:0.5;font-size:0.8rem'>— {sev} · {item.get('mastery_pct','?')}% mastery</span><br>"
                    f"<span style='opacity:0.7;font-size:0.85rem'>📌 {item.get('root_cause','')}</span><br>"
                    f"<em style='font-size:0.85rem'>💊 {item.get('intervention','')}</em>"
                    f"</div>",
                    unsafe_allow_html=True,
                )

        pred = engine.predict()
        st.markdown("<div class='section-title'>Recommended Actions</div>", unsafe_allow_html=True)
        for i, a in enumerate(pred.get("recommended_actions", []), 1):
            st.markdown(f"{i}. {a}")

    # ── TAB 3: EXPLAINER ──────────────────────────────────────────────
    with tab3:
        mastery = llp["academic"]["mastery"]["mastery_map"]
        topics  = list(mastery.keys())
        weak    = llp["academic"]["mastery"]["weak_topics"]
        default = topics.index(weak[0]) if weak and weak[0] in topics else 0

        col1, col2 = st.columns([2, 1])
        with col1:
            topic = st.selectbox("Choose a topic", topics, index=default)
        with col2:
            extra = st.text_input("Extra focus", placeholder="e.g. focus on examples")

        if st.button("Generate Explanation", type="primary"):
            with st.spinner(f"Generating explanation for {topic}..."):
                result = engine.explain(topic=topic, extra_context=extra, force=True)

            pct   = result["mastery_pct"]
            color = "#ff6b6b" if pct < 40 else "#ffd93d" if pct < 65 else "#6bcb77"
            st.markdown(
                f"<div style='font-size:0.8rem;opacity:0.5;margin-bottom:0.8rem'>"
                f"Style: <strong>{result['style_used']}</strong> · "
                f"Tone: <strong>{result['tone']}</strong> · "
                f"Mastery: <strong style='color:{color}'>{pct}%</strong></div>",
                unsafe_allow_html=True,
            )
            st.markdown(f"<div class='explanation-box'>{result['explanation']}</div>", unsafe_allow_html=True)
            if result.get("check_question"):
                st.markdown(f"<div class='check-question'>✏️ {result['check_question']}</div>", unsafe_allow_html=True)

    # ── TAB 4: EXAM SIM ───────────────────────────────────────────────
    with tab4:
        mastery = llp["academic"]["mastery"]["mastery_map"]
        topics  = list(mastery.keys())
        weak    = llp["academic"]["mastery"]["weak_topics"]
        default = topics.index(weak[0]) if weak and weak[0] in topics else 0

        sim_topic = st.selectbox("Topic area", topics, index=default, key="sim_topic")
        question  = st.text_area(
            "Exam question",
            value=f"Explain the core concept of {sim_topic} and give a real-world example.",
            height=80,
        )

        if st.button("Simulate My Answer", type="primary"):
            with st.spinner("Simulating..."):
                result = engine.simulate(question=question, topic=sim_topic, force=True)
            q_color = {"Excellent":"#6bcb77","Good":"#4ecdc4","Partial":"#ffd93d","Poor":"#ff6b6b"}.get(result["quality_estimate"],"#fff")
            st.markdown(
                f"<div style='font-size:0.8rem;opacity:0.5;margin-bottom:0.8rem'>"
                f"Mastery: <strong style='color:{q_color}'>{result['mastery_pct']}%</strong> · "
                f"Quality: <strong style='color:{q_color}'>{result['quality_estimate']}</strong></div>",
                unsafe_allow_html=True,
            )
            st.markdown("**Simulated answer:**")
            st.markdown(f"<div class='explanation-box'>{result['simulated_answer']}</div>", unsafe_allow_html=True)
            st.markdown("")
            st.info(f"**Tutor note:** {result['tutor_note']}")

    # ── TAB 5: LLP SUMMARY ────────────────────────────────────────────
    with tab5:
        st.markdown("<div class='section-title'>Your Full Digital Twin Profile</div>", unsafe_allow_html=True)
        st.code(summarise_llp(llp), language=None)
        import json
        st.download_button(
            "Download LLP as JSON",
            data=json.dumps(llp, indent=2),
            file_name=f"llp_{user_id}.json",
            mime="application/json",
        )
