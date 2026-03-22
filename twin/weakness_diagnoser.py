"""
EduTwin — Weakness Diagnoser
=============================
LLM-powered weak topic identification with root cause + intervention.

Usage:
    from twin.weakness_diagnoser import diagnose_weaknesses

    results = diagnose_weaknesses(llp, provider="mock")  # no API needed
    results = diagnose_weaknesses(llp, provider="groq")  # real LLM
"""

from __future__ import annotations
import json, os
from typing import Any
from twin.prompt_engine import build_prompt


def diagnose_weaknesses(
    llp: dict[str, Any],
    provider: str = "groq",
    model: str | None = None,
) -> list[dict[str, Any]]:
    """
    Identify and diagnose weak topics.

    Returns list of dicts with keys:
        topic, mastery_pct, root_cause, severity, intervention
    """
    if provider == "mock":
        return _rule_based_diagnosis(llp)

    system_prompt, user_message = build_prompt(llp, task="diagnose_weaknesses")
    raw = _call_llm(system_prompt, user_message, provider, model)
    return _parse_json(raw, expected_type=list)


def format_diagnosis_report(diagnosis: list[dict], student_name: str = "Student") -> str:
    if not diagnosis:
        return f"No weak areas identified for {student_name}."

    order = {"Critical": 0, "Moderate": 1, "Minor": 2}
    sorted_d = sorted(diagnosis, key=lambda x: order.get(x.get("severity", "Minor"), 3))

    lines = [f"Weakness Diagnosis — {student_name}", "=" * 50]
    for i, item in enumerate(sorted_d, 1):
        sev = item.get("severity", "Unknown")
        tag = {"Critical": "[!!!]", "Moderate": "[!]", "Minor": "[ ]"}.get(sev, "[?]")
        lines += [
            f"\n{i}. {item.get('topic','?')}  {tag} {sev}",
            f"   Mastery:      {item.get('mastery_pct','?')}%",
            f"   Root cause:   {item.get('root_cause','N/A')}",
            f"   Intervention: {item.get('intervention','N/A')}",
        ]
    return "\n".join(lines)


# ── Rule-based fallback ───────────────────────────────────────────────────

def _rule_based_diagnosis(llp: dict[str, Any]) -> list[dict[str, Any]]:
    mastery  = llp["academic"]["mastery"]["mastery_map"]
    weak     = llp["academic"]["mastery"]["weak_topics"]
    mistakes = llp["cognitive"]["common_mistakes"]
    anxiety  = llp["self_reported"]["confidence"]["anxiety_level"]
    style    = llp["cognitive"]["learning_style"]
    pref     = llp["self_reported"]["preferences"]["preferred_explanation"]

    results = []
    topics_to_check = weak if weak else sorted(mastery, key=lambda t: mastery[t])[:2]

    for topic in topics_to_check:
        pct = int(mastery.get(topic, 0) * 100)
        severity = "Critical" if pct < 40 else "Moderate" if pct < 60 else "Minor"

        if "conceptual" in mistakes:
            root_cause = f"Fundamental conceptual gaps in {topic}."
        elif "calculation" in mistakes:
            root_cause = f"Execution/calculation errors despite partial understanding."
        elif anxiety > 0.65:
            root_cause = f"High anxiety ({int(anxiety*100)}%) suppressing performance."
        else:
            root_cause = f"Insufficient practice — low retention in {topic}."

        intervention = f"Use {pref} materials for {style} learner. "
        intervention += (
            "Schedule immediate 1-on-1 session." if severity == "Critical" else
            "Assign 3-5 targeted practice problems." if severity == "Moderate" else
            "Include in next revision session."
        )
        results.append({
            "topic":        topic,
            "mastery_pct":  pct,
            "root_cause":   root_cause,
            "severity":     severity,
            "intervention": intervention,
        })
    return results


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
        parsed = json.loads(cleaned)
    except json.JSONDecodeError as e:
        raise RuntimeError(f"LLM returned invalid JSON: {e}\nRaw:\n{raw[:400]}")
    if not isinstance(parsed, expected_type):
        raise RuntimeError(f"Expected {expected_type.__name__}, got {type(parsed).__name__}")
    return parsed


if __name__ == "__main__":
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from core.profile_builder import build_llp

    with open("data/raw/students.json") as f:
        records = json.load(f)

    # Find a student that has weak topics
    llp = None
    for r in records:
        candidate = build_llp(r)
        if candidate["academic"]["mastery"]["weak_topics"]:
            llp = candidate
            break
    if llp is None:
        llp = build_llp(records[0])

    name = llp["identity"]["name"]
    print(f"[weakness_diagnoser] Running MOCK diagnosis for: {name}\n")
    diagnosis = diagnose_weaknesses(llp, provider="mock")
    print(format_diagnosis_report(diagnosis, name))
    print("\nRaw JSON:")
    print(json.dumps(diagnosis, indent=2))
