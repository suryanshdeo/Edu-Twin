"""
llp_schema.py
=============
Defines the Live Learner Profile (LLP) schema for EduTwin.

The LLP has four domains:
  1. Academic    — grades, scores, topic mastery
  2. Behavioral  — study habits, attendance, deadlines
  3. Cognitive   — learning style, memory, problem-solving
  4. Self-reported — confidence, motivation, anxiety
"""

from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional
import json


# ---------------------------------------------------------------------------
# Sub-schemas (one dataclass per domain)
# ---------------------------------------------------------------------------

@dataclass
class AcademicProfile:
    """Measurable academic performance data."""
    gpa: float                          # 0.0 – 4.0
    subject_scores: Dict[str, float]    # {"Math": 78.5, "Physics": 65.0, ...}
    topic_mastery: Dict[str, float]     # {"Calculus": 0.72, "Vectors": 0.45, ...}
    quiz_attempts: int                  # total quizzes taken
    avg_quiz_score: float               # 0 – 100
    assignment_completion_rate: float   # 0.0 – 1.0
    recent_scores: List[float]          # last 5 quiz/test scores (newest first)
    weak_topics: List[str]              # auto-computed from topic_mastery < 0.5
    strong_topics: List[str]            # auto-computed from topic_mastery > 0.75


@dataclass
class BehavioralProfile:
    """Study habits and engagement patterns."""
    avg_study_hours_per_day: float      # e.g., 2.5
    study_consistency_score: float      # 0.0 – 1.0  (how regular their sessions are)
    attendance_rate: float              # 0.0 – 1.0
    deadline_adherence_rate: float      # 0.0 – 1.0
    help_seeking_frequency: str         # "low" | "medium" | "high"
    preferred_study_time: str           # "morning" | "afternoon" | "evening" | "night"
    avg_session_duration_minutes: int   # typical study session length
    forum_posts_count: int              # engagement in discussion forums
    resource_downloads: int             # PDFs, slides downloaded


@dataclass
class CognitiveProfile:
    """Learning style and cognitive traits (mostly self-assessed or inferred)."""
    learning_style: str                 # "visual" | "auditory" | "reading" | "kinesthetic"
    memory_retention_score: float       # 0.0 – 1.0 (inferred from re-quiz performance)
    problem_solving_speed: str          # "slow" | "average" | "fast"
    conceptual_vs_procedural: str       # "conceptual" | "balanced" | "procedural"
    attention_span_estimate: str        # "short" | "medium" | "long"
    note_taking_style: str              # "detailed" | "summary" | "none"


@dataclass
class SelfReportedProfile:
    """Student's own perception of their learning."""
    confidence_level: float             # 0.0 – 1.0
    motivation_level: float             # 0.0 – 1.0
    exam_anxiety_level: float           # 0.0 – 1.0
    academic_goals: str                 # "pass" | "good_grades" | "excellence" | "career"
    preferred_resource_types: List[str] # ["video", "textbook", "practice_problems", ...]
    self_assessed_weak_areas: List[str] # student's own weak topics
    stress_level: float                 # 0.0 – 1.0
    sleep_hours_per_night: float        # reported average


# ---------------------------------------------------------------------------
# Master LLP schema
# ---------------------------------------------------------------------------

@dataclass
class LiveLearnerProfile:
    """
    The complete Live Learner Profile (LLP) for a single student.
    This is the core data structure that EduTwin maintains and updates.
    """
    # --- Identity ---
    student_id: str
    name: str
    age: int
    year_of_study: int                  # 1–4
    major: str
    university: str

    # --- The four domain profiles ---
    academic: AcademicProfile
    behavioral: BehavioralProfile
    cognitive: CognitiveProfile
    self_reported: SelfReportedProfile

    # --- Meta ---
    profile_version: int = 1            # increments on each update
    created_at: str = ""                # ISO timestamp
    last_updated_at: str = ""           # ISO timestamp
    update_history: List[Dict] = field(default_factory=list)  # log of all events

    # --- Derived summary (filled by profile_builder) ---
    predicted_performance: Optional[str] = None  # "at_risk" | "average" | "strong"
    twin_summary: Optional[str] = None            # human-readable paragraph

    def to_dict(self) -> dict:
        """Serialize the full LLP to a plain Python dict."""
        return asdict(self)

    def to_json(self, indent: int = 2) -> str:
        """Serialize the full LLP to a JSON string."""
        return json.dumps(self.to_dict(), indent=indent)

    def get_risk_flag(self) -> str:
        """
        Quick heuristic risk assessment based on key signals.
        Returns: 'high_risk' | 'moderate_risk' | 'on_track'
        """
        risk_score = 0
        if self.academic.gpa < 2.0:
            risk_score += 3
        elif self.academic.gpa < 2.5:
            risk_score += 1

        if self.behavioral.attendance_rate < 0.6:
            risk_score += 2
        if self.behavioral.deadline_adherence_rate < 0.5:
            risk_score += 2
        if len(self.academic.weak_topics) > 3:
            risk_score += 1
        if self.self_reported.confidence_level < 0.3:
            risk_score += 1

        if risk_score >= 5:
            return "high_risk"
        elif risk_score >= 2:
            return "moderate_risk"
        return "on_track"


# ---------------------------------------------------------------------------
# Reference schema dict (for documentation / validation reference)
# ---------------------------------------------------------------------------

LLP_SCHEMA_REFERENCE = {
    "student_id": "string (UUID)",
    "name": "string",
    "age": "int (17–30)",
    "year_of_study": "int (1–4)",
    "major": "string",
    "university": "string",
    "academic": {
        "gpa": "float (0.0–4.0)",
        "subject_scores": "dict[str, float(0–100)]",
        "topic_mastery": "dict[str, float(0–1)]",
        "quiz_attempts": "int",
        "avg_quiz_score": "float (0–100)",
        "assignment_completion_rate": "float (0–1)",
        "recent_scores": "list[float] (last 5)",
        "weak_topics": "list[str] (mastery < 0.5)",
        "strong_topics": "list[str] (mastery > 0.75)"
    },
    "behavioral": {
        "avg_study_hours_per_day": "float",
        "study_consistency_score": "float (0–1)",
        "attendance_rate": "float (0–1)",
        "deadline_adherence_rate": "float (0–1)",
        "help_seeking_frequency": "low | medium | high",
        "preferred_study_time": "morning | afternoon | evening | night",
        "avg_session_duration_minutes": "int",
        "forum_posts_count": "int",
        "resource_downloads": "int"
    },
    "cognitive": {
        "learning_style": "visual | auditory | reading | kinesthetic",
        "memory_retention_score": "float (0–1)",
        "problem_solving_speed": "slow | average | fast",
        "conceptual_vs_procedural": "conceptual | balanced | procedural",
        "attention_span_estimate": "short | medium | long",
        "note_taking_style": "detailed | summary | none"
    },
    "self_reported": {
        "confidence_level": "float (0–1)",
        "motivation_level": "float (0–1)",
        "exam_anxiety_level": "float (0–1)",
        "academic_goals": "pass | good_grades | excellence | career",
        "preferred_resource_types": "list[str]",
        "self_assessed_weak_areas": "list[str]",
        "stress_level": "float (0–1)",
        "sleep_hours_per_night": "float"
    },
    "profile_version": "int",
    "created_at": "ISO 8601 timestamp",
    "last_updated_at": "ISO 8601 timestamp",
    "update_history": "list[dict]",
    "predicted_performance": "at_risk | average | strong | null",
    "twin_summary": "string | null"
}
