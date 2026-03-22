"""
EduTwin — Profile Builder
=========================
Builds a structured LLP dict from either:
  1. A database user_id  (real user flow)
  2. A flat raw dict     (synthetic data / testing)

Usage:
    from core.profile_builder import build_llp_from_db, build_llp, summarise_llp
"""

from __future__ import annotations
from datetime import datetime
from typing import Any


def build_llp_from_db(user_id: int) -> dict[str, Any]:
    """
    Fetch all DB records for a user and assemble a complete LLP dict.
    Structure is identical to build_llp() so all twin modules work unchanged.
    """
    from database.crud import (
        get_user_by_id, get_profile, get_performance,
        get_behavioral, get_self_reports, get_global_self_report,
    )

    user = get_user_by_id(user_id)
    if not user:
        raise ValueError(f"User {user_id} not found.")

    profile   = get_profile(user_id) or {}
    perf_rows = get_performance(user_id)
    beh       = get_behavioral(user_id) or {}
    sr_rows   = get_self_reports(user_id)
    global_sr = get_global_self_report(user_id) or {}

    # Academic aggregation
    mastery_map, quiz_scores, assign_scores, exam_scores = {}, [], [], []
    for row in perf_rows:
        if row["subject"] == "__global__":
            continue
        mastery_map[row["subject"]] = float(row["mastery_score"])
        quiz_scores.append(float(row["quiz_score"]))
        assign_scores.append(float(row["assignment_score"]))
        exam_scores.append(float(row["exam_score"]))

    def avg(lst): return round(sum(lst) / len(lst), 1) if lst else 50.0

    quiz_avg       = avg(quiz_scores)
    assignment_avg = avg(assign_scores)
    exam_avg       = avg(exam_scores)
    overall_gpa    = round((quiz_avg*0.30 + assignment_avg*0.30 + exam_avg*0.40) / 25.0, 2)
    weak, strong   = _derive_weak_strong(mastery_map)

    # Self-reports
    confidence_map = {}
    for row in sr_rows:
        if row["subject"] != "__global__":
            confidence_map[row["subject"]] = float(row["confidence_score"])

    return {
        "identity": {
            "student_id":      f"USR-{user_id:04d}",
            "name":            user["name"],
            "email":           user["email"],
            "age":             20,
            "year_level":      int(profile.get("year_level", 1)),
            "major":           profile.get("major", "Computer Science"),
            "enrolled_on":     profile.get("enrolled_on", "2023-09-01"),
            "last_updated":    datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
            "profile_version": "2.0",
        },
        "academic": {
            "scores": {
                "quiz_avg": quiz_avg, "assignment_avg": assignment_avg,
                "exam_avg": exam_avg, "overall_gpa": overall_gpa,
            },
            "mastery": {
                "mastery_map": mastery_map,
                "weak_topics": weak, "strong_topics": strong,
            },
            "history": {"total_attempts": len(perf_rows), "score_trend": "stable"},
        },
        "behavioral": {
            "engagement": {
                "login_freq_per_week": float(beh.get("login_freq_per_week", 3.0)),
                "avg_session_minutes": float(beh.get("avg_session_minutes", 45.0)),
                "resources_used":      int(beh.get("resources_used", 3)),
            },
            "habits": {
                "submission_rate":     float(beh.get("submission_rate", 0.8)),
                "late_submission_pct": float(beh.get("late_submission_pct", 0.1)),
            },
            "collaboration": {
                "peer_interaction": beh.get("peer_interaction", "medium"),
                "forum_posts":      int(beh.get("forum_posts", 0)),
            },
        },
        "cognitive": {
            "learning_style":     profile.get("learning_style", "visual"),
            "processing_speed":   profile.get("processing_speed", "average"),
            "retention_score":    0.6,
            "attention_span_min": int(profile.get("attention_span_min", 30)),
            "common_mistakes":    [],
        },
        "self_reported": {
            "confidence": {
                "confidence_map": confidence_map,
                "anxiety_level":  float(global_sr.get("anxiety_level", 0.5)),
            },
            "goals": {
                "target_grade":        global_sr.get("target_grade", "B"),
                "motivation_score":    float(global_sr.get("motivation_score", 0.5)),
                "study_hours_per_day": float(global_sr.get("study_hours_per_day", 2.0)),
            },
            "preferences": {
                "preferred_explanation": profile.get("preferred_explanation", "examples"),
            },
        },
    }


