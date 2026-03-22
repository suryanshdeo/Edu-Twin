"""
EduTwin — Twin Engine
======================
Unified facade combining all Phase 2 capabilities.
This is what Phase 3 (Streamlit UI) will import.

Usage:
    from twin.twin_engine import TwinEngine

    engine = TwinEngine(provider="mock")   # or "groq" / "gemini"
    engine.load_student(llp)

    print(engine.diagnosis_report())
    print(engine.prediction_report())
    print(engine.full_report())
"""

from __future__ import annotations
from typing import Any

from core.profile_builder import build_llp, summarise_llp
from twin.weakness_diagnoser import diagnose_weaknesses, format_diagnosis_report
from twin.explainer          import explain_topic, explain_weak_topics
from twin.predictor          import predict_performance, format_prediction_report
from twin.exam_simulator     import simulate_exam_answer, format_simulation_report


class TwinEngine:
    """Stateful facade for all EduTwin Phase 2 capabilities."""

    def __init__(self, provider: str = "mock", model: str | None = None):
        self.provider = provider
        self.model    = model
        self._llp:   dict[str, Any] | None = None
        self._cache: dict[str, Any] = {}

    # ── Loading ───────────────────────────────────────────────────────

    def load_student(self, llp_or_raw: dict[str, Any]) -> None:
        """Load a student. Accepts structured LLP or raw flat record."""
        self._llp = llp_or_raw if "identity" in llp_or_raw else build_llp(llp_or_raw)
        self._cache.clear()

    @property
    def llp(self) -> dict[str, Any]:
        if self._llp is None:
            raise RuntimeError("No student loaded. Call load_student() first.")
        return self._llp

    @property
    def student_name(self) -> str:
        return self.llp["identity"]["name"]

    def _safe_topic(self) -> str:
        """Return a topic to use — weak topic if available, else first mastery topic."""
        weak = self.llp["academic"]["mastery"]["weak_topics"]
        if weak:
            return weak[0]
        mastery = self.llp["academic"]["mastery"]["mastery_map"]
        if mastery:
            return list(mastery.keys())[0]
        return ""

    # ── Capabilities ──────────────────────────────────────────────────

    def diagnose(self, force: bool = False) -> list[dict[str, Any]]:
        if "diagnosis" not in self._cache or force:
            self._cache["diagnosis"] = diagnose_weaknesses(
                self.llp, provider=self.provider, model=self.model
            )
        return self._cache["diagnosis"]

    def explain(self, topic: str = "", extra_context: str = "", force: bool = False) -> dict[str, Any]:
        topic = topic or self._safe_topic()
        key   = f"explain:{topic}"
        if key not in self._cache or force:
            self._cache[key] = explain_topic(
                self.llp, topic=topic,
                provider=self.provider, model=self.model,
                extra_context=extra_context,
            )
        return self._cache[key]

    def explain_all_weak(self, force: bool = False) -> list[dict[str, Any]]:
        if "explain_all" not in self._cache or force:
            self._cache["explain_all"] = explain_weak_topics(
                self.llp, provider=self.provider, model=self.model
            )
        return self._cache["explain_all"]

    def predict(self, force: bool = False) -> dict[str, Any]:
        if "prediction" not in self._cache or force:
            self._cache["prediction"] = predict_performance(
                self.llp, provider=self.provider, model=self.model
            )
        return self._cache["prediction"]

    def simulate(self, question: str = "", topic: str = "", force: bool = False) -> dict[str, Any]:
        topic    = topic or self._safe_topic()
        question = question or f"Explain the core concept of {topic} and give a real-world example."
        key      = f"simulate:{question[:40]}"
        if key not in self._cache or force:
            self._cache[key] = simulate_exam_answer(
                self.llp, question=question, topic=topic,
                provider=self.provider, model=self.model,
            )
        return self._cache[key]

    # ── Reports ───────────────────────────────────────────────────────

    def profile_summary(self) -> str:
        return summarise_llp(self.llp)

    def diagnosis_report(self) -> str:
        return format_diagnosis_report(self.diagnose(), self.student_name)

    def prediction_report(self) -> str:
        return format_prediction_report(self.predict(), self.student_name)

    def simulation_report(self, question: str = "", topic: str = "") -> str:
        return format_simulation_report(self.simulate(question, topic), self.student_name)

    def full_report(self, exam_question: str = "") -> str:
        """Generate a comprehensive report combining all twin capabilities."""
        topic = self._safe_topic()
        question = exam_question or (
            f"Explain the fundamental concept of {topic} and its practical applications."
            if topic else "Explain a key concept from your major."
        )

        sections = [
            self.profile_summary(),
            "",
            self.diagnosis_report(),
            "",
            self.prediction_report(),
            "",
            self.simulation_report(question, topic),
        ]

        if topic:
            expl = self.explain(topic)
            sections += [
                "",
                f"PERSONALIZED EXPLANATION — {topic}",
                "=" * 50,
                f"  Mastery: {expl['mastery_pct']}%  |  Style: {expl['style_used']}  |  Tone: {expl['tone']}",
                "",
                expl["explanation"],
            ]
            if expl["check_question"]:
                sections += ["", "CHECK QUESTION:", expl["check_question"]]

        return "\n".join(sections)

    # ── UI helpers ────────────────────────────────────────────────────

    def get_mastery_chart_data(self) -> dict[str, Any]:
        mastery = self.llp["academic"]["mastery"]["mastery_map"]
        return {
            "topics": list(mastery.keys()),
            "scores": [int(v * 100) for v in mastery.values()],
        }

    def get_score_summary(self) -> dict[str, Any]:
        scores = self.llp["academic"]["scores"]
        pred   = self.predict()
        return {
            "current_gpa":    scores["overall_gpa"],
            "quiz_avg":       scores["quiz_avg"],
            "exam_avg":       scores["exam_avg"],
            "predicted_exam": pred["predicted_next_exam_score"],
            "predicted_gpa":  pred["predicted_end_of_term_gpa"],
            "risk_level":     pred["risk_level"],
        }


def run_full_twin(raw_or_llp: dict[str, Any], provider: str = "mock", exam_question: str = "") -> str:
    """One-shot convenience function — load student and return full report."""
    engine = TwinEngine(provider=provider)
    engine.load_student(raw_or_llp)
    return engine.full_report(exam_question=exam_question)


if __name__ == "__main__":
    import json, sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from core.profile_builder import build_llp

    with open("data/raw/students.json") as f:
        records = json.load(f)

    llp = None
    for r in records:
        candidate = build_llp(r)
        if candidate["academic"]["mastery"]["mastery_map"]:
            llp = candidate
            break
    if llp is None:
        llp = build_llp(records[0])

    mastery = llp["academic"]["mastery"]["mastery_map"]
    weak    = llp["academic"]["mastery"]["weak_topics"]

    if weak:
        topic = weak[0]
    elif mastery:
        topic = min(mastery, key=lambda t: mastery[t])
    else:
        topic = llp["identity"]["major"]

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
