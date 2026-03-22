"""
run_phase1.py
=============
Entry point to run and verify all Phase 1 components:

  1. Generate 75 synthetic student profiles
  2. Save to CSV + JSON
  3. Build a profile from a raw dict
  4. Print a twin summary
  5. Simulate update_llp with a quiz event

Usage:
    python run_phase1.py
"""

import json
import subprocess
import sys
from pathlib import Path
from copy import deepcopy

from core.profile_builder import build_llp, summarise_llp
from core.llp_updater import update_llp


def main():
    print("\n" + "=" * 65)
    print("  EduTwin — Phase 1 Runner")
    print("=" * 65)

    # ---------------------------------------------------------------
    # Step 1: Generate synthetic dataset
    # ---------------------------------------------------------------
    print("\n[1/4] Generating 75 synthetic student profiles...")

    raw_path = Path("data/raw/students.json")
    csv_path = Path("data/raw/students.csv")

    if not raw_path.exists():
        subprocess.run(
            [sys.executable, "data/generate_data.py", "--n", "75", "--seed", "42"],
            check=True
        )
    else:
        print("      Data already exists — skipping generation.")

    with open(raw_path) as f:
        records = json.load(f)

    print(f"      Loaded {len(records)} profiles from {raw_path}")
    print(f"      CSV available at {csv_path}")

    # ---------------------------------------------------------------
    # Step 2: Show sample profile summary (from generated data)
    # ---------------------------------------------------------------
    print("\n[2/4] Sample generated profile:")
    sample_llp = build_llp(records[0])
    print(summarise_llp(sample_llp))

    # ---------------------------------------------------------------
    # Step 3: Build a profile from raw dict (simulates intake form)
    # ---------------------------------------------------------------
    print("\n[3/4] Building profile from raw intake data (manual entry)...")

    raw_input = {
        "student_id":            "STU-AISHA",
        "name":                  "Aisha Patel",
        "email":                 "aisha@techinstitute.edu",
        "age":                   20,
        "year_level":            2,
        "major":                 "Computer Science",
        "enrolled_on":           "2023-09-01",
        "profile_version":       "1.0",

        # Academic
        "quiz_avg":              58.0,
        "assignment_avg":        70.0,
        "exam_avg":              55.0,
        "overall_gpa":           2.80,
        "mastery_map": {
            "Data Structures":   0.55,
            "Algorithms":        0.35,
            "Databases":         0.60,
            "Networking":        0.70,
            "OS":                0.20,
        },
        "weak_topics":           ["Algorithms", "OS"],
        "strong_topics":         ["Networking", "Databases"],
        "total_attempts":        18,
        "score_trend":           "stable",

        # Behavioral
        "login_freq_per_week":   3.5,
        "avg_session_minutes":   45.0,
        "submission_rate":       0.72,
        "late_submission_pct":   0.35,
        "resources_used":        5,
        "peer_interaction":      "medium",
        "forum_posts":           4,

        # Cognitive
        "learning_style":        "visual",
        "processing_speed":      "average",
        "retention_score":       0.55,
        "attention_span_min":    30,
        "common_mistakes":       ["conceptual", "careless"],

        # Self-reported
        "confidence_map": {
            "Data Structures":   0.50,
            "Algorithms":        0.25,
            "Databases":         0.60,
            "Networking":        0.65,
            "OS":                0.20,
        },
        "anxiety_level":         0.72,
        "motivation_score":      0.55,
        "target_grade":          "B",
        "preferred_explanation": "diagrams",
        "study_hours_per_day":   1.8,
    }

    aisha = build_llp(raw_input)
    print(summarise_llp(aisha))

    # ---------------------------------------------------------------
    # Step 4: Simulate update_llp with events
    # ---------------------------------------------------------------
    print("\n[4/4] Simulating update_llp events on Aisha's profile...")

    # Snapshot before
    before_gpa      = aisha["academic"]["scores"]["overall_gpa"]
    before_anxiety  = aisha["self_reported"]["confidence"]["anxiety_level"]
    before_mastery  = deepcopy(aisha["academic"]["mastery"]["mastery_map"])
    before_sub_rate = aisha["behavioral"]["habits"]["submission_rate"]

    # Event A: Quiz on weak topic
    aisha = update_llp(aisha, {
        "type":      "quiz_result",
        "topic":     "OS",
        "score":     45.0,
        "max_score": 100.0,
        "timestamp": "2024-06-20T10:00:00",
        "mistakes":  ["conceptual"],
    })
    print(f"  After quiz (score 45/100 on OS):")
    print(f"    quiz_avg   : {aisha['academic']['scores']['quiz_avg']:.1f}")
    print(f"    OS mastery : {aisha['academic']['mastery']['mastery_map'].get('OS', 0):.3f}")

    # Event B: Late assignment submission
    aisha = update_llp(aisha, {
        "type":      "assignment_result",
        "score":     70.0,
        "max_score": 100.0,
        "submitted": True,
        "late":      True,
        "timestamp": "2024-06-21T23:50:00",
    })
    print(f"  After late assignment submission:")
    print(f"    late_submission_pct : {aisha['behavioral']['habits']['late_submission_pct']:.3f}")

    # Event C: Self-report check-in
    aisha = update_llp(aisha, {
        "type":             "self_assessment",
        "anxiety_level":    0.68,
        "motivation_score": 0.60,
        "topic":            "Algorithms",
        "confidence":       0.35,
        "timestamp":        "2024-06-22T09:00:00",
    })
    print(f"  After self-report check-in:")
    print(f"    anxiety_level    : {aisha['self_reported']['confidence']['anxiety_level']:.3f}")
    print(f"    motivation_score : {aisha['self_reported']['goals']['motivation_score']:.3f}")

    # Diff summary
    print(f"\n  Summary of changes from baseline:")
    print(f"    {'overall_gpa':30s}: {before_gpa} → {aisha['academic']['scores']['overall_gpa']}")
    print(f"    {'anxiety_level':30s}: {before_anxiety:.3f} → {aisha['self_reported']['confidence']['anxiety_level']:.3f}")
    print(f"    {'OS mastery':30s}: {before_mastery.get('OS', 0):.3f} → {aisha['academic']['mastery']['mastery_map'].get('OS', 0):.3f}")
    print(f"    {'submission_rate':30s}: {before_sub_rate:.3f} → {aisha['behavioral']['habits']['submission_rate']:.3f}")

    print(f"\n  Audit log entries : {len(aisha.get('audit_log', []))}")
    print(f"  Weak topics now   : {aisha['academic']['mastery']['weak_topics']}")
    print(f"  Score trend       : {aisha['academic']['history']['score_trend']}")

    print("\n  Updated twin summary:")
    print(summarise_llp(aisha))

    # Save
    out_path = Path("data/raw/aisha_llp.json")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w") as f:
        json.dump(aisha, f, indent=2)

    print("\n" + "=" * 65)
    print("  Phase 1 complete.")
    print(f"  students.json  → data/raw/students.json")
    print(f"  students.csv   → data/raw/students.csv")
    print(f"  aisha_llp.json → {out_path}")
    print("=" * 65 + "\n")


if __name__ == "__main__":
    main()