def build_llp(raw: dict[str, Any]) -> dict[str, Any]:
    """Build LLP from flat raw dict. Used for synthetic data and testing."""
    mastery_map     = _parse_map(raw.get("mastery_map", {}))
    confidence_map  = _parse_map(raw.get("confidence_map", {}))
    weak_topics     = _parse_list(raw.get("weak_topics", []))
    strong_topics   = _parse_list(raw.get("strong_topics", []))
    common_mistakes = _parse_list(raw.get("common_mistakes", []))

    if not weak_topics and mastery_map:
        weak_topics, strong_topics = _derive_weak_strong(mastery_map)

    return {
        "identity": {
            "student_id":      raw.get("student_id", "STU-0000"),
            "name":            raw.get("name", "Unknown"),
            "email":           raw.get("email", ""),
            "age":             int(raw.get("age", 18)),
            "year_level":      int(raw.get("year_level", 1)),
            "major":           raw.get("major", "General"),
            "enrolled_on":     raw.get("enrolled_on", "2023-09-01"),
            "last_updated":    datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
            "profile_version": raw.get("profile_version", "1.0"),
        },
        "academic": {
            "scores": {
                "quiz_avg":       float(raw.get("quiz_avg", 50.0)),
                "assignment_avg": float(raw.get("assignment_avg", 50.0)),
                "exam_avg":       float(raw.get("exam_avg", 50.0)),
                "overall_gpa":    float(raw.get("overall_gpa", 2.0)),
            },
            "mastery": {
                "mastery_map":   mastery_map,
                "weak_topics":   weak_topics,
                "strong_topics": strong_topics,
            },
            "history": {
                "total_attempts": int(raw.get("total_attempts", 0)),
                "score_trend":    raw.get("score_trend", "stable"),
            },
        },
        "behavioral": {
            "engagement": {
                "login_freq_per_week": float(raw.get("login_freq_per_week", 3.0)),
                "avg_session_minutes": float(raw.get("avg_session_minutes", 45.0)),
                "resources_used":      int(raw.get("resources_used", 0)),
            },
            "habits": {
                "submission_rate":     float(raw.get("submission_rate", 0.8)),
                "late_submission_pct": float(raw.get("late_submission_pct", 0.1)),
            },
            "collaboration": {
                "peer_interaction": raw.get("peer_interaction", "medium"),
                "forum_posts":      int(raw.get("forum_posts", 0)),
            },
        },
        "cognitive": {
            "learning_style":     raw.get("learning_style", "visual"),
            "processing_speed":   raw.get("processing_speed", "average"),
            "retention_score":    float(raw.get("retention_score", 0.5)),
            "attention_span_min": int(raw.get("attention_span_min", 30)),
            "common_mistakes":    common_mistakes,
        },
        "self_reported": {
            "confidence": {
                "confidence_map": confidence_map,
                "anxiety_level":  float(raw.get("anxiety_level", 0.5)),
            },
            "goals": {
                "target_grade":        raw.get("target_grade", "B"),
                "motivation_score":    float(raw.get("motivation_score", 0.5)),
                "study_hours_per_day": float(raw.get("study_hours_per_day", 2.0)),
            },
            "preferences": {
                "preferred_explanation": raw.get("preferred_explanation", "examples"),
            },
        },
    }


def summarise_llp(llp: dict[str, Any]) -> str:
    ident  = llp["identity"]
    acad   = llp["academic"]
    beh    = llp["behavioral"]
    cog    = llp["cognitive"]
    self_r = llp["self_reported"]
    name   = ident["name"]
    gpa    = acad["scores"]["overall_gpa"]
    weak   = acad["mastery"]["weak_topics"]
    strong = acad["mastery"]["strong_topics"]
    mastery = acad["mastery"]["mastery_map"]

    gpa_desc = (
        "strong performer" if gpa >= 3.5 else
        "above-average"    if gpa >= 2.8 else
        "average"          if gpa >= 2.0 else "struggling"
    )
    weak_d   = " and ".join(f"{t} ({int(mastery.get(t,0)*100)}%)" for t in weak)
    strong_d = " and ".join(f"{t} ({int(mastery.get(t,0)*100)}%)" for t in strong)
    anxiety  = self_r["confidence"]["anxiety_level"]
    anxiety_flag = " ⚠ High anxiety." if anxiety >= 0.70 else " Moderate anxiety." if anxiety >= 0.50 else ""
    pref = self_r["preferences"]["preferred_explanation"]
    style = cog["learning_style"]

    lines = [
        f"{'='*60}",
        f"  {name}  |  {_ordinal(ident['year_level'])}-year {ident['major']}  |  {ident['student_id']}",
        f"{'='*60}",
        f"ACADEMIC  GPA {gpa:.2f} ({gpa_desc}) | Quiz: {acad['scores']['quiz_avg']:.1f} | Exam: {acad['scores']['exam_avg']:.1f}",
        f"  Weak: {weak_d or 'none'}  |  Strong: {strong_d or 'none'}",
        f"BEHAVIORAL  Logins: {beh['engagement']['login_freq_per_week']:.1f}/wk | Submits: {int(beh['habits']['submission_rate']*100)}%",
        f"COGNITIVE  Style: {style} | Prefers: {pref}",
        f"SELF-REPORT  Motivation: {int(self_r['goals']['motivation_score']*100)}% | Anxiety: {int(anxiety*100)}%{anxiety_flag}",
        f"RECOMMENDATION  → Focus on {' and '.join(weak) if weak else 'current topics'}; use {pref} for {style} learner.",
        f"{'='*60}",
    ]
    return "\n".join(lines)


# ── Helpers ───────────────────────────────────────────────────────────────

def _derive_weak_strong(mastery_map: dict) -> tuple[list, list]:
    if not mastery_map:
        return [], []
    sorted_t = sorted(mastery_map.items(), key=lambda x: x[1])
    n = min(2, max(1, len(sorted_t) // 2))
    return [t for t, _ in sorted_t[:n]], [t for t, _ in sorted_t[-n:]]


def _parse_map(value: Any) -> dict[str, float]:
    if isinstance(value, dict):
        return {k: float(v) for k, v in value.items()}
    if isinstance(value, str) and value:
        result = {}
        for part in value.split("|"):
            if ":" in part:
                k, v = part.split(":", 1)
                result[k.strip()] = float(v.strip())
        return result
    return {}


def _parse_list(value: Any) -> list[str]:
    if isinstance(value, list):
        return [str(x) for x in value]
    if isinstance(value, str) and value:
        return [x.strip() for x in value.split("|") if x.strip()]
    return []


def _ordinal(n: int) -> str:
    return {1: "1st", 2: "2nd", 3: "3rd"}.get(int(n), f"{n}th")
