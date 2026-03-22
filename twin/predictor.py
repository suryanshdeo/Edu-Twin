"""
EduTwin — Performance Predictor
=================================
Predicts exam score, GPA, and risk level using rule-based scoring
plus optional LLM enrichment.

Usage:
    from twin.predictor import predict_performance

    result = predict_performance(llp, provider="mock")
    print(result["risk_level"])
"""

from __future__ import annotations
import json, os
from typing import Any
from twin.prompt_engine import build_prompt


def predict_performance(
    llp: dict[str, Any],
    provider: str = "groq",
    model: str | None = None,
) -> dict[str, Any]:
    """
    Predict upcoming performance. Rule-based baseline always runs first.
    LLM layer enriches with qualitative reasoning when provider != 'mock'.

    Returns dict with keys:
        predicted_next_exam_score, predicted_end_of_term_gpa,
        risk_level, confidence, key_risk_factors,
        key_protective_factors, recommended_actions, method
    """
    baseline = _rule_based(llp)

    if provider == "mock":
        baseline["method"] = "rule_based"
        return baseline

    try:
        system_prompt, user_message = build_prompt(llp, task="predict_performance")
        raw = _call_llm(system_prompt, user_message, provider, model)
        llm = _parse_json(raw, dict)

        merged = {
            "predicted_next_exam_score": round(
                (float(llm.get("predicted_next_exam_score", baseline["predicted_next_exam_score"]))
                 + baseline["predicted_next_exam_score"]) / 2, 1),
            "predicted_end_of_term_gpa": round(
                (float(llm.get("predicted_end_of_term_gpa", baseline["predicted_end_of_term_gpa"]))
                 + baseline["predicted_end_of_term_gpa"]) / 2, 2),
            "risk_level":             llm.get("risk_level", baseline["risk_level"]),
            "confidence":             llm.get("confidence", baseline["confidence"]),
            "key_risk_factors":       llm.get("key_risk_factors", baseline["key_risk_factors"]),
            "key_protective_factors": llm.get("key_protective_factors", baseline["key_protective_factors"]),
            "recommended_actions":    llm.get("recommended_actions", baseline["recommended_actions"]),
            "method": "llm",
        }
        return merged
    except Exception as e:
        baseline["method"] = "rule_based"
        baseline["llm_error"] = str(e)
        return baseline


def format_prediction_report(pred: dict, student_name: str = "Student") -> str:
    icons = {"High": "[!!!]", "Medium": "[!]", "Low": "[OK]"}
    icon  = icons.get(pred.get("risk_level", ""), "[?]")
    lines = [
        f"Performance Prediction — {student_name}", "=" * 50,
        f"  Method:          {pred.get('method','unknown')}",
        f"  Next exam score: {pred.get('predicted_next_exam_score','?')} / 100",
        f"  End-of-term GPA: {pred.get('predicted_end_of_term_gpa','?')} / 4.0",
        f"  Risk level:      {icon} {pred.get('risk_level','?')}",
        f"  Confidence:      {pred.get('confidence','?')}",
        "", "  Risk factors:",
    ]
    for rf in pred.get("key_risk_factors", []):
        lines.append(f"    - {rf}")
    lines.append("\n  Protective factors:")
    for pf in pred.get("key_protective_factors", []):
        lines.append(f"    + {pf}")
    lines.append("\n  Recommended actions:")
    for i, a in enumerate(pred.get("recommended_actions", []), 1):
        lines.append(f"    {i}. {a}")
    return "\n".join(lines)


# ── Rule-based predictor ──────────────────────────────────────────────────

