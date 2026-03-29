"""
models.py — SQLAlchemy ORM Models
Defines database schema for Subjects, Students, Enrollments,
and TimetableEntries.
"""

from app import db


class Subject(db.Model):
    """
    Represents an exam subject (vertex in the conflict graph).
    """
    __tablename__ = "subjects"

    id      = db.Column(db.Integer, primary_key=True)
    code    = db.Column(db.String(20), unique=True, nullable=False)   # e.g. CS101
    name    = db.Column(db.String(100), nullable=False)               # e.g. Data Structures

    # Relationships
    enrollments = db.relationship("Enrollment", backref="subject", lazy=True, cascade="all, delete-orphan")
    timetable   = db.relationship("TimetableEntry", backref="subject", lazy=True, cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Subject {self.code}: {self.name}>"


class Student(db.Model):
    """
    Represents a student (shared enrollment creates graph edges).
    """
    __tablename__ = "students"

    id      = db.Column(db.Integer, primary_key=True)
    roll_no = db.Column(db.String(20), unique=True, nullable=False)
    name    = db.Column(db.String(100), nullable=False)
    email   = db.Column(db.String(120), unique=True, nullable=True)

    # Relationships
    enrollments = db.relationship("Enrollment", backref="student", lazy=True, cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Student {self.roll_no}: {self.name}>"


class Enrollment(db.Model):
    """
    Junction table: maps Students ↔ Subjects.
    If two subjects share an enrollment, they form a conflict edge.
    """
    __tablename__ = "enrollments"

    id         = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey("students.id"), nullable=False)
    subject_id = db.Column(db.Integer, db.ForeignKey("subjects.id"), nullable=False)

    # A student can only be enrolled in a subject once
    __table_args__ = (
        db.UniqueConstraint("student_id", "subject_id", name="unique_enrollment"),
    )

    def __repr__(self):
        return f"<Enrollment student={self.student_id} subject={self.subject_id}>"


class TimetableEntry(db.Model):
    """
    Stores the result of the Graph Coloring algorithm.
    Each subject is assigned a color (int) which maps to a TimeSlot label.
    """
    __tablename__ = "timetable_entries"

    id          = db.Column(db.Integer, primary_key=True)
    subject_id  = db.Column(db.Integer, db.ForeignKey("subjects.id"), nullable=False)
    slot_number = db.Column(db.Integer, nullable=False)   # 1-based slot index (= color + 1)
    slot_label  = db.Column(db.String(60), nullable=False) # e.g. "Slot 1 — Day 1, 9:00 AM"
    color       = db.Column(db.Integer, nullable=False)   # raw color assigned by algorithm

    def __repr__(self):
        return f"<TimetableEntry subject={self.subject_id} slot={self.slot_number}>"
