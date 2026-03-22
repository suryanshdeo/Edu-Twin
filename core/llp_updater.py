"""
EduTwin — LLP Updater
=====================
Provides the canonical `update_llp(profile, new_event)` function.

Supported event types:
  - quiz_result        → updates quiz_avg, mastery_map, weak/strong topics
  - assignment_result  → updates assignment_avg, submission_rate, late flag
  - exam_result        → updates exam_avg, GPA, optional per-topic mastery
  - self_assessment    → updates confidence_map, anxiety, motivation
  - session_log        → updates login_freq, avg_session_minutes
  - resource_access    → increments resources_used

All updates are non-destructive: the original LLP is never mutated.
Every event is appended to an audit_log inside the profile.

Usage (as module):
    from core.llp_updater import update_llp

    event = {
        "type":      "quiz_result",
        "topic":     "Algorithms",
        "score":     82.0,
        "max_score": 100.0,
        "timestamp": "2024-06-20T10:15:00"
    }
    updated_llp = update_llp(llp, event)

Usage (standalone demo):
    python core/llp_updater.py
"""

from __future__ import annotations

import copy
import json
from datetime import datetime
from pathlib import Path
from typing import Any


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def update_llp(profile: dict[str, Any], new_event: dict[str, Any]) -> dict[str, Any]:
    """
    Apply a new learning event to an LLP and return the updated profile.

    Pure function — does not mutate the input.

    Args:
        profile:   Structured LLP dict (from profile_builder.build_llp)
        new_event: Event dict with at minimum {"type": ..., "timestamp": ...}

    Returns:
        Updated LLP dict (deep copy)

    Raises:
        ValueError: If event type is unrecognised or required fields are missing.
    """
    llp = copy.deepcopy(profile)

    event_type = new_event.get("type")
    if not event_type:
        raise ValueError("Event must have a 'type' field.")

    handlers = {
        "quiz_result":       _handle_quiz,
        "assignment_result": _handle_assignment,
        "exam_result":       _handle_exam,
        "self_assessment":   _handle_self_assessment,
        "session_log":       _handle_session_log,
        "resource_access":   _handle_resource_access,
    }

    handler = handlers.get(event_type)
    if handler is None:
        raise ValueError(
            f"Unknown event type: '{event_type}'. "
            f"Valid types: {list(handlers.keys())}"
        )

    # Apply domain-specific update
    handler(llp, new_event)

    # Recalculate all derived fields
    _recalculate_gpa(llp)
    _recalculate_weak_strong(llp)
    _recalculate_score_trend(llp)

    # Append event to audit trail
    _append_audit(llp, new_event)

    # Bump last_updated timestamp
    llp["identity"]["last_updated"] = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")

    return llp


# ---------------------------------------------------------------------------
# Event Handlers
# ---------------------------------------------------------------------------

def _handle_quiz(llp: dict, event: dict) -> None:
    """
    Required fields: topic (str), score (float)
    Optional fields: max_score (float, default 100), mistakes (list[str])
    """
    _require(event, ["topic", "score"])

    score     = float(event["score"])
    max_score = float(event.get("max_score", 100.0))
    pct       = score / max_score
    topic     = event["topic"]

    acad = llp["academic"]

    # Update quiz rolling average
    acad["scores"]["quiz_avg"] = _ema(
        acad["scores"]["quiz_avg"], score, alpha=0.20
    )

    # Update per-topic mastery score
    mastery = acad["mastery"]["mastery_map"]
    if topic in mastery:
        mastery[topic] = round(_ema(mastery[topic], pct, alpha=0.25), 3)
    else:
        mastery[topic] = round(pct, 3)  # new topic — seed with this score

    acad["history"]["total_attempts"] += 1

    # Merge observed mistake types into cognitive profile
    if "mistakes" in event and isinstance(event["mistakes"], list):
        existing = set(llp["cognitive"]["common_mistakes"])
        existing.update(event["mistakes"])
        llp["cognitive"]["common_mistakes"] = sorted(existing)


def _handle_assignment(llp: dict, event: dict) -> None:
    """
    Required fields: score (float)
    Optional fields: max_score (float), submitted (bool), late (bool)
    """
    _require(event, ["score"])

    score     = float(event["score"])
    submitted = bool(event.get("submitted", True))
    late      = bool(event.get("late", False))

    acad  = llp["academic"]
    habit = llp["behavioral"]["habits"]

    acad["scores"]["assignment_avg"] = _ema(
        acad["scores"]["assignment_avg"], score, alpha=0.20
    )

    # Submission rate: 1.0 = submitted, 0.0 = missed
    habit["submission_rate"] = round(
        _ema(habit["submission_rate"], 1.0 if submitted else 0.0, alpha=0.10), 3
    )

    # Late rate: only update if the assignment was actually submitted
    if submitted:
        habit["late_submission_pct"] = round(
            _ema(habit["late_submission_pct"], 1.0 if late else 0.0, alpha=0.10), 3
        )

    acad["history"]["total_attempts"] += 1