def _rule_based(llp: dict[str, Any]) -> dict[str, Any]:
    acad   = llp["academic"]
    beh    = llp["behavioral"]
    self_r = llp["self_reported"]

    exam_avg     = acad["scores"]["exam_avg"]
    mastery_vals = list(acad["mastery"]["mastery_map"].values())
    mastery_avg  = (sum(mastery_vals) / len(mastery_vals) * 100) if mastery_vals else 50.0
    sub_rate     = beh["habits"]["submission_rate"] * 100
    login_score  = min(beh["engagement"]["login_freq_per_week"] / 7.0, 1.0) * 100
    motivation   = self_r["goals"]["motivation_score"] * 100
    anxiety      = self_r["confidence"]["anxiety_level"] * 100
    trend        = acad["history"]["score_trend"]

    predicted = (
        exam_avg      * 0.30 +
        mastery_avg   * 0.25 +
        sub_rate      * 0.15 +
        login_score   * 0.10 +
        motivation    * 0.10 +
        (100-anxiety) * 0.10
    )
    trend_adj   = {"improving": +3.0, "stable": 0.0, "declining": -5.0}.get(trend, 0.0)
    predicted   = round(min(100.0, max(0.0, predicted + trend_adj)), 1)
    current_gpa = acad["scores"]["overall_gpa"]
    pred_gpa    = round(min(4.0, max(0.0, current_gpa + (predicted - exam_avg) / 100.0 * 0.5)), 2)

    risk_score = 0
    risk_f, prot_f, actions = [], [], []

    if predicted < 50:
        risk_score += 3; risk_f.append("Predicted exam score below passing threshold")
    elif predicted < 65:
        risk_score += 2; risk_f.append("Predicted exam score is borderline")
    else:
        prot_f.append(f"Exam performance projected at {predicted:.0f}%")

    weak = acad["mastery"]["weak_topics"]
    critical = [t for t in weak if acad["mastery"]["mastery_map"].get(t, 1) < 0.40]
    if critical:
        risk_score += 2
        risk_f.append(f"Critical mastery gaps: {', '.join(critical)}")
        actions.append(f"Immediate remediation of: {', '.join(critical)}")
    elif weak:
        risk_score += 1; risk_f.append(f"Below-average mastery in: {', '.join(weak)}")

    if sub_rate < 60:
        risk_score += 2; risk_f.append(f"Low submission rate ({sub_rate:.0f}%)")
        actions.append("Implement assignment tracking and check-in")
    elif sub_rate > 85:
        prot_f.append("Consistently submits work on time")

    if trend == "declining":
        risk_score += 2; risk_f.append("Declining score trend")
        actions.append("Urgent academic check-in with tutor")
    elif trend == "improving":
        prot_f.append("Scores on an upward trajectory")

    if motivation < 40:
        risk_score += 1; risk_f.append("Low motivation")
        actions.append("Goal-setting or motivational coaching session")
    elif motivation > 70:
        prot_f.append("High motivation and goal orientation")

    if anxiety > 65:
        risk_score += 1; risk_f.append(f"High exam anxiety ({int(anxiety)}%)")
        actions.append("Anxiety management strategies before assessments")

    if login_score < 30:
        risk_score += 1; risk_f.append("Low platform engagement")
    else:
        prot_f.append("Regular platform engagement")

    risk_level = "High" if risk_score >= 6 else "Medium" if risk_score >= 3 else "Low"
    confidence = "High" if risk_score >= 6 else "Medium"

    if not actions:
        actions = ["Continue current study habits", "Review weak topics regularly"]

    return {
        "predicted_next_exam_score": predicted,
        "predicted_end_of_term_gpa": pred_gpa,
        "risk_level":                risk_level,
        "confidence":                confidence,
        "key_risk_factors":          risk_f,
        "key_protective_factors":    prot_f,
        "recommended_actions":       actions,
    }


# ── LLM backends ─────────────────────────────────────────────────────────

def _call_llm(system_prompt, user_message, provider, model):
    if provider == "groq":
        return _call_groq(system_prompt, user_message, model or "llama-3.3-70b-versatile")
    elif provider == "gemini":
        return _call_gemini(system_prompt, user_message, model or "gemini-1.5-flash")
    raise ValueError(f"Unknown provider: '{provider}'")


def _call_groq(system_prompt, user_message, model):
    try:
        from groq import Groq
    except ImportError:
        raise RuntimeError("Run: pip install groq")
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        raise RuntimeError("GROQ_API_KEY not set.")
    client = Groq(api_key=api_key)
    resp = client.chat.completions.create(
        model=model,
        messages=[{"role": "system", "content": system_prompt},
                  {"role": "user",   "content": user_message}],
        temperature=0.2, max_tokens=1024,
    )
    return resp.choices[0].message.content


def _call_gemini(system_prompt, user_message, model):
    try:
        import google.generativeai as genai
    except ImportError:
        raise RuntimeError("Run: pip install google-generativeai")
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY not set.")
    genai.configure(api_key=api_key)
    m = genai.GenerativeModel(model_name=model, system_instruction=system_prompt)
    return m.generate_content(
        user_message,
        generation_config=genai.GenerationConfig(temperature=0.2, max_output_tokens=1024),
    ).text


def _parse_json(raw, expected_type):
    cleaned = raw.strip()
    if cleaned.startswith("```"):
        cleaned = "\n".join(
            l for l in cleaned.split("\n") if not l.strip().startswith("```")
        ).strip()
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError as e:
        raise RuntimeError(f"LLM returned invalid JSON: {e}")


if __name__ == "__main__":
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from core.profile_builder import build_llp

    with open("data/raw/students.json") as f:
        records = json.load(f)

    for r in records[:3]:
        llp  = build_llp(r)
        pred = predict_performance(llp, provider="mock")
        print(format_prediction_report(pred, llp["identity"]["name"]))
        print()
