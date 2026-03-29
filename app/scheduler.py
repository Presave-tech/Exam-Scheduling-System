"""
scheduler.py — Exam Timetable Scheduler
=========================================
Orchestrates the full scheduling pipeline:
  1. Fetch subjects + enrollments from DB
  2. Build conflict graph via graph.py
  3. Run Greedy Graph Coloring
  4. Map colors → time slot labels
  5. Persist results to TimetableEntry table
"""

from app import db
from app.models import Subject, Enrollment, TimetableEntry
from app.graph import ConflictGraph


# Pre-defined time slot labels (expandable)
# Color 0 → Slot 1 label, Color 1 → Slot 2 label, etc.
SLOT_LABELS = [
    "Day 1 — 9:00 AM",
    "Day 1 — 1:00 PM",
    "Day 2 — 9:00 AM",
    "Day 2 — 1:00 PM",
    "Day 3 — 9:00 AM",
    "Day 3 — 1:00 PM",
    "Day 4 — 9:00 AM",
    "Day 4 — 1:00 PM",
    "Day 5 — 9:00 AM",
    "Day 5 — 1:00 PM",
]


def generate_timetable():
    """
    Full scheduling pipeline.

    Returns:
        result dict with keys:
          - success      : bool
          - message      : status string
          - num_slots    : number of time slots used
          - steps_log    : algorithm step-by-step log (list of strings)
          - timetable    : list of {subject, slot_number, slot_label}
          - conflicts    : list of (subj_a_name, subj_b_name) conflict pairs
    """
    subjects    = Subject.query.all()
    enrollments = Enrollment.query.all()

    # Guard: need at least one subject
    if not subjects:
        return {"success": False, "message": "No subjects found. Please add subjects first."}

    # Guard: need enrollment data to detect conflicts
    if not enrollments:
        return {"success": False, "message": "No enrollments found. Enroll students in subjects first."}

    # ---- Phase 1: Build conflict graph ----
    graph = ConflictGraph()
    graph.build_from_enrollments(subjects, enrollments)

    # ---- Phase 2: Run Greedy Coloring ----
    color_map, steps_log, num_colors = graph.greedy_color()

    # Check if our pre-defined slots are enough
    if num_colors > len(SLOT_LABELS):
        # Auto-extend with generic labels
        for i in range(len(SLOT_LABELS), num_colors):
            SLOT_LABELS.append(f"Day {i // 2 + 6} — {'9:00 AM' if i % 2 == 0 else '1:00 PM'}")

    # ---- Phase 3: Clear old timetable & persist new one ----
    TimetableEntry.query.delete()
    db.session.commit()

    timetable_rows = []
    subj_map = {s.id: s for s in subjects}

    for subject_id, color in color_map.items():
        slot_number = color + 1                   # 1-based
        slot_label  = SLOT_LABELS[color]

        entry = TimetableEntry(
            subject_id  = subject_id,
            slot_number = slot_number,
            slot_label  = slot_label,
            color       = color,
        )
        db.session.add(entry)

        subj = subj_map[subject_id]
        timetable_rows.append({
            "subject_code": subj.code,
            "subject_name": subj.name,
            "slot_number" : slot_number,
            "slot_label"  : slot_label,
            "color"       : color,
        })

    db.session.commit()

    # Build human-readable conflict list
    subj_labels = {s.id: f"{s.code} — {s.name}" for s in subjects}
    conflicts = [
        (subj_labels.get(u, u), subj_labels.get(v, v))
        for (u, v) in graph.get_conflict_pairs()
    ]

    # Sort timetable by slot for display
    timetable_rows.sort(key=lambda r: r["slot_number"])

    return {
        "success"  : True,
        "message"  : f"Timetable generated successfully using {num_colors} time slot(s).",
        "num_slots": num_colors,
        "steps_log": steps_log,
        "timetable": timetable_rows,
        "conflicts": conflicts,
    }


# Sample data loading logic has been removed.
