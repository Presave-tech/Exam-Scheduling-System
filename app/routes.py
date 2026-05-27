"""
routes.py — Flask Route Handlers (Blueprint)
============================================
Phase 1 routes:
  GET  /                  → Dashboard
  GET/POST /subjects      → Manage subjects
  GET/POST /students      → Manage students
  GET/POST /enrollments   → Manage enrollments
  GET      /timetable     → View generated timetable
  POST     /generate      → Run algorithm & save timetable
  POST     /clear         → Clear timetable results
  POST     /load-sample   → Load sample data
  GET      /api/conflicts → JSON conflict pairs
  GET      /export/csv    → Download timetable as CSV

Phase 2 (TODO): /graph visualization, /export/pdf
"""

import csv
import io
import time
from flask import (Blueprint, render_template, request,
                   redirect, url_for, flash, jsonify,
                   make_response, current_app)

from app import db
from app.models import Subject, Student, Enrollment, TimetableEntry
from app.scheduler import generate_timetable

main = Blueprint("main", __name__)


# ──────────────────────────────────────────────────────────────
#  DASHBOARD
# ──────────────────────────────────────────────────────────────
@main.route("/")
def index():
    """Dashboard — shows summary statistics."""
    stats = {
        "subjects"   : Subject.query.count(),
        "students"   : Student.query.count(),
        "enrollments": Enrollment.query.count(),
        "timetable"  : TimetableEntry.query.count(),
    }
    # Grab existing timetable (grouped by slot) for preview
    entries = (
        db.session.query(TimetableEntry, Subject)
        .join(Subject, TimetableEntry.subject_id == Subject.id)
        .order_by(TimetableEntry.slot_number)
        .all()
    )
    return render_template("index.html", stats=stats, entries=entries)


# ──────────────────────────────────────────────────────────────
#  SUBJECTS
# ──────────────────────────────────────────────────────────────
@main.route("/subjects", methods=["GET", "POST"])
def subjects():
    """Add and list exam subjects."""
    if request.method == "POST":
        code    = request.form.get("code", "").strip().upper()
        name    = request.form.get("name", "").strip()

        if not code or not name:
            flash("Subject code and name are required.", "danger")
        elif Subject.query.filter_by(code=code).first():
            flash(f"Subject code '{code}' already exists.", "warning")
        else:
            db.session.add(Subject(code=code, name=name))
            db.session.commit()
            flash(f"Subject '{code} — {name}' added successfully.", "success")
        return redirect(url_for("main.subjects"))

    all_subjects = Subject.query.order_by(Subject.code).all()
    return render_template("subjects.html", subjects=all_subjects)


@main.route("/subjects/delete/<int:subject_id>", methods=["POST"])
def delete_subject(subject_id):
    """Delete a subject (cascades to enrollments & timetable)."""
    s = Subject.query.get_or_404(subject_id)
    db.session.delete(s)
    db.session.commit()
    flash(f"Subject '{s.code}' deleted.", "info")
    return redirect(url_for("main.subjects"))


# ──────────────────────────────────────────────────────────────
#  STUDENTS
# ──────────────────────────────────────────────────────────────
@main.route("/students", methods=["GET", "POST"])
def students():
    """Add and list students."""
    if request.method == "POST":
        roll_no = request.form.get("roll_no", "").strip().upper()
        name    = request.form.get("name",    "").strip()
        email   = request.form.get("email",   "").strip() or None

        if not roll_no or not name:
            flash("Roll number and name are required.", "danger")
        elif Student.query.filter_by(roll_no=roll_no).first():
            flash(f"Roll number '{roll_no}' already exists.", "warning")
        else:
            db.session.add(Student(roll_no=roll_no, name=name, email=email))
            db.session.commit()
            flash(f"Student '{name}' ({roll_no}) added successfully.", "success")
        return redirect(url_for("main.students"))

    all_students = Student.query.order_by(Student.roll_no).all()
    return render_template("students.html", students=all_students)


@main.route("/students/delete/<int:student_id>", methods=["POST"])
def delete_student(student_id):
    """Delete a student (cascades to enrollments)."""
    st = Student.query.get_or_404(student_id)
    db.session.delete(st)
    db.session.commit()
    flash(f"Student '{st.name}' deleted.", "info")
    return redirect(url_for("main.students"))


# ──────────────────────────────────────────────────────────────
#  ENROLLMENTS
# ──────────────────────────────────────────────────────────────
@main.route("/enrollments", methods=["GET", "POST"])
def enrollments():
    """Enroll students in subjects with checkboxes and matrix view."""
    if request.method == "POST":
        student_id = request.form.get("student_id", type=int)
        selected_subject_ids = request.form.getlist("subject_ids", type=int)

        if not student_id:
            flash("Please select a student.", "danger")
        else:
            # Get existing enrollments for the student
            existing_enrollments = Enrollment.query.filter_by(student_id=student_id).all()
            existing_subject_ids = {e.subject_id for e in existing_enrollments}
            selected_set = set(selected_subject_ids)

            # Remove subjects that are no longer selected
            for enr in existing_enrollments:
                if enr.subject_id not in selected_set:
                    db.session.delete(enr)
            
            # Add newly selected subjects
            for sub_id in selected_set:
                if sub_id not in existing_subject_ids:
                    db.session.add(Enrollment(student_id=student_id, subject_id=sub_id))

            db.session.commit()
            flash("Student's enrollments updated and synchronized.", "success")
        return redirect(url_for("main.enrollments"))

    # Sorting for matrix consistency
    all_students   = Student.query.order_by(Student.roll_no).all()
    all_subjects   = Subject.query.order_by(Subject.code).all()
    
    # For matrix: {student_id: list(subject_ids)}
    matrix = {st.id: [e.subject_id for e in st.enrollments] for st in all_students}

    return render_template("enrollments.html",
                           students=all_students,
                           subjects=all_subjects,
                           matrix=matrix)


