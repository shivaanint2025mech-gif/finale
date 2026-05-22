from app import app, db
from models import Event, Student, EventParticipant

with app.app_context():
    for event in Event.query.all():
        # If the event has a selected_batch_start (joining year), add missing participants
        if event.selected_batch_start:
            students = Student.query.filter_by(joining_year=event.selected_batch_start).all()
            added = 0
            for student in students:
                exists = EventParticipant.query.filter_by(event_id=event.id, student_id=student.id).first()
                if not exists:
                    ep = EventParticipant(event_id=event.id, student_id=student.id)
                    db.session.add(ep)
                    added += 1
            db.session.commit()
            print(f"Event '{event.title}': {added} participants added.")
    print("All done.")