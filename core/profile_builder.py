"""
EduTwin — Profile Builder
=========================
Converts a raw student record into a structured LLP dict + human summary.

Usage:
    from core.profile_builder import build_llp, summarise_llp
"""

from __future__ import annotations
import json
from datetime import datetime
from pathlib import Path
from typing import Any


def build_llp(raw: dict[str, Any]) -> dict[str, Any]:
    """
    Convert a flat raw student record into a structured LLP dict.
    All fields use .get() with safe defaults — no KeyError possible.
    """
    mastery_map     = _parse_map(raw.get("mastery_map", {}))
    confidence_map  = _parse_map(raw.get("confidence_map", {}))
    weak_topics     = _parse_list(raw.get("weak_topics", []))
    strong_topics   = _parse_list(raw.get("strong_topics", []))
    common_mistakes = _parse_list(raw.get("common_mistakes", []))

    return {
        "identity": {
            "student_id":      raw.get("student_id", "STU-0000"),
            "name":            raw.get("name", "Unknown Student"),
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
    """Return a human-readable multi-line summary of an LLP."""
    ident  = llp["identity"]
    acad   = llp["academic"]
    beh    = llp["behavioral"]
    cog    = llp["cognitive"]
    self_r = llp["self_reported"]

    name    = ident["name"]
    gpa     = acad["scores"]["overall_gpa"]
    quiz    = acad["scores"]["quiz_avg"]
    exam    = acad["scores"]["exam_avg"]
    trend   = acad["history"]["score_trend"]
    weak    = acad["mastery"]["weak_topics"]
    strong  = acad["mastery"]["strong_topics"]
    mastery = acad["mastery"]["mastery_map"]

    gpa_desc = (
        "strong performer"        if gpa >= 3.5 else
        "above-average student"   if gpa >= 2.8 else
        "average student"         if gpa >= 2.0 else
        "struggling academically"
    )
    trend_str = {
        "improving": "Performance is improving.",
        "stable":    "Performance is stable.",
        "declining": "⚠ Scores are declining — intervention recommended.",
    }.get(trend, "")

    weak_detail   = " and ".join(f"{t} ({int(mastery.get(t,0)*100)}%)" for t in weak)
    strong_detail = " and ".join(f"{t} ({int(mastery.get(t,0)*100)}%)" for t in strong)

    login      = beh["engagement"]["login_freq_per_week"]
    session    = beh["engagement"]["avg_session_minutes"]
    sub_rate   = beh["habits"]["submission_rate"]
    anxiety    = self_r["confidence"]["anxiety_level"]
    motivation = self_r["goals"]["motivation_score"]
    target     = self_r["goals"]["target_grade"]
    study_hrs  = self_r["goals"]["study_hours_per_day"]
    pref       = self_r["preferences"]["preferred_explanation"]
    style      = cog["learning_style"]
    mistakes   = ", ".join(cog["common_mistakes"]) or "none"

    anxiety_flag = (
        " ⚠ High anxiety."   if anxiety >= 0.70 else
        " Moderate anxiety." if anxiety >= 0.50 else ""
    )

    lines = [
        f"{'='*60}",
        f"  {name}  |  {_ordinal(ident['year_level'])}-year {ident['major']}  |  ID: {ident['student_id']}",
        f"{'='*60}",
        "ACADEMIC",
        f"  GPA {gpa:.2f} ({gpa_desc}) | Quiz: {quiz:.1f} | Exam: {exam:.1f}",
        f"  {trend_str}",
        f"  Weak:   {weak_detail   or 'none identified'}",
        f"  Strong: {strong_detail or 'none identified'}",
        "",
        "BEHAVIORAL",
        f"  Logins: {login:.1f}/wk | Session: {session:.0f} min | Submits: {int(sub_rate*100)}%",
        f"  Peer interaction: {beh['collaboration']['peer_interaction']}",
        "",
        "COGNITIVE",
        f"  Style: {style} | Speed: {cog['processing_speed']} | Retention: {int(cog['retention_score']*100)}%",
        f"  Common mistakes: {mistakes}",
        f"  Prefers: {pref} | Attention span: {cog['attention_span_min']} min",
        "",
        "SELF-REPORTED",
        f"  Motivation: {int(motivation*100)}% | Anxiety: {int(anxiety*100)}%{anxiety_flag}",
        f"  Target grade: {target} | Study: {study_hrs:.1f} hr/day",
        "",
        "RECOMMENDATION",
        f"  → Focus on {' and '.join(weak) if weak else 'maintaining current topics'}; "
        f"deliver as {pref} for {style} learner.",
        f"{'='*60}",
    ]
    return "\n".join(lines)


# ── Helpers ───────────────────────────────────────────────────────────────

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


if __name__ == "__main__":
    import sys
    sys.path.insert(0, str(Path(__file__).parent.parent))
    raw_path = Path("data/raw/students.json")
    if not raw_path.exists():
        print("Run: python data/generate_data.py first")
        sys.exit(1)
    with open(raw_path) as f:
        records = json.load(f)
    llp = build_llp(records[0])
    print(summarise_llp(llp))