def _handle_exam(llp: dict, event: dict) -> None:
    """
    Required fields: score (float)
    Optional fields: max_score (float), topic_scores (dict[str, float])
    """
    _require(event, ["score"])

    score     = float(event["score"])
    max_score = float(event.get("max_score", 100.0))

    acad = llp["academic"]
    acad["scores"]["exam_avg"] = _ema(
        acad["scores"]["exam_avg"], score, alpha=0.15
    )
    acad["history"]["total_attempts"] += 1

    # Optional per-topic mastery update from exam breakdown
    if "topic_scores" in event and isinstance(event["topic_scores"], dict):
        mastery = acad["mastery"]["mastery_map"]
        for topic, t_score in event["topic_scores"].items():
            pct = float(t_score) / max_score
            if topic in mastery:
                mastery[topic] = round(_ema(mastery[topic], pct, alpha=0.20), 3)
            else:
                mastery[topic] = round(pct, 3)


def _handle_self_assessment(llp: dict, event: dict) -> None:
    """
    All fields optional — update whichever are provided:
        topic (str), confidence (float 0-1)
        anxiety_level (float 0-1)
        motivation_score (float 0-1)
        study_hours (float)
    """
    conf_block = llp["self_reported"]["confidence"]
    goal_block = llp["self_reported"]["goals"]

    if "topic" in event and "confidence" in event:
        topic = event["topic"]
        val   = float(event["confidence"])
        cmap  = conf_block["confidence_map"]
        if topic in cmap:
            cmap[topic] = round(_ema(cmap[topic], val, alpha=0.30), 3)
        else:
            cmap[topic] = round(val, 3)

    if "anxiety_level" in event:
        conf_block["anxiety_level"] = round(
            _ema(conf_block["anxiety_level"], float(event["anxiety_level"]), alpha=0.30), 3
        )

    if "motivation_score" in event:
        goal_block["motivation_score"] = round(
            _ema(goal_block["motivation_score"], float(event["motivation_score"]), alpha=0.30), 3
        )

    if "study_hours" in event:
        goal_block["study_hours_per_day"] = round(
            _ema(goal_block["study_hours_per_day"], float(event["study_hours"]), alpha=0.20), 2
        )


def _handle_session_log(llp: dict, event: dict) -> None:
    """
    Required fields: duration_minutes (float)
    """
    _require(event, ["duration_minutes"])

    dur = float(event["duration_minutes"])
    eng = llp["behavioral"]["engagement"]

    eng["avg_session_minutes"] = round(
        _ema(eng["avg_session_minutes"], dur, alpha=0.15), 1
    )
    # Each logged session nudges the weekly login frequency slightly upward
    eng["login_freq_per_week"] = round(
        min(7.0, eng["login_freq_per_week"] + 0.1), 1
    )


def _handle_resource_access(llp: dict, event: dict) -> None:
    """
    Optional fields: count (int, default 1)
    """
    count = int(event.get("count", 1))
    llp["behavioral"]["engagement"]["resources_used"] += count


# ---------------------------------------------------------------------------
# Derived-field Recalculators
# ---------------------------------------------------------------------------

def _recalculate_gpa(llp: dict) -> None:
    """GPA on 4.0 scale = weighted blend (quiz 30%, assignment 30%, exam 40%) / 25."""
    s = llp["academic"]["scores"]
    composite = (
        s["quiz_avg"]       * 0.30
        + s["assignment_avg"] * 0.30
        + s["exam_avg"]       * 0.40
    )
    llp["academic"]["scores"]["overall_gpa"] = round(composite / 25.0, 2)


