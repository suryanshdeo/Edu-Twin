"""
EduTwin — Profile Form
=======================
Lets a student enter/update their academic, behavioral,
and self-reported data. Saves to database on submit.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import streamlit as st
from database.crud import (
    upsert_profile, upsert_performance, upsert_behavioral,
    upsert_self_report, upsert_global_self_report,
    get_profile, get_performance, get_behavioral, get_self_reports, get_global_self_report,
)

SUBJECTS_BY_MAJOR = {
    "Computer Science": ["Data Structures", "Algorithms", "OS", "Networking", "Databases"],
    "Mathematics":      ["Calculus", "Algebra", "Statistics", "Geometry", "Linear Algebra"],
    "Physics":          ["Mechanics", "Thermodynamics", "Optics", "Electromagnetism", "Quantum"],
    "Chemistry":        ["Organic", "Inorganic", "Physical Chemistry", "Electrochemistry", "Bonding"],
    "Data Science":     ["Statistics", "ML Fundamentals", "Data Wrangling", "Visualization", "Deep Learning"],
}
ALL_MAJORS = list(SUBJECTS_BY_MAJOR.keys())


def render_profile_form(user: dict):
    user_id = user["id"]
    st.markdown(f"## ✏️ Update Your Profile")
    st.markdown(
        "<span style='opacity:0.5;font-size:0.85rem'>"
        "Keep your profile accurate so your digital twin reflects your real learning state."
        "</span>",
        unsafe_allow_html=True,
    )

    # Load existing data for pre-filling
    existing_profile = get_profile(user_id) or {}
    existing_beh     = get_behavioral(user_id) or {}
    existing_global  = get_global_self_report(user_id) or {}
    existing_perf    = {r["subject"]: r for r in get_performance(user_id)}
    existing_sr      = {r["subject"]: r for r in get_self_reports(user_id) if r["subject"] != "__global__"}

    tab1, tab2, tab3, tab4 = st.tabs([
        "🎓 Academic Info", "📚 Subject Scores", "🕐 Study Habits", "💭 Self-Assessment"
    ])

    # ── TAB 1: Academic Info ──────────────────────────────────────────
    with tab1:
        st.markdown("<div class='section-title'>Basic Information</div>", unsafe_allow_html=True)
        col1, col2 = st.columns(2)
        with col1:
            major = st.selectbox(
                "Your major",
                ALL_MAJORS,
                index=ALL_MAJORS.index(existing_profile.get("major", "Computer Science"))
                if existing_profile.get("major") in ALL_MAJORS else 0,
            )
            year_level = st.selectbox(
                "Year of study",
                [1, 2, 3, 4],
                index=int(existing_profile.get("year_level", 1)) - 1,
            )
        with col2:
            learning_style = st.selectbox(
                "Learning style",
                ["visual", "auditory", "reading", "kinesthetic"],
                index=["visual", "auditory", "reading", "kinesthetic"].index(
                    existing_profile.get("learning_style", "visual")
                ),
            )
            processing_speed = st.selectbox(
                "Processing speed",
                ["slow", "average", "fast"],
                index=["slow", "average", "fast"].index(
                    existing_profile.get("processing_speed", "average")
                ),
            )

        col3, col4 = st.columns(2)
        with col3:
            attention_span = st.slider(
                "Attention span (minutes)",
                10, 90,
                int(existing_profile.get("attention_span_min", 30)),
            )
        with col4:
            pref_explanation = st.selectbox(
                "Preferred explanation style",
                ["examples", "step-by-step", "analogies", "diagrams", "brief-summary"],
                index=["examples", "step-by-step", "analogies", "diagrams", "brief-summary"].index(
                    existing_profile.get("preferred_explanation", "examples")
                ),
            )

        if st.button("Save Academic Info", type="primary"):
            upsert_profile(user_id, {
                "major":                  major,
                "year_level":             year_level,
                "learning_style":         learning_style,
                "processing_speed":       processing_speed,
                "attention_span_min":     attention_span,
                "preferred_explanation":  pref_explanation,
                "enrolled_on":            existing_profile.get("enrolled_on", "2023-09-01"),
            })
            st.success("Academic info saved!")

    # ── TAB 2: Subject Scores ─────────────────────────────────────────
    with tab2:
        subjects = SUBJECTS_BY_MAJOR.get(existing_profile.get("major", "Computer Science"),
                                          SUBJECTS_BY_MAJOR["Computer Science"])
        st.markdown(
            "<div class='section-title'>Enter your scores for each subject (0–100)</div>",
            unsafe_allow_html=True,
        )

        perf_data = {}
        for subject in subjects:
            existing = existing_perf.get(subject, {})
            st.markdown(f"**{subject}**")
            c1, c2, c3, c4 = st.columns(4)
            with c1:
                quiz = st.number_input(
                    "Quiz", 0.0, 100.0,
                    float(existing.get("quiz_score", 0.0)),
                    key=f"quiz_{subject}"
                )
            with c2:
                assign = st.number_input(
                    "Assignment", 0.0, 100.0,
                    float(existing.get("assignment_score", 0.0)),
                    key=f"assign_{subject}"
                )
            with c3:
                exam = st.number_input(
                    "Exam", 0.0, 100.0,
                    float(existing.get("exam_score", 0.0)),
                    key=f"exam_{subject}"
                )
            with c4:
                mastery = st.slider(
                    "Mastery", 0.0, 1.0,
                    float(existing.get("mastery_score", 0.5)),
                    0.05,
                    key=f"mastery_{subject}",
                    help="Your self-assessed mastery (0=none, 1=expert)"
                )
            perf_data[subject] = {
                "quiz_score": quiz, "assignment_score": assign,
                "exam_score": exam, "mastery_score": mastery,
            }
            st.markdown("---")

        if st.button("Save Subject Scores", type="primary"):
            for subject, data in perf_data.items():
                upsert_performance(user_id, subject, data)
            st.success(f"Scores saved for {len(perf_data)} subjects!")

    # ── TAB 3: Study Habits ───────────────────────────────────────────
    with tab3:
        st.markdown("<div class='section-title'>Behavioral + Study Habits</div>", unsafe_allow_html=True)
        col1, col2 = st.columns(2)
        with col1:
            login_freq = st.slider(
                "How often do you log in to study per week?",
                0.0, 7.0, float(existing_beh.get("login_freq_per_week", 3.0)), 0.5
            )
            session_min = st.slider(
                "Average study session (minutes)",
                5, 180, int(existing_beh.get("avg_session_minutes", 45))
            )
            resources = st.number_input(
                "Resources used this month",
                0, 50, int(existing_beh.get("resources_used", 3))
            )
        with col2:
            submission_rate = st.slider(
                "Submission rate (% of assignments submitted)",
                0, 100, int(float(existing_beh.get("submission_rate", 0.8)) * 100)
            ) / 100
            late_pct = st.slider(
                "Late submission rate (%)",
                0, 100, int(float(existing_beh.get("late_submission_pct", 0.1)) * 100)
            ) / 100
            peer = st.selectbox(
                "Peer interaction level",
                ["low", "medium", "high"],
                index=["low", "medium", "high"].index(existing_beh.get("peer_interaction", "medium")),
            )
            forum_posts = st.number_input(
                "Forum posts this term",
                0, 100, int(existing_beh.get("forum_posts", 0))
            )

        if st.button("Save Study Habits", type="primary"):
            upsert_behavioral(user_id, {
                "login_freq_per_week": login_freq,
                "avg_session_minutes": session_min,
                "submission_rate":     submission_rate,
                "late_submission_pct": late_pct,
                "resources_used":      resources,
                "peer_interaction":    peer,
                "forum_posts":         forum_posts,
            })
            st.success("Study habits saved!")

    # ── TAB 4: Self-Assessment ────────────────────────────────────────
    with tab4:
        st.markdown("<div class='section-title'>Overall Wellbeing</div>", unsafe_allow_html=True)
        col1, col2 = st.columns(2)
        with col1:
            anxiety = st.slider(
                "Exam anxiety level (0=none, 1=very high)",
                0.0, 1.0, float(existing_global.get("anxiety_level", 0.5)), 0.05
            )
            motivation = st.slider(
                "Motivation level (0=low, 1=high)",
                0.0, 1.0, float(existing_global.get("motivation_score", 0.5)), 0.05
            )
        with col2:
            study_hrs = st.slider(
                "Study hours per day",
                0.0, 12.0, float(existing_global.get("study_hours_per_day", 2.0)), 0.5
            )
            target_grade = st.selectbox(
                "Target grade",
                ["A", "B", "C"],
                index=["A", "B", "C"].index(existing_global.get("target_grade", "B")),
            )

        st.markdown("<div class='section-title'>Confidence Per Subject</div>", unsafe_allow_html=True)
        subjects = SUBJECTS_BY_MAJOR.get(existing_profile.get("major", "Computer Science"),
                                          SUBJECTS_BY_MAJOR["Computer Science"])
        conf_data = {}
        for subject in subjects:
            existing_s = existing_sr.get(subject, {})
            conf = st.slider(
                f"Confidence in {subject}",
                0.0, 1.0,
                float(existing_s.get("confidence_score", 0.5)),
                0.05,
                key=f"conf_{subject}",
            )
            conf_data[subject] = conf

        if st.button("Save Self-Assessment", type="primary"):
            upsert_global_self_report(user_id, {
                "anxiety_level":     anxiety,
                "motivation_score":  motivation,
                "study_hours_per_day": study_hrs,
                "target_grade":      target_grade,
            })
            for subject, conf in conf_data.items():
                upsert_self_report(user_id, subject, {"confidence_score": conf})
            st.success("Self-assessment saved!")
