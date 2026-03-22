"""
EduTwin — Streamlit App
========================
Entry point. Handles role selection and routes to the correct view.

Run with:
    streamlit run ui/app.py
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import streamlit as st

# ── Page config ───────────────────────────────────────────────────────────
st.set_page_config(
    page_title="EduTwin",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Global CSS ────────────────────────────────────────────────────────────
st.markdown("""
<style>
    /* Font + base */
    @import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@300;400;500;600&family=DM+Mono&display=swap');
    html, body, [class*="css"] { font-family: 'DM Sans', sans-serif; }

    /* Hide default Streamlit chrome */
    #MainMenu, footer, header { visibility: hidden; }
    .block-container { padding-top: 1.5rem; padding-bottom: 2rem; }

    /* Sidebar */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #0f0f1a 0%, #1a1a2e 100%);
        border-right: 1px solid rgba(255,255,255,0.06);
    }
    [data-testid="stSidebar"] * { color: #e2e2f0 !important; }

    /* KPI cards */
    .kpi-card {
        background: rgba(255,255,255,0.03);
        border: 1px solid rgba(255,255,255,0.08);
        border-radius: 12px;
        padding: 1.2rem 1.4rem;
        text-align: center;
    }
    .kpi-value {
        font-size: 2rem;
        font-weight: 600;
        letter-spacing: -0.02em;
        line-height: 1;
        margin-bottom: 0.3rem;
    }
    .kpi-label {
        font-size: 0.75rem;
        text-transform: uppercase;
        letter-spacing: 0.08em;
        opacity: 0.55;
    }
    .risk-high   { color: #ff6b6b; }
    .risk-medium { color: #ffd93d; }
    .risk-low    { color: #6bcb77; }

    /* Section headers */
    .section-title {
        font-size: 0.7rem;
        text-transform: uppercase;
        letter-spacing: 0.12em;
        opacity: 0.45;
        margin-bottom: 0.6rem;
        margin-top: 1.4rem;
    }

    /* Diagnosis card */
    .diag-card {
        border-left: 3px solid;
        padding: 0.8rem 1rem;
        border-radius: 0 8px 8px 0;
        margin-bottom: 0.6rem;
        background: rgba(255,255,255,0.02);
    }
    .diag-critical { border-color: #ff6b6b; }
    .diag-moderate { border-color: #ffd93d; }
    .diag-minor    { border-color: #6bcb77; }

    /* Mastery bar */
    .mastery-row {
        display: flex;
        align-items: center;
        gap: 0.8rem;
        margin-bottom: 0.5rem;
        font-size: 0.85rem;
    }
    .mastery-label { width: 160px; flex-shrink: 0; }
    .mastery-bar-bg {
        flex: 1;
        height: 6px;
        background: rgba(255,255,255,0.08);
        border-radius: 3px;
        overflow: hidden;
    }
    .mastery-bar-fill {
        height: 100%;
        border-radius: 3px;
        transition: width 0.6s ease;
    }
    .mastery-pct { width: 36px; text-align: right; opacity: 0.6; font-size: 0.78rem; }

    /* Student table row hover */
    .stDataFrame tr:hover { background: rgba(255,255,255,0.04) !important; }

    /* Tab styling */
    .stTabs [data-baseweb="tab-list"] {
        gap: 0.5rem;
        border-bottom: 1px solid rgba(255,255,255,0.08);
    }
    .stTabs [data-baseweb="tab"] {
        font-size: 0.82rem;
        letter-spacing: 0.04em;
        padding: 0.5rem 1rem;
        border-radius: 6px 6px 0 0;
    }

    /* Explanation box */
    .explanation-box {
        background: rgba(255,255,255,0.03);
        border: 1px solid rgba(255,255,255,0.08);
        border-radius: 10px;
        padding: 1.4rem;
        line-height: 1.75;
        font-size: 0.92rem;
    }
    .check-question {
        margin-top: 1rem;
        padding: 0.8rem 1rem;
        background: rgba(107, 203, 119, 0.08);
        border-left: 3px solid #6bcb77;
        border-radius: 0 6px 6px 0;
        font-style: italic;
        font-size: 0.88rem;
    }
</style>
""", unsafe_allow_html=True)


# ── Sidebar: role + provider ──────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 🎓 EduTwin")
    st.markdown("<div class='section-title'>Select Role</div>", unsafe_allow_html=True)

    role = st.radio(
        label="role",
        options=["Student", "Teacher"],
        label_visibility="collapsed",
    )

    st.markdown("<div class='section-title'>LLM Provider</div>", unsafe_allow_html=True)
    provider = st.selectbox(
        label="provider",
        options=["mock", "groq"],
        label_visibility="collapsed",
        help="'mock' works without any API key",
    )

    if provider != "mock":
        import os
        key_name = "GROQ_API_KEY" if provider == "groq" else "GEMINI_API_KEY"
        key_set  = bool(os.environ.get(key_name))
        if key_set:
            st.success(f"{key_name} detected")
        else:
            st.warning(f"{key_name} not set — falling back to mock")
            provider = "mock"

    st.markdown("---")
    st.markdown(
        "<div style='font-size:0.72rem;opacity:0.35;line-height:1.6'>"
        "EduTwin v1.0<br>Phase 1 + 2 + 3<br>Built with Streamlit"
        "</div>",
        unsafe_allow_html=True,
    )

# ── Route to correct view ─────────────────────────────────────────────────
import importlib.util, os

def load_view(filename):
    # Always resolve relative to this file's actual location
    base = os.path.dirname(os.path.abspath(__file__))
    path = os.path.join(base, "views", filename)
    spec = importlib.util.spec_from_file_location("view", path)
    mod  = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod

if role == "Student":
    mod = load_view("student_view.py")
    mod.render_student_view(provider=provider)
else:
    mod = load_view("teacher_view.py")
    mod.render_teacher_view(provider=provider)