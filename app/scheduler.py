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
from app.models import Subject, Enrollment, TimetableEntry, TimeSlot
from app.graph import ConflictGraph



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

    # Load time slots from database or seed if empty
    existing_slots = TimeSlot.query.order_by(TimeSlot.slot_number).all()
    if not existing_slots:
        default_labels = [
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
        for idx, label in enumerate(default_labels):
            db.session.add(TimeSlot(slot_number=idx + 1, label=label))
        db.session.commit()
        existing_slots = TimeSlot.query.order_by(TimeSlot.slot_number).all()

    slot_labels = [slot.label for slot in existing_slots]

    # Check if our pre-defined slots are enough
    if num_colors > len(slot_labels):
        # Auto-extend with generic labels
        for i in range(len(slot_labels), num_colors):
            new_label = f"Day {i // 2 + 6} — {'9:00 AM' if i % 2 == 0 else '1:00 PM'}"
            slot_labels.append(new_label)
            db.session.add(TimeSlot(slot_number=i + 1, label=new_label))
        db.session.commit()

    # ---- Phase 3: Clear old timetable & persist new one ----
    TimetableEntry.query.delete()
    db.session.commit()

    timetable_rows = []
    subj_map = {s.id: s for s in subjects}

    for subject_id, color in color_map.items():
        slot_number = color + 1                   # 1-based
        slot_label  = slot_labels[color]

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


def load_sample_data():
    """
    Clears all existing data and inserts a robust sample academic dataset:
      - 6 Subjects (Algorithms, Data Structures, etc.)
      - 6 Students
      - 15 Enrollments forming a realistic conflict graph structure.
    """
    from app.models import Subject, Student, Enrollment, TimetableEntry

    # 1. Clear database completely (order matters due to foreign keys)
    TimetableEntry.query.delete()
    Enrollment.query.delete()
    Student.query.delete()
    Subject.query.delete()
    db.session.commit()

    # 2. Add Subjects
    subjects = [
        Subject(code="CS101", name="Introduction to Programming"),
        Subject(code="CS201", name="Data Structures"),
        Subject(code="CS301", name="Algorithms & Complexity"),
        Subject(code="CS401", name="Database Systems"),
        Subject(code="CS501", name="Computer Networks"),
        Subject(code="MA101", name="Discrete Mathematics"),
    ]
    for s in subjects:
        db.session.add(s)
    db.session.commit()

    # 3. Add Students
    students = [
        Student(roll_no="S2024-01", name="Alice Smith", email="alice@edu.in"),
        Student(roll_no="S2024-02", name="Bob Jones", email="bob@edu.in"),
        Student(roll_no="S2024-03", name="Charlie Brown", email="charlie@edu.in"),
        Student(roll_no="S2024-04", name="David Miller", email="david@edu.in"),
        Student(roll_no="S2024-05", name="Eve Davies", email="eve@edu.in"),
        Student(roll_no="S2024-06", name="Frank Wilson", email="frank@edu.in"),
    ]
    for st in students:
        db.session.add(st)
    db.session.commit()

    # Create mapping for easy enrollment
    subj_map = {s.code: s.id for s in subjects}
    stud_map = {st.roll_no: st.id for st in students}

    # 4. Add Enrollments (forms conflict graph edges)
    enrollments_data = [
        ("S2024-01", "CS101"), ("S2024-01", "MA101"), ("S2024-01", "CS201"),
        ("S2024-02", "CS201"), ("S2024-02", "CS301"), ("S2024-02", "CS401"),
        ("S2024-03", "CS301"), ("S2024-03", "CS401"), ("S2024-03", "CS501"),
        ("S2024-04", "CS401"), ("S2024-04", "CS501"),
        ("S2024-05", "CS201"), ("S2024-05", "MA101"),
        ("S2024-06", "CS101"), ("S2024-06", "MA101"),
    ]

    for roll, code in enrollments_data:
        enr = Enrollment(student_id=stud_map[roll], subject_id=subj_map[code])
        db.session.add(enr)
    db.session.commit()

    return {"success": True, "message": "Sample data with 6 subjects, 6 students, and 15 enrollments loaded successfully."}

