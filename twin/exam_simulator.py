"""
EduTwin — Exam Answer Simulator
=================================
Simulates how a specific student would answer an exam question,
reflecting their actual mastery level and mistake patterns.

Usage:
    from twin.exam_simulator import simulate_exam_answer

    result = simulate_exam_answer(llp, question="Explain X", topic="Y", provider="mock")
    print(result["simulated_answer"])
    print(result["tutor_note"])
"""

from __future__ import annotations
import os
from typing import Any
from twin.prompt_engine import build_prompt


def simulate_exam_answer(
    llp: dict[str, Any],
    question: str,
    topic: str = "",
    provider: str = "groq",
    model: str | None = None,
) -> dict[str, Any]:
    """
    Simulate how this student would answer an exam question.

    Returns dict with keys:
        question, topic, mastery_pct, simulated_answer, tutor_note, quality_estimate
    """
    mastery_map = llp["academic"]["mastery"]["mastery_map"]
    mastery_pct = int(mastery_map.get(topic, 0.5) * 100) if topic else _avg_mastery(llp)
    quality     = _quality(mastery_pct)

    user_message  = _build_user_message(question, topic, mastery_pct, llp)
    system_prompt, _ = build_prompt(llp, task="simulate_exam_answer")

    if provider == "mock":
        answer, note = _mock_simulation(question, topic, mastery_pct, llp)
    else:
        raw = _call_llm(system_prompt, user_message, provider, model)
        answer, note = _split_answer(raw)

    return {
        "question":         question,
        "topic":            topic,
        "mastery_pct":      mastery_pct,
        "simulated_answer": answer,
        "tutor_note":       note,
        "quality_estimate": quality,
    }


def format_simulation_report(result: dict, student_name: str = "Student") -> str:
    lines = [
        f"Exam Simulation — {student_name}", "=" * 50,
        f"  Topic:            {result['topic'] or 'General'}",
        f"  Mastery:          {result['mastery_pct']}%",
        f"  Quality estimate: {result['quality_estimate']}",
        "",
        "  QUESTION:",
        f"  {result['question']}",
        "",
        "  SIMULATED ANSWER:",
        "  " + result["simulated_answer"].replace("\n", "\n  "),
        "",
        "  TUTOR NOTE:",
        "  " + result["tutor_note"].replace("\n", "\n  "),
    ]
    return "\n".join(lines)


# ── Helpers ───────────────────────────────────────────────────────────────

def _build_user_message(question, topic, mastery_pct, llp):
    mistakes = llp["cognitive"]["common_mistakes"]
    style    = llp["cognitive"]["learning_style"]
    speed    = llp["cognitive"]["processing_speed"]
    anxiety  = llp["self_reported"]["confidence"]["anxiety_level"]

    lines = [
        f"Exam question: {question}",
        f"Topic area: {topic or 'General'}",
        f"Student mastery on this topic: {mastery_pct}%",
        f"Typical mistake types: {', '.join(mistakes) or 'none'}",
        f"Learning style: {style}, {speed} processing speed",
    ]
    if anxiety > 0.65:
        lines.append(f"High exam anxiety ({int(anxiety*100)}%) — may show signs of rushing.")
    if mastery_pct < 40:
        lines.append("Very low mastery — answer will be incomplete with fundamental errors.")
    elif mastery_pct < 65:
        lines.append("Partial mastery — may get gist right but miss precision or skip steps.")
    else:
        lines.append("Good mastery — mostly correct but may miss edge cases.")
    return "\n".join(lines)


def _split_answer(raw):
    raw = raw.strip()
    for marker in ["\n\n[TUTOR NOTE]", "\n[TUTOR NOTE]", "\n\nTutor note:", "\nTutor Note:"]:
        idx = raw.lower().find(marker.lower())
        if idx != -1:
            return raw[:idx].strip(), raw[idx + len(marker):].strip()
    return raw, "No tutor note generated."


def _quality(mastery_pct):
    if mastery_pct >= 80: return "Excellent"
    if mastery_pct >= 65: return "Good"
    if mastery_pct >= 45: return "Partial"
    return "Poor"


def _avg_mastery(llp):
    vals = list(llp["academic"]["mastery"]["mastery_map"].values())
    return int(sum(vals) / len(vals) * 100) if vals else 50


# ── Mock simulation ───────────────────────────────────────────────────────

def _mock_simulation(question, topic, mastery_pct, llp):
    mistakes = llp["cognitive"]["common_mistakes"]
    style    = llp["cognitive"]["learning_style"]
    name     = llp["identity"]["name"].split()[0]

    if mastery_pct < 40:
        answer = (
            f"I think {topic or 'this'} is about... [long pause] "
            f"I know it has something to do with the basic definition but I'm not sure exactly. "
            f"I think the answer might involve [vague statement]. Sorry, not very confident here."
        )
        note = (
            f"{name}'s answer reveals fundamental gaps in {topic or 'this area'}. "
            f"They are aware of the topic but cannot articulate core mechanisms. "
            f"Recommend re-teaching from fundamentals before assigning practice problems."
        )
    elif mastery_pct < 65:
        answer = (
            f"So {topic or 'this'} basically works by... [partially correct explanation]. "
            f"{'I think there might also be' if 'conceptual' in mistakes else 'And then'} "
            f"[incomplete elaboration]. I'm fairly sure about the first part."
        )
        note = (
            f"{name} shows partial understanding — right intuition but lacks precision. "
            f"Targeted practice with {'worked examples' if style == 'kinesthetic' else 'structured review'} "
            f"would consolidate their knowledge effectively."
        )
    else:
        answer = (
            f"{topic or 'This concept'} refers to [mostly correct, well-structured explanation]. "
            f"The key principle is [accurate statement]. "
            f"[Minor gap or missed nuance at the edges.] Overall fairly confident."
        )
        note = (
            f"{name} demonstrates solid understanding with minor gaps at the edges. "
            f"Challenge with harder variants to develop deeper mastery."
        )
    return answer, note


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
        temperature=0.7, max_tokens=1000,
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
        generation_config=genai.GenerationConfig(temperature=0.7, max_output_tokens=1000),
    ).text


if __name__ == "__main__":
    import json, sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from core.profile_builder import build_llp

    with open("data/raw/students.json") as f:
        records = json.load(f)

    # Find first student with any mastery data
    llp = None
    for r in records:
        candidate = build_llp(r)
        mastery = candidate["academic"]["mastery"]["mastery_map"]
        if mastery:
            llp = candidate
            break
    if llp is None:
        print("No students with mastery data found.")
        sys.exit(1)

    # Pick topic safely from whatever is available
    weak    = llp["academic"]["mastery"]["weak_topics"]
    mastery = llp["academic"]["mastery"]["mastery_map"]

    if weak:
        topic = weak[0]
    elif mastery:
        # pick lowest mastery topic
        topic = min(mastery, key=lambda t: mastery[t])
    else:
        topic = "General"

    question = f"Explain the core concept of {topic} and give one real-world example."
    name     = llp["identity"]["name"]

    print(f"[exam_simulator] Simulating answer for: {name}")
    print(f"[exam_simulator] Topic: {topic}\n")
    result = simulate_exam_answer(llp, question=question, topic=topic, provider="mock")
    print(format_simulation_report(result, name))
