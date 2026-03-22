"""
EduTwin — Personalized Explainer
==================================
Generates topic explanations tailored to a student's learning style,
mastery level, and preferred explanation format.

Usage:
    from twin.explainer import explain_topic

    result = explain_topic(llp, topic="Algorithms", provider="mock")
    print(result["explanation"])
"""

from __future__ import annotations
import os
from typing import Any
from twin.prompt_engine import build_prompt


def explain_topic(
    llp: dict[str, Any],
    topic: str,
    provider: str = "groq",
    model: str | None = None,
    extra_context: str = "",
) -> dict[str, Any]:
    """
    Generate a personalised explanation for a topic.

    Returns dict with keys:
        topic, mastery_pct, explanation, check_question, style_used, tone
    """
    mastery     = llp["academic"]["mastery"]["mastery_map"]
    mastery_pct = int(mastery.get(topic, 0.5) * 100)
    style       = llp["cognitive"]["learning_style"]
    anxiety     = llp["self_reported"]["confidence"]["anxiety_level"]
    tone        = "encouraging" if anxiety >= 0.60 else "standard"

    user_message  = _build_user_message(topic, mastery_pct, style, tone, extra_context)
    system_prompt, _ = build_prompt(llp, task="explain_topic")

    if provider == "mock":
        explanation, check_q = _mock_explanation(topic, mastery_pct, style, tone)
    else:
        raw = _call_llm(system_prompt, user_message, provider, model)
        explanation, check_q = _split_explanation(raw)

    return {
        "topic":          topic,
        "mastery_pct":    mastery_pct,
        "explanation":    explanation,
        "check_question": check_q,
        "style_used":     style,
        "tone":           tone,
    }


def explain_weak_topics(llp, provider="groq", model=None):
    """Generate explanations for all weak topics in the LLP."""
    weak = llp["academic"]["mastery"]["weak_topics"]
    return [explain_topic(llp, t, provider=provider, model=model) for t in weak]


# ── Helpers ───────────────────────────────────────────────────────────────

def _build_user_message(topic, mastery_pct, style, tone, extra_context):
    style_hints = {
        "visual":      "Use spatial metaphors and describe diagrams in words.",
        "auditory":    "Use a conversational tone with verbal analogies.",
        "reading":     "Use precise language, definitions first, then elaboration.",
        "kinesthetic": "Lead with a hands-on worked example, then explain theory.",
    }
    lines = [
        f"Please explain: {topic}",
        f"Student mastery: {mastery_pct}%",
        f"Learning style: {style} — {style_hints.get(style, '')}",
        f"Tone: {tone}",
        (
            "Start from first principles." if mastery_pct < 40 else
            "Build on partial knowledge, address common gaps." if mastery_pct < 65 else
            "Go deeper, address edge cases."
        ),
    ]
    if extra_context:
        lines.append(f"Additional focus: {extra_context}")
    return "\n".join(lines)


def _split_explanation(raw):
    raw = raw.strip()
    for marker in ["\n\nCheck your understanding:", "\nCheck your understanding:",
                   "\n\nQuestion:", "\n\nTry this:"]:
        idx = raw.lower().find(marker.lower())
        if idx != -1:
            return raw[:idx].strip(), raw[idx + len(marker):].strip()
    sentences = raw.split(".")
    if sentences and sentences[-1].strip().endswith("?"):
        check_q = sentences[-1].strip()
        return raw[:raw.rfind(check_q)].strip(), check_q
    return raw, ""


def _mock_explanation(topic, mastery_pct, style, tone):
    opener = (
        f"Don't worry — {topic} can be tricky at first, but let's break it down!"
        if tone == "encouraging"
        else f"Let's examine {topic} systematically."
    )
    level = (
        "We'll start from the very beginning"     if mastery_pct < 40 else
        "We'll build on what you already know"    if mastery_pct < 65 else
        "We'll go deeper into the nuances"
    )
    style_note = {
        "visual":      "Think of it like a map — each concept connects to the next.",
        "auditory":    "Let me walk you through this as if we were talking it out.",
        "reading":     "Here is a precise definition followed by a structured breakdown.",
        "kinesthetic": "Let's start with a concrete example you can work through.",
    }.get(style, "Here's how it works.")

    explanation = (
        f"{opener}\n\n{level} with {topic}. {style_note}\n\n"
        f"[Mock mode — connect a real LLM provider (groq/gemini) via API key "
        f"to get a full personalised explanation for {topic} at {mastery_pct}% mastery.]"
    )
    check_q = f"Can you explain the core idea of {topic} in your own words without notes?"
    return explanation, check_q


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
        temperature=0.5, max_tokens=1200,
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
        generation_config=genai.GenerationConfig(temperature=0.5, max_output_tokens=1200),
    ).text


if __name__ == "__main__":
    import json, sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from core.profile_builder import build_llp

    with open("data/raw/students.json") as f:
        records = json.load(f)

    # Find first student with weak topics
    llp = None
    for r in records:
        candidate = build_llp(r)
        if candidate["academic"]["mastery"]["weak_topics"]:
            llp = candidate
            break
    if llp is None:
        llp = build_llp(records[0])

    # Pick a topic — weak topic if available, else first mastery topic
    weak = llp["academic"]["mastery"]["weak_topics"]
    topic = weak[0] if weak else list(llp["academic"]["mastery"]["mastery_map"].keys())[0]

    name = llp["identity"]["name"]
    print(f"[explainer] Generating MOCK explanation of '{topic}' for {name}\n")
    result = explain_topic(llp, topic=topic, provider="groq")

    print(f"Topic:   {result['topic']}  ({result['mastery_pct']}% mastery)")
    print(f"Style:   {result['style_used']}  |  Tone: {result['tone']}")
    print("\n--- EXPLANATION ---")
    print(result["explanation"])
    if result["check_question"]:
        print("\n--- CHECK QUESTION ---")
        print(result["check_question"])
