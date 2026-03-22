"""
EduTwin — CRUD Operations
==========================
All database read/write operations in one place.
Every function opens and closes its own connection.

Usage:
    from database.crud import get_user_by_email, save_performance
"""

import sqlite3
from typing import Any
from database.db import get_connection


# ── Users ─────────────────────────────────────────────────────────────────

def create_user(name: str, email: str, password_hash: str, role: str = "student") -> int:
    """Insert a new user. Returns new user ID."""
    conn = get_connection()
    try:
        cur = conn.execute(
            "INSERT INTO users (name, email, password_hash, role) VALUES (?,?,?,?)",
            (name, email, password_hash, role)
        )
        conn.commit()
        return cur.lastrowid
    finally:
        conn.close()


def get_user_by_email(email: str) -> dict | None:
    """Fetch user row by email. Returns dict or None."""
    conn = get_connection()
    try:
        row = conn.execute(
            "SELECT * FROM users WHERE email = ?", (email,)
        ).fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


def get_user_by_id(user_id: int) -> dict | None:
    conn = get_connection()
    try:
        row = conn.execute(
            "SELECT * FROM users WHERE id = ?", (user_id,)
        ).fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


def get_all_students() -> list[dict]:
    """Return all users with role='student'."""
    conn = get_connection()
    try:
        rows = conn.execute(
            "SELECT * FROM users WHERE role = 'student' ORDER BY name"
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


# ── Student Profiles ──────────────────────────────────────────────────────

def upsert_profile(user_id: int, data: dict) -> None:
    """Insert or update a student profile."""
    conn = get_connection()
    try:
        existing = conn.execute(
            "SELECT id FROM student_profiles WHERE user_id = ?", (user_id,)
        ).fetchone()

        if existing:
            conn.execute("""
                UPDATE student_profiles SET
                    major=?, year_level=?, enrolled_on=?,
                    learning_style=?, processing_speed=?,
                    attention_span_min=?, preferred_explanation=?,
                    updated_at=datetime('now')
                WHERE user_id=?
            """, (
                data.get("major", "Computer Science"),
                data.get("year_level", 1),
                data.get("enrolled_on", "2023-09-01"),
                data.get("learning_style", "visual"),
                data.get("processing_speed", "average"),
                data.get("attention_span_min", 30),
                data.get("preferred_explanation", "examples"),
                user_id,
            ))
        else:
            conn.execute("""
                INSERT INTO student_profiles
                    (user_id, major, year_level, enrolled_on,
                     learning_style, processing_speed,
                     attention_span_min, preferred_explanation)
                VALUES (?,?,?,?,?,?,?,?)
            """, (
                user_id,
                data.get("major", "Computer Science"),
                data.get("year_level", 1),
                data.get("enrolled_on", "2023-09-01"),
                data.get("learning_style", "visual"),
                data.get("processing_speed", "average"),
                data.get("attention_span_min", 30),
                data.get("preferred_explanation", "examples"),
            ))
        conn.commit()
    finally:
        conn.close()


def get_profile(user_id: int) -> dict | None:
    conn = get_connection()
    try:
        row = conn.execute(
            "SELECT * FROM student_profiles WHERE user_id = ?", (user_id,)
        ).fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


# ── Performance Data ──────────────────────────────────────────────────────

def upsert_performance(user_id: int, subject: str, data: dict) -> None:
    """Insert or update performance record for a subject."""
    conn = get_connection()
    try:
        existing = conn.execute(
            "SELECT id FROM performance_data WHERE user_id=? AND subject=?",
            (user_id, subject)
        ).fetchone()

        if existing:
            conn.execute("""
                UPDATE performance_data SET
                    quiz_score=?, assignment_score=?, exam_score=?,
                    mastery_score=?, recorded_at=datetime('now')
                WHERE user_id=? AND subject=?
            """, (
                data.get("quiz_score", 0),
                data.get("assignment_score", 0),
                data.get("exam_score", 0),
                data.get("mastery_score", 0.5),
                user_id, subject,
            ))
        else:
            conn.execute("""
                INSERT INTO performance_data
                    (user_id, subject, quiz_score, assignment_score,
                     exam_score, mastery_score)
                VALUES (?,?,?,?,?,?)
            """, (
                user_id, subject,
                data.get("quiz_score", 0),
                data.get("assignment_score", 0),
                data.get("exam_score", 0),
                data.get("mastery_score", 0.5),
            ))
        conn.commit()
    finally:
        conn.close()


def get_performance(user_id: int) -> list[dict]:
    conn = get_connection()
    try:
        rows = conn.execute(
            "SELECT * FROM performance_data WHERE user_id=? ORDER BY subject",
            (user_id,)
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


# ── Behavioral Data ───────────────────────────────────────────────────────

def upsert_behavioral(user_id: int, data: dict) -> None:
    conn = get_connection()
    try:
        existing = conn.execute(
            "SELECT id FROM behavioral_data WHERE user_id=?", (user_id,)
        ).fetchone()

        if existing:
            conn.execute("""
                UPDATE behavioral_data SET
                    login_freq_per_week=?, avg_session_minutes=?,
                    submission_rate=?, late_submission_pct=?,
                    resources_used=?, peer_interaction=?,
                    forum_posts=?, updated_at=datetime('now')
                WHERE user_id=?
            """, (
                data.get("login_freq_per_week", 3.0),
                data.get("avg_session_minutes", 45.0),
                data.get("submission_rate", 0.8),
                data.get("late_submission_pct", 0.1),
                data.get("resources_used", 3),
                data.get("peer_interaction", "medium"),
                data.get("forum_posts", 0),
                user_id,
            ))
        else:
            conn.execute("""
                INSERT INTO behavioral_data
                    (user_id, login_freq_per_week, avg_session_minutes,
                     submission_rate, late_submission_pct, resources_used,
                     peer_interaction, forum_posts)
                VALUES (?,?,?,?,?,?,?,?)
            """, (
                user_id,
                data.get("login_freq_per_week", 3.0),
                data.get("avg_session_minutes", 45.0),
                data.get("submission_rate", 0.8),
                data.get("late_submission_pct", 0.1),
                data.get("resources_used", 3),
                data.get("peer_interaction", "medium"),
                data.get("forum_posts", 0),
            ))
        conn.commit()
    finally:
        conn.close()


def get_behavioral(user_id: int) -> dict | None:
    conn = get_connection()
    try:
        row = conn.execute(
            "SELECT * FROM behavioral_data WHERE user_id=?", (user_id,)
        ).fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


# ── Self Reports ──────────────────────────────────────────────────────────

def upsert_self_report(user_id: int, subject: str, data: dict) -> None:
    conn = get_connection()
    try:
        existing = conn.execute(
            "SELECT id FROM self_reports WHERE user_id=? AND subject=?",
            (user_id, subject)
        ).fetchone()

        if existing:
            conn.execute("""
                UPDATE self_reports SET
                    confidence_score=?, anxiety_level=?,
                    motivation_score=?, target_grade=?,
                    study_hours_per_day=?, updated_at=datetime('now')
                WHERE user_id=? AND subject=?
            """, (
                data.get("confidence_score", 0.5),
                data.get("anxiety_level", 0.5),
                data.get("motivation_score", 0.5),
                data.get("target_grade", "B"),
                data.get("study_hours_per_day", 2.0),
                user_id, subject,
            ))
        else:
            conn.execute("""
                INSERT INTO self_reports
                    (user_id, subject, confidence_score, anxiety_level,
                     motivation_score, target_grade, study_hours_per_day)
                VALUES (?,?,?,?,?,?,?)
            """, (
                user_id, subject,
                data.get("confidence_score", 0.5),
                data.get("anxiety_level", 0.5),
                data.get("motivation_score", 0.5),
                data.get("target_grade", "B"),
                data.get("study_hours_per_day", 2.0),
            ))
        conn.commit()
    finally:
        conn.close()


def get_self_reports(user_id: int) -> list[dict]:
    conn = get_connection()
    try:
        rows = conn.execute(
            "SELECT * FROM self_reports WHERE user_id=? ORDER BY subject",
            (user_id,)
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def upsert_global_self_report(user_id: int, data: dict) -> None:
    """Save global (non-subject) self-report fields like anxiety + motivation."""
    upsert_self_report(user_id, "__global__", data)


def get_global_self_report(user_id: int) -> dict | None:
    conn = get_connection()
    try:
        row = conn.execute(
            "SELECT * FROM self_reports WHERE user_id=? AND subject='__global__'",
            (user_id,)
        ).fetchone()
        return dict(row) if row else None
    finally:
        conn.close()
