"""
EduTwin — Prompt Engine
=======================
Converts an LLP into a compact LLM context string.
All twin modules call build_prompt() before hitting the LLM.

Usage:
    from twin.prompt_engine import build_prompt, llp_to_context
"""

from __future__ import annotations
from typing import Any


def llp_to_context(llp: dict[str, Any]) -> str:
    """Serialize LLP into a token-efficient [STUDENT PROFILE] block."""
    ident  = llp["identity"]
    acad   = llp["academic"]
    beh    = llp["behavioral"]
    cog    = llp["cognitive"]
    self_r = llp["self_reported"]

    mastery    = acad["mastery"]["mastery_map"]
    conf_map   = self_r["confidence"]["confidence_map"]
    sorted_m   = sorted(mastery.items(), key=lambda x: x[1])
    sorted_c   = sorted(conf_map.items(), key=lambda x: x[1])
    mastery_str = ", ".join(f"{t}: {int(v*100)}%" for t, v in sorted_m)
    conf_str    = ", ".join(f"{t}: {int(v*100)}%" for t, v in sorted_c)
    mistakes    = ", ".join(cog["common_mistakes"]) or "none identified"

    lines = [
        "[STUDENT PROFILE]",
        f"Name:           {ident['name']}  |  ID: {ident['student_id']}",
        f"Year/Major:     Year {ident['year_level']}, {ident['major']}",
        "",
        "[ACADEMIC]",
        f"GPA:            {acad['scores']['overall_gpa']:.2f} / 4.0",
        f"Scores:         Quiz {acad['scores']['quiz_avg']:.1f}  |  "
        f"Assignment {acad['scores']['assignment_avg']:.1f}  |  "
        f"Exam {acad['scores']['exam_avg']:.1f}",
        f"Trend:          {acad['history']['score_trend']}  "
        f"({acad['history']['total_attempts']} attempts)",
        f"Weak topics:    {', '.join(acad['mastery']['weak_topics']) or 'none'}",
        f"Strong topics:  {', '.join(acad['mastery']['strong_topics']) or 'none'}",
        f"Mastery map:    {mastery_str}",
        "",
        "[BEHAVIORAL]",
        f"Engagement:     {beh['engagement']['login_freq_per_week']:.1f} logins/wk  |  "
        f"Avg session: {beh['engagement']['avg_session_minutes']:.0f} min",
        f"Submissions:    {int(beh['habits']['submission_rate']*100)}% on time  |  "
        f"{int(beh['habits']['late_submission_pct']*100)}% late",
        f"Peer:           {beh['collaboration']['peer_interaction']}  |  "
        f"Forum posts: {beh['collaboration']['forum_posts']}",
        "",
        "[COGNITIVE]",
        f"Learning style: {cog['learning_style']}",
        f"Processing:     {cog['processing_speed']} speed  |  "
        f"Retention: {int(cog['retention_score']*100)}%  |  "
        f"Attention span: {cog['attention_span_min']} min",
        f"Common mistakes: {mistakes}",
        "",
        "[SELF-REPORTED]",
        f"Confidence map: {conf_str}",
        f"Anxiety:        {int(self_r['confidence']['anxiety_level']*100)}%  |  "
        f"Motivation: {int(self_r['goals']['motivation_score']*100)}%",
        f"Target grade:   {self_r['goals']['target_grade']}  |  "
        f"Study hrs/day: {self_r['goals']['study_hours_per_day']:.1f}",
        f"Prefers:        {self_r['preferences']['preferred_explanation']} explanations",
        "[END PROFILE]",
    ]
    return "\n".join(lines)


_TASK_INSTRUCTIONS: dict[str, str] = {

    "diagnose_weaknesses": """\
[TASK: WEAKNESS DIAGNOSIS]
You are an expert academic tutor analysing a student's learning profile.
For each weak topic identify: root cause, severity (Critical/Moderate/Minor), intervention.

Respond ONLY with a valid JSON array — no markdown, no preamble:
[
  {
    "topic": "...",
    "mastery_pct": <int>,
    "root_cause": "...",
    "severity": "Critical|Moderate|Minor",
    "intervention": "..."
  }
]""",

    "explain_topic": """\
[TASK: PERSONALIZED EXPLANATION]
Explain the requested topic tailored to this specific student's learning style,
mastery level, and preferred explanation format.
If anxiety > 60% use an encouraging tone.
End with one check-your-understanding question appropriate to their level.""",

    "predict_performance": """\
[TASK: PERFORMANCE PREDICTION]
Predict this student's upcoming performance using ALL available signals.

Respond ONLY with valid JSON — no markdown, no preamble:
{
  "predicted_next_exam_score": <float>,
  "predicted_end_of_term_gpa": <float>,
  "risk_level": "High|Medium|Low",
  "confidence": "High|Medium|Low",
  "key_risk_factors": ["..."],
  "key_protective_factors": ["..."],
  "recommended_actions": ["..."]
}""",

    "simulate_exam_answer": """\
[TASK: EXAM ANSWER SIMULATION]
Write the answer AS THIS STUDENT — not a model answer.
Reflect their actual mastery level, typical mistakes, and cognitive style.
After the answer add a [TUTOR NOTE] section (2-3 sentences) explaining
what the answer reveals and what follow-up would help most.""",
}


def build_prompt(
    llp: dict[str, Any],
    task: str,
    extra_instruction: str = "",
) -> tuple[str, str]:
    """
    Build (system_prompt, user_message) for a given task.

    Args:
        llp:               Structured LLP dict
        task:              One of the keys in _TASK_INSTRUCTIONS
        extra_instruction: Optional extra text appended to the user message

    Returns:
        (system_prompt, user_message)
    """
    if task not in _TASK_INSTRUCTIONS:
        raise ValueError(f"Unknown task: '{task}'. Valid: {list(_TASK_INSTRUCTIONS)}")

    context      = llp_to_context(llp)
    instruction  = _TASK_INSTRUCTIONS[task]
    system_prompt = f"{context}\n\n{instruction}"
    user_message  = extra_instruction.strip() if extra_instruction else _default_user(task)
    return system_prompt, user_message


def _default_user(task: str) -> str:
    return {
        "diagnose_weaknesses":  "Please diagnose this student's weak areas.",
        "explain_topic":        "Please explain the most critical weak topic for this student.",
        "predict_performance":  "Please predict this student's upcoming performance.",
        "simulate_exam_answer": "Please simulate this student's answer on their weakest topic.",
    }.get(task, "Please complete the task described in the system prompt.")


def available_tasks() -> list[str]:
    return list(_TASK_INSTRUCTIONS.keys())


if __name__ == "__main__":
    import json, sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from core.profile_builder import build_llp

    with open("data/raw/students.json") as f:
        records = json.load(f)

    llp = build_llp(records[0])
    print("=" * 60)
    print(llp_to_context(llp))
    print("\n[prompt_engine] OK — context block generated successfully.")