# Delete enrollment is now handled by the sync logic in the POST /enrollments route.


# ──────────────────────────────────────────────────────────────
#  TIMETABLE — VIEW
# ──────────────────────────────────────────────────────────────
@main.route("/timetable")
def timetable():
    """Display the generated timetable grouped by slot."""
    entries = (
        db.session.query(TimetableEntry, Subject)
        .join(Subject, TimetableEntry.subject_id == Subject.id)
        .order_by(TimetableEntry.slot_number, Subject.code)
        .all()
    )

    # Group entries by slot_number for table display
    slots = {}
    for entry, subj in entries:
        slots.setdefault(entry.slot_number, {
            "label"   : entry.slot_label,
            "subjects": []
        })["subjects"].append(subj)

    return render_template("timetable.html", slots=slots)


# ──────────────────────────────────────────────────────────────
#  GENERATE TIMETABLE — Trigger Algorithm
# ──────────────────────────────────────────────────────────────
@main.route("/generate", methods=["POST"])
def generate():
    """Run the Graph Coloring algorithm and save results."""
    result = generate_timetable()
    if result["success"]:
        flash(result["message"], "success")
        # Store steps log in session for display on timetable page
        from flask import session
        session["steps_log"] = result["steps_log"]
        session["num_slots"] = result["num_slots"]
    else:
        flash(result["message"], "danger")
    return redirect(url_for("main.timetable"))


# ──────────────────────────────────────────────────────────────
#  CLEAR TIMETABLE
# ──────────────────────────────────────────────────────────────
@main.route("/clear", methods=["POST"])
def clear_timetable():
    """Delete all timetable entries."""
    TimetableEntry.query.delete()
    db.session.commit()
    flash("Timetable cleared.", "info")
    return redirect(url_for("main.timetable"))


# ──────────────────────────────────────────────────────────────
#  LOAD SAMPLE DATA
# ──────────────────────────────────────────────────────────────
@main.route("/load-sample", methods=["POST"])
def load_sample():
    """Triggers loading of sample academic data."""
    from app.scheduler import load_sample_data
    result = load_sample_data()
    flash(result["message"], "success")
    return redirect(url_for("main.index"))



# ──────────────────────────────────────────────────────────────
#  API — CONFLICT PAIRS (JSON)
# ──────────────────────────────────────────────────────────────
@main.route("/api/conflicts")
def api_conflicts():
    """
    Returns JSON list of conflict pairs (subjects sharing a student).
    Used by frontend to display conflict warnings.
    """
    from app.graph import ConflictGraph
    subjects    = Subject.query.all()
    enrollments = Enrollment.query.all()

    graph = ConflictGraph()
    graph.build_from_enrollments(subjects, enrollments)

    subj_map = {s.id: f"{s.code} — {s.name}" for s in subjects}
    pairs = [
        {"a": subj_map.get(u, u), "b": subj_map.get(v, v)}
        for (u, v) in graph.get_conflict_pairs()
    ]
    return jsonify({
        "total_subjects" : len(subjects),
        "total_edges"    : len(pairs),
        "conflict_pairs" : pairs,
    })


# ──────────────────────────────────────────────────────────────
#  INTERACTIVE CONFLICT GRAPH (VIS.JS)
# ──────────────────────────────────────────────────────────────
@main.route("/graph")
def graph_vis():
    """Render the Interactive Conflict Graph Visualization page."""
    return render_template("graph_vis.html")