def _recalculate_weak_strong(llp: dict) -> None:
    """Re-derive weak/strong topic lists from current mastery_map."""
    mastery = llp["academic"]["mastery"]["mastery_map"]
    if not mastery:
        return

    sorted_topics = sorted(mastery.items(), key=lambda x: x[1])
    n        = len(sorted_topics)
    n_slots  = min(2, max(1, n // 2))

    llp["academic"]["mastery"]["weak_topics"]   = [t for t, _ in sorted_topics[:n_slots]]
    llp["academic"]["mastery"]["strong_topics"] = [t for t, _ in sorted_topics[-n_slots:]]


def _recalculate_score_trend(llp: dict) -> None:
    """
    Infer improving / stable / declining from the last 5 scored events in audit_log.
    Requires at least 3 events to make a determination.
    """
    audit = llp.get("audit_log", [])
    scored = [
        e for e in audit
        if e.get("type") in ("quiz_result", "exam_result") and "score" in e
    ]

    if len(scored) < 3:
        return  # keep existing trend

    recent    = [float(e["score"]) for e in scored[-5:]]
    diffs     = [recent[i + 1] - recent[i] for i in range(len(recent) - 1)]
    avg_delta = sum(diffs) / len(diffs)

    if avg_delta > 2.0:
        llp["academic"]["history"]["score_trend"] = "improving"
    elif avg_delta < -2.0:
        llp["academic"]["history"]["score_trend"] = "declining"
    else:
        llp["academic"]["history"]["score_trend"] = "stable"


# ---------------------------------------------------------------------------
# Audit Trail
# ---------------------------------------------------------------------------

def _append_audit(llp: dict, event: dict) -> None:
    """Append event to profile audit_log (creates the key if missing)."""
    if "audit_log" not in llp:
        llp["audit_log"] = []

    entry = dict(event)
    if "timestamp" not in entry:
        entry["timestamp"] = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")

    llp["audit_log"].append(entry)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _ema(current: float, new_value: float, alpha: float = 0.20) -> float:
    """
    Exponential Moving Average.
    alpha = learning rate: 0.10 (slow/stable) to 0.30 (reactive).
    """
    return round((1.0 - alpha) * current + alpha * new_value, 2)


def _require(event: dict, fields: list[str]) -> None:
    """Raise ValueError if any required field is missing from event."""
    missing = [f for f in fields if f not in event]
    if missing:
        raise ValueError(
            f"Event type '{event.get('type')}' is missing required fields: {missing}"
        )


# ---------------------------------------------------------------------------
# Demo entrypoint
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import sys
    sys.path.insert(0, str(Path(__file__).parent.parent))

    from core.profile_builder import build_llp, summarise_llp

    raw_path = Path("data/raw/students.json")
    if not raw_path.exists():
        print("[llp_updater] Please run generate_data.py first.")
        sys.exit(1)

    with open(raw_path) as f:
        records = json.load(f)

    llp  = build_llp(records[0])
    name = llp["identity"]["name"]

    print(f"\n[llp_updater] Applying 5 events to: {name}")
    print(f"  BEFORE  GPA: {llp['academic']['scores']['overall_gpa']}  "
          f"| Weak topics: {llp['academic']['mastery']['weak_topics']}\n")

    demo_events = [
        {   # Attempt 1: quiz on a weak topic (poor score)
            "type":      "quiz_result",
            "topic":     llp["academic"]["mastery"]["weak_topics"][0],
            "score":     42.0,
            "max_score": 100.0,
            "timestamp": "2024-06-20T09:00:00",
            "mistakes":  ["conceptual", "careless"],
        },
        {   # Attempt 2: assignment submitted late
            "type":      "assignment_result",
            "score":     61.0,
            "submitted": True,
            "late":      True,
            "timestamp": "2024-06-21T23:50:00",
        },
        {   # Attempt 3: quiz again — improving
            "type":      "quiz_result",
            "topic":     llp["academic"]["mastery"]["weak_topics"][0],
            "score":     68.0,
            "max_score": 100.0,
            "timestamp": "2024-06-23T10:30:00",
        },
        {   # Attempt 4: exam with per-topic breakdown
            "type":        "exam_result",
            "score":       74.0,
            "max_score":   100.0,
            "topic_scores": {
                llp["academic"]["mastery"]["weak_topics"][0]:   60.0,
                llp["academic"]["mastery"]["strong_topics"][0]: 88.0,
            },
            "timestamp": "2024-06-25T14:00:00",
        },
        {   # Attempt 5: self-assessment post-exam
            "type":             "self_assessment",
            "topic":            llp["academic"]["mastery"]["weak_topics"][0],
            "confidence":       0.50,
            "anxiety_level":    0.55,
            "motivation_score": 0.75,
            "timestamp":        "2024-06-25T16:00:00",
        },
    ]

    updated = llp
    for i, event in enumerate(demo_events, 1):
        updated = update_llp(updated, event)
        print(
            f"  [{i}] {event['type']:22s} → "
            f"GPA: {updated['academic']['scores']['overall_gpa']:.2f}  "
            f"quiz_avg: {updated['academic']['scores']['quiz_avg']:.1f}  "
            f"trend: {updated['academic']['history']['score_trend']}"
        )

    print(f"\n  AFTER   GPA: {updated['academic']['scores']['overall_gpa']}  "
          f"| Weak topics: {updated['academic']['mastery']['weak_topics']}")
    print(f"  Audit entries: {len(updated.get('audit_log', []))}")

    out_path = Path("data/raw/llp_updated_sample.json")
    with open(out_path, "w") as f:
        json.dump(updated, f, indent=2)
    print(f"\n[llp_updater] Saved → {out_path}")
    print("\n" + summarise_llp(updated))
