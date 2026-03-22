"""
EduTwin — Main App
==================
Entry point with authentication routing.

Run:
    streamlit run ui/app.py
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import os
import importlib.util
import streamlit as st
from database.db import init_db
from auth.auth import is_logged_in, get_current_user, logout

init_db()

st.set_page_config(page_title="EduTwin", page_icon="🎓", layout="wide")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@300;400;500;600&display=swap');
html, body, [class*="css"] { font-family: 'DM Sans', sans-serif; }
#MainMenu, footer, header { visibility: hidden; }
.block-container { padding-top: 1.5rem; }
[data-testid="stSidebar"] { background: linear-gradient(180deg,#0f0f1a,#1a1a2e); border-right:1px solid rgba(255,255,255,0.06); }
[data-testid="stSidebar"] * { color: #e2e2f0 !important; }
.kpi-card { background:rgba(255,255,255,0.03); border:1px solid rgba(255,255,255,0.08); border-radius:12px; padding:1.2rem 1.4rem; text-align:center; }
.kpi-value { font-size:2rem; font-weight:600; letter-spacing:-0.02em; line-height:1; margin-bottom:0.3rem; }
.kpi-label { font-size:0.75rem; text-transform:uppercase; letter-spacing:0.08em; opacity:0.55; }
.risk-high { color:#ff6b6b; } .risk-medium { color:#ffd93d; } .risk-low { color:#6bcb77; }
.section-title { font-size:0.7rem; text-transform:uppercase; letter-spacing:0.12em; opacity:0.45; margin-bottom:0.6rem; margin-top:1.4rem; }
.diag-card { border-left:3px solid; padding:0.8rem 1rem; border-radius:0 8px 8px 0; margin-bottom:0.6rem; background:rgba(255,255,255,0.02); }
.diag-critical{border-color:#ff6b6b;} .diag-moderate{border-color:#ffd93d;} .diag-minor{border-color:#6bcb77;}
.mastery-row{display:flex;align-items:center;gap:0.8rem;margin-bottom:0.5rem;font-size:0.85rem;}
.mastery-label{width:160px;flex-shrink:0;}
.mastery-bar-bg{flex:1;height:6px;background:rgba(255,255,255,0.08);border-radius:3px;overflow:hidden;}
.mastery-bar-fill{height:100%;border-radius:3px;}
.mastery-pct{width:36px;text-align:right;opacity:0.6;font-size:0.78rem;}
.explanation-box{background:rgba(255,255,255,0.03);border:1px solid rgba(255,255,255,0.08);border-radius:10px;padding:1.4rem;line-height:1.75;font-size:0.92rem;}
.check-question{margin-top:1rem;padding:0.8rem 1rem;background:rgba(107,203,119,0.08);border-left:3px solid #6bcb77;border-radius:0 6px 6px 0;font-style:italic;font-size:0.88rem;}
</style>
""", unsafe_allow_html=True)


def load_view(filename: str):
    base = os.path.dirname(os.path.abspath(__file__))
    path = os.path.join(base, "views", filename)
    spec = importlib.util.spec_from_file_location("view", path)
    mod  = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def show_login():
    col1, col2, col3 = st.columns([1, 1.2, 1])
    with col2:
        st.markdown("## 🎓 EduTwin")
        st.markdown("#### Sign In")
        with st.form("login"):
            email    = st.text_input("Email")
            password = st.text_input("Password", type="password")
            if st.form_submit_button("Sign In", use_container_width=True, type="primary"):
                from auth.auth import login
                ok, msg = login(email, password)
                if ok:
                    st.rerun()
                else:
                    st.error(msg)
        if st.button("No account? Sign up →"):
            st.session_state["auth_page"] = "signup"
            st.rerun()


def show_signup():
    col1, col2, col3 = st.columns([1, 1.2, 1])
    with col2:
        st.markdown("## 🎓 EduTwin")
        st.markdown("#### Create Account")
        with st.form("signup"):
            name     = st.text_input("Full name")
            email    = st.text_input("Email")
            role     = st.selectbox("Role", ["student", "teacher"])
            password = st.text_input("Password", type="password")
            confirm  = st.text_input("Confirm password", type="password")
            if st.form_submit_button("Create Account", use_container_width=True, type="primary"):
                if password != confirm:
                    st.error("Passwords do not match.")
                else:
                    from auth.auth import signup
                    ok, msg = signup(name, email, password, role)
                    if ok:
                        st.success(msg + " Please sign in.")
                        st.session_state["auth_page"] = "login"
                        st.rerun()
                    else:
                        st.error(msg)
        if st.button("← Back to sign in"):
            st.session_state["auth_page"] = "login"
            st.rerun()


# ── Main routing ──────────────────────────────────────────────────────────

if not is_logged_in():
    page = st.session_state.get("auth_page", "login")
    show_signup() if page == "signup" else show_login()

else:
    user = get_current_user()

    with st.sidebar:
        st.markdown("## 🎓 EduTwin")
        st.markdown(
            f"<div style='opacity:0.6;font-size:0.82rem'>Signed in as<br>"
            f"<strong>{user['name']}</strong> · {user['role']}</div>",
            unsafe_allow_html=True,
        )
        st.markdown("---")

        if user["role"] == "student":
            view = st.radio("Go to", ["My Dashboard", "Update Profile"], label_visibility="collapsed")
        else:
            view = "Teacher Dashboard"

        st.markdown("<div class='section-title'>LLM Provider</div>", unsafe_allow_html=True)
        provider = st.selectbox("provider", ["mock", "groq"], label_visibility="collapsed")
        if provider == "groq" and not os.environ.get("GROQ_API_KEY"):
            st.warning("GROQ_API_KEY not set — using mock")
            provider = "mock"
        elif provider == "groq":
            st.success("Groq ready")

        st.markdown("---")
        if st.button("Sign Out", use_container_width=True):
            logout()

    if user["role"] == "teacher":
        load_view("teacher_view.py").render_teacher_view(provider=provider)
    elif view == "Update Profile":
        load_view("profile_form.py").render_profile_form(user=user)
    else:
        load_view("student_view.py").render_student_view(user=user, provider=provider)