@main.route("/api/graph-data")
def api_graph_data():
    """
    Returns JSON structured for vis.js network diagram:
      { nodes: [...], edges: [...] }
    Includes timetable slot coloring and degree-based node sizing.
    """
    from app.graph import ConflictGraph
    subjects    = Subject.query.all()
    enrollments = Enrollment.query.all()

    graph = ConflictGraph()
    graph.build_from_enrollments(subjects, enrollments)

    # Fetch existing timetable mapping
    entries = TimetableEntry.query.all()
    entry_map = {e.subject_id: e for e in entries}

    # Color palette
    HEX_COLORS = [
        "#6366F1",  # Indigo
        "#10B981",  # Emerald
        "#F59E0B",  # Amber
        "#EF4444",  # Rose
        "#3B82F6",  # Blue
        "#EC4899",  # Pink
        "#8B5CF6",  # Violet
        "#14B8A6",  # Teal
        "#F43F5E",  # Rose
        "#84CC16"   # Lime
    ]

    nodes = []
    for s in subjects:
        degree = len(graph.adjacency.get(s.id, []))
        entry = entry_map.get(s.id)
        
        node_color = "#E5E7EB"  # default gray
        font_color = "#1F2937"  # dark font
        
        slot_info = "Not scheduled yet"
        if entry is not None:
            c_idx = entry.color % len(HEX_COLORS)
            node_color = HEX_COLORS[c_idx]
            # Since shape is 'dot', labels are drawn outside the node on the white canvas.
            # We must use a dark font color so it's visible against the white background.
            font_color = "#1F2937"
            slot_info = f"Slot {entry.slot_number} ({entry.slot_label})"

        nodes.append({
            "id": s.id,
            "label": f"{s.code}\n{s.name}",
            "slot_info": slot_info,
            "color": {
                "background": node_color,
                "border": node_color,
                "highlight": {
                    "background": node_color,
                    "border": "#1F2937"
                }
            },
            "font": {
                "color": font_color, 
                "size": 14, 
                "bold": True,
                "strokeWidth": 3,
                "strokeColor": "#FFFFFF"
            },
            "value": 10 + degree * 4,  # node sizing based on degree
            "shape": "dot"
        })

    edges = []
    for u, v in graph.get_conflict_pairs():
        edges.append({
            "from": u,
            "to": v,
            "color": {"color": "#CBD5E1", "highlight": "#6366F1"},
            "width": 1.5
        })

    return jsonify({"nodes": nodes, "edges": edges})



#  EXPORT — CSV
# ──────────────────────────────────────────────────────────────
@main.route("/export/csv")
def export_csv():
    """Generates a downloadable CSV of the currently generated timetable."""
    entries = (
        db.session.query(TimetableEntry, Subject)
        .join(Subject, TimetableEntry.subject_id == Subject.id)
        .order_by(TimetableEntry.slot_number, Subject.code)
        .all()
    )

    if not entries:
        flash("No timetable exists to export. Please generate one first.", "warning")
        return redirect(url_for("main.timetable"))

    # Create CSV in-memory
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Write CSV header
    writer.writerow(["Slot Number", "Slot Time/Label", "Subject Code", "Subject Name"])
    
    # Write CSV data rows
    for entry, subj in entries:
        writer.writerow([entry.slot_number, entry.slot_label, subj.code, subj.name])
        
    response = make_response(output.getvalue())
    response.headers["Content-Disposition"] = "attachment; filename=exam_timetable.csv"
    response.headers["Content-Type"] = "text/csv"
    return response


# ──────────────────────────────────────────────────────────────
#  TIME SLOT CONFIGURATION
# ──────────────────────────────────────────────────────────────
@main.route("/slots", methods=["GET", "POST"])
def manage_slots():
    """List, add, edit, and reset exam time slots."""
    from app.models import TimeSlot
    
    if request.method == "POST":
        action = request.form.get("action")
        
        if action == "add":
            label = request.form.get("label", "").strip()
            if not label:
                flash("Time slot label cannot be empty.", "danger")
            else:
                # Find the next slot number
                max_slot = db.session.query(db.func.max(TimeSlot.slot_number)).scalar() or 0
                new_slot = TimeSlot(slot_number=max_slot + 1, label=label)
                db.session.add(new_slot)
                db.session.commit()
                flash(f"Slot {max_slot + 1} ('{label}') added successfully.", "success")
                
        elif action == "edit":
            slot_id = request.form.get("slot_id", type=int)
            label = request.form.get("label", "").strip()
            slot = TimeSlot.query.get(slot_id)
            if slot and label:
                slot.label = label
                db.session.commit()
                flash(f"Slot {slot.slot_number} label updated to '{label}'.", "success")
                
        elif action == "delete":
            # Delete the maximum slot number (must maintain sequential slots)
            max_slot = db.session.query(db.func.max(TimeSlot.slot_number)).scalar()
            if max_slot:
                slot = TimeSlot.query.filter_by(slot_number=max_slot).first()
                db.session.delete(slot)
                db.session.commit()
                flash(f"Deleted the last time slot (Slot {max_slot}).", "info")
            else:
                flash("No slots left to delete.", "warning")
                
        elif action == "reset":
            TimeSlot.query.delete()
            default_labels = [
                "Day 1 — 9:00 AM", "Day 1 — 1:00 PM",
                "Day 2 — 9:00 AM", "Day 2 — 1:00 PM",
                "Day 3 — 9:00 AM", "Day 3 — 1:00 PM",
                "Day 4 — 9:00 AM", "Day 4 — 1:00 PM",
                "Day 5 — 9:00 AM", "Day 5 — 1:00 PM",
            ]
            for idx, label in enumerate(default_labels):
                db.session.add(TimeSlot(slot_number=idx + 1, label=label))
            db.session.commit()
            flash("Time slots reset to default standard schedule.", "info")
            
        return redirect(url_for("main.manage_slots"))

    # Fetch slots
    slots = TimeSlot.query.order_by(TimeSlot.slot_number).all()
    return render_template("slots.html", slots=slots)


