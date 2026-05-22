from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime

db = SQLAlchemy()

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(20), nullable=False)
    name = db.Column(db.String(100))
    department = db.Column(db.String(100))

class Student(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    name = db.Column(db.String(100))
    email = db.Column(db.String(120))
    roll_number = db.Column(db.String(50))
    joining_year = db.Column(db.Integer)
    user = db.relationship('User', backref='student_profile')

class Event(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    faculty_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    academic_year = db.Column(db.String(20))
    semester = db.Column(db.String(10))
    event_type = db.Column(db.String(50))
    other_event_type = db.Column(db.String(100))
    title = db.Column(db.String(200))
    start_date = db.Column(db.Date)
    end_date = db.Column(db.Date)
    start_time = db.Column(db.String(10))
    end_time = db.Column(db.String(10))
    duration = db.Column(db.String(20))
    venue = db.Column(db.String(200))
    coordinator_name = db.Column(db.String(100))
    coordinator_contact = db.Column(db.String(20))
    coordinator_email = db.Column(db.String(120))
    permission_letter_path = db.Column(db.String(200))
    flier_path = db.Column(db.String(200))
    chief_guest_name = db.Column(db.String(100))
    chief_guest_designation = db.Column(db.String(100))
    chief_guest_institution = db.Column(db.String(100))
    chief_guest_profile_path = db.Column(db.String(200))
    optional_url = db.Column(db.String(300))
    selected_batch_start = db.Column(db.Integer)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class EventParticipant(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    event_id = db.Column(db.Integer, db.ForeignKey('event.id'))
    student_id = db.Column(db.Integer, db.ForeignKey('student.id'))
    feedback_sent = db.Column(db.Boolean, default=False)

class Feedback(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    event_id = db.Column(db.Integer, db.ForeignKey('event.id'))
    student_id = db.Column(db.Integer, db.ForeignKey('student.id'))
    rating = db.Column(db.Integer)
    comments = db.Column(db.Text)
    submitted_at = db.Column(db.DateTime, default=datetime.utcnow)