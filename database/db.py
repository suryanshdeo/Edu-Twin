"""
EduTwin — Database Connection
==============================
Handles SQLite connection and first-time table creation.

Usage:
    from database.db import get_connection, init_db

    init_db()                    # call once at app startup
    conn = get_connection()      # get a connection anywhere
"""

import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / "data" / "edutwin.db"


def get_connection() -> sqlite3.Connection:
    """Return a SQLite connection with row_factory set to Row."""
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def init_db() -> None:
    """Create all tables if they don't exist. Safe to call multiple times."""
    conn = get_connection()
    cursor = conn.cursor()

    # ── users ─────────────────────────────────────────────────────────
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            name          TEXT    NOT NULL,
            email         TEXT    NOT NULL UNIQUE,
            password_hash TEXT    NOT NULL,
            role          TEXT    NOT NULL DEFAULT 'student',
            created_at    TEXT    NOT NULL DEFAULT (datetime('now'))
        )
    """)

    # ── student_profiles ──────────────────────────────────────────────
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS student_profiles (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id       INTEGER NOT NULL UNIQUE REFERENCES users(id),
            major         TEXT    NOT NULL DEFAULT 'Computer Science',
            year_level    INTEGER NOT NULL DEFAULT 1,
            enrolled_on   TEXT    NOT NULL DEFAULT (date('now')),
            learning_style      TEXT DEFAULT 'visual',
            processing_speed    TEXT DEFAULT 'average',
            attention_span_min  INTEGER DEFAULT 30,
            preferred_explanation TEXT DEFAULT 'examples',
            updated_at    TEXT NOT NULL DEFAULT (datetime('now'))
        )
    """)

    # ── performance_data ──────────────────────────────────────────────
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS performance_data (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id         INTEGER NOT NULL REFERENCES users(id),
            subject         TEXT    NOT NULL,
            quiz_score      REAL    DEFAULT 0,
            assignment_score REAL   DEFAULT 0,
            exam_score      REAL    DEFAULT 0,
            mastery_score   REAL    DEFAULT 0.5,
            recorded_at     TEXT    NOT NULL DEFAULT (datetime('now'))
        )
    """)

    # ── behavioral_data ───────────────────────────────────────────────
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS behavioral_data (
            id                    INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id               INTEGER NOT NULL REFERENCES users(id),
            login_freq_per_week   REAL    DEFAULT 3.0,
            avg_session_minutes   REAL    DEFAULT 45.0,
            submission_rate       REAL    DEFAULT 0.8,
            late_submission_pct   REAL    DEFAULT 0.1,
            resources_used        INTEGER DEFAULT 3,
            peer_interaction      TEXT    DEFAULT 'medium',
            forum_posts           INTEGER DEFAULT 0,
            updated_at            TEXT    NOT NULL DEFAULT (datetime('now'))
        )
    """)

    # ── self_reports ──────────────────────────────────────────────────
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS self_reports (
            id               INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id          INTEGER NOT NULL REFERENCES users(id),
            subject          TEXT    NOT NULL,
            confidence_score REAL    DEFAULT 0.5,
            anxiety_level    REAL    DEFAULT 0.5,
            motivation_score REAL    DEFAULT 0.5,
            target_grade     TEXT    DEFAULT 'B',
            study_hours_per_day REAL DEFAULT 2.0,
            updated_at       TEXT    NOT NULL DEFAULT (datetime('now'))
        )
    """)

    conn.commit()
    conn.close()
    print(f"[db] Database ready at {DB_PATH}")
