"""
EduTwin — Synthetic Student Data Generator
==========================================
Generates 50-100 realistic student profiles as CSV and JSON.

Usage:
    python data/generate_data.py
    python data/generate_data.py --n 50 --seed 99
"""

import argparse
import json
import random
import uuid
from datetime import datetime, timedelta
from pathlib import Path

import numpy as np
import pandas as pd
from faker import Faker

SUBJECTS = ["Mathematics", "Physics", "Chemistry", "Computer Science", "English"]

TOPICS = {
    "Mathematics":      ["Calculus", "Algebra", "Statistics", "Geometry", "Linear Algebra"],
    "Physics":          ["Mechanics", "Thermodynamics", "Optics", "Electromagnetism", "Quantum"],
    "Chemistry":        ["Organic", "Inorganic", "Physical Chemistry", "Electrochemistry", "Bonding"],
    "Computer Science": ["Data Structures", "Algorithms", "OS", "Networking", "Databases"],
    "English":          ["Grammar", "Comprehension", "Writing", "Literature", "Vocabulary"],
}

LEARNING_STYLES   = ["visual", "auditory", "reading", "kinesthetic"]
EXPLANATION_PREFS = ["step-by-step", "analogies", "diagrams", "examples", "brief-summary"]
MISTAKE_TYPES     = ["conceptual", "calculation", "careless", "memory-based", "misinterpretation"]

fake = Faker()
Faker.seed(0)


def rng_score(mean, std, lo=0.0, hi=100.0):
    return round(float(np.clip(np.random.normal(mean, std), lo, hi)), 1)


def build_mastery_map(topics, strength_bias):
    return {
        t: round(float(np.clip(np.random.normal(strength_bias, 0.18), 0.0, 1.0)), 2)
        for t in topics
    }


def pick_weak_strong(mastery_map):
    sorted_topics = sorted(mastery_map.items(), key=lambda x: x[1])
    return [t for t, _ in sorted_topics[:2]], [t for t, _ in sorted_topics[-2:]]


def random_date(start_days_ago=180):
    delta = timedelta(days=random.randint(0, start_days_ago))
    return (datetime.now() - delta).strftime("%Y-%m-%d")


def generate_student(index):
    student_id = f"STU-{str(index).zfill(4)}"
    major      = random.choice(SUBJECTS)
    tier_mean  = random.choices([0.30, 0.60, 0.85], weights=[0.25, 0.5, 0.25], k=1)[0]

    quiz_avg       = rng_score(tier_mean * 100, 10)
    assignment_avg = rng_score(tier_mean * 100, 8)
    exam_avg       = rng_score(tier_mean * 100, 15)
    overall_gpa    = round((quiz_avg * 0.3 + assignment_avg * 0.3 + exam_avg * 0.4) / 25.0, 2)

    all_topics  = TOPICS[major]
    mastery_map = build_mastery_map(all_topics, tier_mean)
    weak, strong = pick_weak_strong(mastery_map)

    confidence_map = {
        t: round(float(np.clip(np.random.normal(mastery_map[t], 0.15), 0, 1)), 2)
        for t in all_topics
    }

    return {
        "student_id":            student_id,
        "name":                  fake.name(),
        "email":                 fake.email(),
        "age":                   random.randint(18, 25),
        "year_level":            random.randint(1, 4),
        "major":                 major,
        "enrolled_on":           random_date(720),
        "quiz_avg":              quiz_avg,
        "assignment_avg":        assignment_avg,
        "exam_avg":              exam_avg,
        "overall_gpa":           overall_gpa,
        "mastery_map":           mastery_map,
        "weak_topics":           weak,
        "strong_topics":         strong,
        "total_attempts":        random.randint(5, 60),
        "score_trend":           random.choices(["improving","stable","declining"], weights=[0.35,0.45,0.20])[0],
        "login_freq_per_week":   round(float(np.clip(np.random.normal(tier_mean*5+1, 1.5), 0, 7)), 1),
        "avg_session_minutes":   round(float(np.clip(np.random.normal(30+tier_mean*60, 15), 5, 180)), 1),
        "submission_rate":       round(float(np.clip(np.random.normal(0.5+tier_mean*0.5, 0.15), 0, 1)), 2),
        "late_submission_pct":   round(float(np.clip(np.random.normal(0.3-tier_mean*0.25, 0.1), 0, 1)), 2),
        "resources_used":        random.randint(1, 12),
        "peer_interaction":      random.choices(["low","medium","high"], weights=[0.3,0.4,0.3])[0],
        "forum_posts":           random.randint(0, 30),
        "learning_style":        random.choice(LEARNING_STYLES),
        "processing_speed":      random.choices(["slow","average","fast"], weights=[0.25,0.5,0.25])[0],
        "retention_score":       round(float(np.clip(np.random.normal(tier_mean, 0.2), 0, 1)), 2),
        "attention_span_min":    random.randint(10, 60),
        "common_mistakes":       random.sample(MISTAKE_TYPES, k=random.randint(1, 3)),
        "confidence_map":        confidence_map,
        "anxiety_level":         round(float(np.clip(np.random.normal(0.5-tier_mean*0.3, 0.2), 0, 1)), 2),
        "motivation_score":      round(float(np.clip(np.random.normal(0.4+tier_mean*0.5, 0.2), 0, 1)), 2),
        "target_grade":          random.choices(["A","B","C"], weights=[0.4,0.45,0.15])[0],
        "preferred_explanation": random.choice(EXPLANATION_PREFS),
        "study_hours_per_day":   round(float(np.clip(np.random.normal(1+tier_mean*4, 1.0), 0, 10)), 1),
        "last_updated":          datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
        "profile_version":       "1.0",
    }


def flatten_for_csv(record):
    flat = {}
    for k, v in record.items():
        if isinstance(v, dict):
            flat[k] = "|".join(f"{tk}:{tv}" for tk, tv in v.items())
        elif isinstance(v, list):
            flat[k] = "|".join(str(x) for x in v)
        else:
            flat[k] = v
    return flat


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--n",    type=int, default=75)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--out",  type=str, default="data/raw")
    args = parser.parse_args()

    random.seed(args.seed)
    np.random.seed(args.seed)

    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)

    print(f"[EduTwin] Generating {args.n} profiles (seed={args.seed})...")
    records = [generate_student(i + 1) for i in range(args.n)]

    json_path = out_dir / "students.json"
    with open(json_path, "w") as f:
        json.dump(records, f, indent=2)
    print(f"[EduTwin] JSON → {json_path}")

    csv_path = out_dir / "students.csv"
    pd.DataFrame([flatten_for_csv(r) for r in records]).to_csv(csv_path, index=False)
    print(f"[EduTwin] CSV  → {csv_path}")
    print(f"[EduTwin] Done. {len(records)} students generated.")


if __name__ == "__main__":
    main()
