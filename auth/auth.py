"""
EduTwin — Authentication
=========================
Handles signup, login, password hashing, and Streamlit session state.

Usage:
    from auth.auth import signup, login, logout, get_current_user, require_auth
"""

import streamlit as st
import bcrypt
from database.crud import create_user, get_user_by_email

SESSION_KEY = "edutwin_user"


# ── Password hashing ──────────────────────────────────────────────────────

def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode("utf-8"), hashed.encode("utf-8"))


# ── Signup ────────────────────────────────────────────────────────────────

def signup(name: str, email: str, password: str, role: str = "student") -> tuple[bool, str]:
    """
    Register a new user.

    Returns:
        (success: bool, message: str)
    """
    # Validation
    if not name.strip():
        return False, "Name cannot be empty."
    if not email.strip() or "@" not in email:
        return False, "Please enter a valid email address."
    if len(password) < 6:
        return False, "Password must be at least 6 characters."

    # Check existing
    if get_user_by_email(email.strip().lower()):
        return False, "An account with this email already exists."

    try:
        password_hash = hash_password(password)
        user_id = create_user(
            name=name.strip(),
            email=email.strip().lower(),
            password_hash=password_hash,
            role=role,
        )
        return True, f"Account created successfully! (ID: {user_id})"
    except Exception as e:
        return False, f"Signup failed: {str(e)}"


# ── Login ─────────────────────────────────────────────────────────────────

def login(email: str, password: str) -> tuple[bool, str]:
    """
    Authenticate a user and store in session.

    Returns:
        (success: bool, message: str)
    """
    if not email.strip() or not password:
        return False, "Please enter both email and password."

    user = get_user_by_email(email.strip().lower())
    if not user:
        return False, "No account found with this email."

    if not verify_password(password, user["password_hash"]):
        return False, "Incorrect password."

    # Store in session (exclude password hash)
    st.session_state[SESSION_KEY] = {
        "id":    user["id"],
        "name":  user["name"],
        "email": user["email"],
        "role":  user["role"],
    }
    return True, f"Welcome back, {user['name']}!"


# ── Logout ────────────────────────────────────────────────────────────────

def logout() -> None:
    """Clear session state."""
    keys_to_clear = [k for k in st.session_state if k.startswith("edutwin")]
    for k in keys_to_clear:
        del st.session_state[k]
    st.rerun()


# ── Session helpers ───────────────────────────────────────────────────────

def get_current_user() -> dict | None:
    """Return current logged-in user dict or None."""
    return st.session_state.get(SESSION_KEY)


def is_logged_in() -> bool:
    return SESSION_KEY in st.session_state


def require_auth() -> dict:
    """
    Call at the top of any protected page.
    Redirects to login if not authenticated.
    Returns current user dict if authenticated.
    """
    user = get_current_user()
    if not user:
        st.warning("Please log in to continue.")
        st.stop()
    return user
