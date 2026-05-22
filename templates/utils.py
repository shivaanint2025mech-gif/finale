import os
from flask import current_app, render_template, url_for
from flask_mail import Message, Mail
from weasyprint import HTML
import pandas as pd
from uuid import uuid4
from werkzeug.security import generate_password_hash

mail = Mail()

def save_file(file, folder):
    if file and file.filename:
        filename = f"{uuid4().hex}_{file.filename}"
        path = os.path.join(current_app.config['UPLOAD_FOLDER'], 'uploads', folder, filename)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        file.save(path)
        return f"uploads/{folder}/{filename}"
    return None

def send_event_emails(event, participants, flier_path=None):
    with current_app.app_context():
        for student in participants:
            feedback_link = f"{current_app.config['BASE_URL']}/feedback/{event.id}/{student.id}"
            msg = Message(f"Event: {event.title} - Feedback Required", recipients=[student.email])
            msg.body = f"Dear {student.name},\n\nYou are registered for {event.title} on {event.start_date}.\n\n"
            msg.body += f"Event flier: {url_for('static', filename=flier_path, _external=True) if flier_path else 'Not available'}\n\n"
            msg.body += f"Please provide your feedback at: {feedback_link}\n\nThank you."
            if flier_path and os.path.exists(os.path.join(current_app.config['UPLOAD_FOLDER'], flier_path)):
                with current_app.open_resource(os.path.join(current_app.config['UPLOAD_FOLDER'], flier_path)) as fp:
                    msg.attach("flier.pdf" if flier_path.endswith('.pdf') else "flier.jpg", "application/octet-stream", fp.read())
            mail.send(msg)

def generate_event_pdf(event, participants, chief_guest_url):
    html = render_template('event_pdf.html', event=event, participants=participants, chief_guest_url=chief_guest_url)
    pdf = HTML(string=html).write_pdf()
    return pdf

def import_students_from_excel(filepath):
    df = pd.read_excel(filepath)
    from models import db, Student, User
    for _, row in df.iterrows():
        name = row['name']
        email = row['email']
        roll = row['roll_number']
        joining_year = int(row['joining_year'])
        user = User.query.filter_by(email=email).first()
        if not user:
            user = User(email=email, password=generate_password_hash('student123'), role='student', name=name)
            db.session.add(user)
            db.session.flush()
        if not Student.query.filter_by(email=email).first():
            student = Student(user_id=user.id, name=name, email=email, roll_number=roll, joining_year=joining_year)
            db.session.add(student)
    db.session.commit()

def import_faculty_from_excel(filepath):
    df = pd.read_excel(filepath)
    from models import db, User
    for _, row in df.iterrows():
        name = row['name']
        email = row['email']
        dept = row['department']
        if not User.query.filter_by(email=email).first():
            user = User(email=email, password=generate_password_hash('faculty123'), role='faculty', name=name, department=dept)
            db.session.add(user)
    db.session.commit()