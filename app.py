import os
import pandas as pd
from datetime import datetime
from flask import (Flask, render_template, request, redirect, url_for,
                   flash, session, send_file, send_from_directory, make_response)
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
from itsdangerous import URLSafeTimedSerializer
from weasyprint import HTML
import sqlite3

app = Flask(__name__)
app.config['SECRET_KEY'] = 'hardcoded-dev-key-12345'   # fixed secret key

# Email mocking – no real SMTP, just prints to terminal
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'dummy@gmail.com'
app.config['MAIL_PASSWORD'] = 'dummy_password'

serializer = URLSafeTimedSerializer(app.config['SECRET_KEY'])

UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'pdf', 'img'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

def send_email(to, subject, body):
    """Simulate email sending – logs to terminal instead of real SMTP."""
    print(f"\n📧 SIMULATED EMAIL")
    print(f"To: {to}")
    print(f"Subject: {subject}")
    print(f"Body: {body}")
    print("--------------------\n")
    return True   # pretend success

# ---------- Database setup ----------
def get_db():
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    conn.executescript('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            role TEXT NOT NULL CHECK(role IN ('faculty','student')),
            name TEXT,
            designation TEXT
        );
        CREATE TABLE IF NOT EXISTS events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            faculty_email TEXT NOT NULL,
            academic_year TEXT,
            semester TEXT,
            event_type TEXT,
            other_event_type TEXT,
            title TEXT,
            start_date TEXT,
            end_date TEXT,
            start_time TEXT,
            end_time TEXT,
            duration TEXT,
            venue TEXT,
            coordinator_name TEXT,
            coordinator_contact TEXT,
            coordinator_email TEXT,
            batch TEXT,
            flier_filename TEXT,
            permission_filename TEXT,
            chief_guest_name TEXT,
            chief_guest_designation TEXT,
            chief_guest_institution TEXT,
            chief_guest_profile_filename TEXT,
            chief_guest_url TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS feedback (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            event_id INTEGER,
            student_email TEXT,
            rating INTEGER,
            comments TEXT,
            FOREIGN KEY(event_id) REFERENCES events(id)
        );
    ''')
    conn.commit()
    conn.close()

def preload_faculty():
    if not os.path.exists('database.db'):
        init_db()
    conn = get_db()
    cur = conn.execute("SELECT COUNT(*) FROM users WHERE role='faculty'")
    if cur.fetchone()[0] == 0:
        try:
            df = pd.read_excel('faculty mail id.xlsx')
            for _, row in df.iterrows():
                email = str(row['mail id']).strip().lower()
                name = str(row.get('staff name', ''))
                designation = str(row.get('designation', ''))
                existing = conn.execute("SELECT id FROM users WHERE email=?", (email,)).fetchone()
                if not existing:
                    hashed = generate_password_hash('faculty123')
                    conn.execute("INSERT INTO users (email, password, role, name, designation) VALUES (?,?,?,?,?)",
                                 (email, hashed, 'faculty', name, designation))
            conn.commit()
        except Exception as e:
            print("Could not preload faculty:", e)
    conn.close()

init_db()
preload_faculty()

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def login_required(role=None):
    from functools import wraps
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            if 'email' not in session:
                flash('Please log in first.', 'warning')
                return redirect(url_for('login'))
            if role and session.get('role') != role:
                flash('Access denied.', 'danger')
                return redirect(url_for('dashboard'))
            return f(*args, **kwargs)
        return wrapper
    return decorator

# ---------- Routes ----------
@app.route('/')
def home():
    return redirect(url_for('login'))

@app.route('/register', methods=['GET','POST'])
def register():
    if request.method == 'POST':
        role = request.form.get('role')
        email = request.form.get('email').strip().lower()
        password = request.form.get('password')
        name = request.form.get('name','')
        designation = request.form.get('designation','')

        if not role or not email or not password:
            flash('All fields are required.', 'danger')
            return render_template('register.html')

        conn = get_db()
        exists = conn.execute("SELECT id FROM users WHERE email=?", (email,)).fetchone()
        if exists:
            flash('Email already registered.', 'warning')
            conn.close()
            return render_template('register.html')

        hashed = generate_password_hash(password)
        conn.execute("INSERT INTO users (email, password, role, name, designation) VALUES (?,?,?,?,?)",
                     (email, hashed, role, name, designation))
        conn.commit()
        conn.close()
        flash('Registration successful! Please log in.', 'success')
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/login', methods=['GET','POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email').strip().lower()
        password = request.form.get('password')
        conn = get_db()
        user = conn.execute("SELECT * FROM users WHERE email=?", (email,)).fetchone()
        conn.close()

        if not user:
            flash('Email not registered. Please sign up.', 'danger')
            return render_template('login.html')
        if not check_password_hash(user['password'], password):
            flash('Incorrect password.', 'danger')
            return render_template('login.html', reset_email=email)

        session['email'] = user['email']
        session['role'] = user['role']
        session['name'] = user['name'] or email
        flash(f'Welcome, {user["name"] or email}!', 'success')
        return redirect(url_for('dashboard'))
    reset_email = request.args.get('reset_email','')
    return render_template('login.html', reset_email=reset_email)

@app.route('/forgot_password', methods=['GET','POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form.get('email').strip().lower()
        conn = get_db()
        user = conn.execute("SELECT id FROM users WHERE email=?", (email,)).fetchone()
        conn.close()
        if not user:
            flash('Email not found.', 'danger')
            return redirect(url_for('forgot_password'))
        token = serializer.dumps(email, salt='password-reset')
        reset_url = url_for('reset_password', token=token, _external=True)
        body = f'Click here to reset your password: {reset_url}\nThis link expires in 1 hour.'
        if send_email(email, 'Password Reset Request', body):
            flash('Reset link sent to your email (check terminal for simulation).', 'info')
        else:
            flash('Could not send email.', 'danger')
        return redirect(url_for('login'))
    return render_template('forgot_password.html')

@app.route('/reset_password/<token>', methods=['GET','POST'])
def reset_password(token):
    try:
        email = serializer.loads(token, salt='password-reset', max_age=3600)
    except:
        flash('Invalid or expired token.', 'danger')
        return redirect(url_for('login'))
    if request.method == 'POST':
        new_password = request.form.get('password')
        hashed = generate_password_hash(new_password)
        conn = get_db()
        conn.execute("UPDATE users SET password=? WHERE email=?", (hashed, email))
        conn.commit()
        conn.close()
        flash('Password updated. You can log in now.', 'success')
        return redirect(url_for('login'))
    return render_template('reset_password.html', token=token)

@app.route('/dashboard')
@login_required()
def dashboard():
    if session['role'] == 'faculty':
        conn = get_db()
        events = conn.execute("SELECT * FROM events WHERE faculty_email=? ORDER BY created_at DESC",
                              (session['email'],)).fetchall()
        conn.close()
        return render_template('faculty_dashboard.html', events=events)
    else:
        # Student dashboard: find events based on joining year
        student_email = session['email']
        joining_year = None
        try:
            df = pd.read_excel('student detail.xlsx')
            student_row = df[df['email'].str.strip().str.lower() == student_email]
            if not student_row.empty:
                joining_year = int(student_row.iloc[0]['joining year'])
        except Exception as e:
            print("Student detail error:", e)
        conn = get_db()
        events = []
        if joining_year:
            all_events = conn.execute("SELECT * FROM events").fetchall()
            for ev in all_events:
                batch_str = ev['batch']
                if batch_str:
                    try:
                        start_year = int('20' + batch_str.split('-')[0])  # '22' -> 2022
                        if start_year == joining_year:
                            events.append(ev)
                    except:
                        pass
        conn.close()
        return render_template('student_dashboard.html', events=events, joining_year=joining_year)

@app.route('/create_event', methods=['GET','POST'])
@login_required(role='faculty')
def create_event():
    if request.method == 'POST':
        academic_year = request.form['academic_year']
        semester = request.form['semester']
        event_type = request.form['event_type']
        other_event_type = request.form.get('other_event_type','')
        title = request.form['title']
        start_date = request.form['start_date']
        end_date = request.form['end_date']
        start_time = request.form['start_time']
        end_time = request.form['end_time']
        duration = request.form['duration']
        venue = request.form['venue']
        coordinator_name = request.form['coordinator_name']
        coordinator_contact = request.form['coordinator_contact']
        coordinator_email = request.form['coordinator_email']
        batch = request.form['batch']
        chief_guest_name = request.form['chief_guest_name']
        chief_guest_designation = request.form['chief_guest_designation']
        chief_guest_institution = request.form['chief_guest_institution']
        chief_guest_url = request.form.get('chief_guest_url','')

        flier_file = request.files.get('flier')
        permission_file = request.files.get('permission_letter')
        profile_file = request.files.get('chief_guest_profile')

        def save_upload(file):
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(filepath)
                return filename
            return None

        flier_filename = save_upload(flier_file)
        perm_filename = save_upload(permission_file)
        profile_filename = save_upload(profile_file)

        conn = get_db()
        conn.execute('''INSERT INTO events 
            (faculty_email, academic_year, semester, event_type, other_event_type, title,
             start_date, end_date, start_time, end_time, duration, venue,
             coordinator_name, coordinator_contact, coordinator_email, batch,
             flier_filename, permission_filename, chief_guest_name, chief_guest_designation,
             chief_guest_institution, chief_guest_profile_filename, chief_guest_url)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)''',
            (session['email'], academic_year, semester, event_type, other_event_type, title,
             start_date, end_date, start_time, end_time, duration, venue,
             coordinator_name, coordinator_contact, coordinator_email, batch,
             flier_filename, perm_filename, chief_guest_name, chief_guest_designation,
             chief_guest_institution, profile_filename, chief_guest_url))
        event_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
        conn.commit()
        conn.close()

        flash('Event created!', 'success')
        return redirect(url_for('view_event', event_id=event_id))

    return render_template('create_event.html')

@app.route('/event/<int:event_id>')
@login_required()
def view_event(event_id):
    conn = get_db()
    event = conn.execute("SELECT * FROM events WHERE id=?", (event_id,)).fetchone()
    conn.close()
    if not event:
        flash('Event not found.', 'danger')
        return redirect(url_for('dashboard'))
    if session['role'] == 'student':
        student_email = session['email']
        df = pd.read_excel('student detail.xlsx')
        student_row = df[df['email'].str.strip().str.lower() == student_email]
        if not student_row.empty:
            joining_year = int(student_row.iloc[0]['joining year'])
            batch_start = int('20' + event['batch'].split('-')[0])
            if joining_year != batch_start:
                flash('You are not a participant of this event.', 'danger')
                return redirect(url_for('dashboard'))
        else:
            flash('Student record not found.', 'danger')
            return redirect(url_for('dashboard'))
    return render_template('view_event.html', event=event)

@app.route('/event/<int:event_id>/participants')
@login_required(role='faculty')
def show_participants(event_id):
    conn = get_db()
    event = conn.execute("SELECT * FROM events WHERE id=?", (event_id,)).fetchone()
    conn.close()
    if not event:
        flash('Event not found.', 'danger')
        return redirect(url_for('dashboard'))
    batch = event['batch']  # e.g. "22-26"
    start_year = int('20' + batch.split('-')[0])  # 2022
    df = pd.read_excel('student detail.xlsx')
    participants = df[df['joining year'] == start_year]
    return render_template('participants.html', event=event, participants=participants)

@app.route('/event/<int:event_id>/send_feedback')
@login_required(role='faculty')
def send_feedback(event_id):
    conn = get_db()
    event = conn.execute("SELECT * FROM events WHERE id=?", (event_id,)).fetchone()
    conn.close()
    if not event:
        flash('Event not found.', 'danger')
        return redirect(url_for('dashboard'))
    batch = event['batch']
    start_year = int('20' + batch.split('-')[0])
    df = pd.read_excel('student detail.xlsx')
    participants = df[df['joining year'] == start_year]
    emails = participants['email'].dropna().tolist()
    feedback_link = url_for('give_feedback', event_id=event_id, _external=True)
    success_count = 0
    for email in emails:
        body = f'Hello,\n\nPlease fill the feedback form for "{event["title"]}": {feedback_link}'
        if send_email(email, f'Feedback: {event["title"]}', body):
            success_count += 1
    flash(f'Feedback emails sent to {success_count} participants (check terminal).', 'info')
    return redirect(url_for('view_event', event_id=event_id))

@app.route('/feedback/<int:event_id>', methods=['GET','POST'])
@login_required()
def give_feedback(event_id):
    if request.method == 'POST':
        rating = request.form.get('rating')
        comments = request.form.get('comments','')
        student_email = session['email']
        conn = get_db()
        conn.execute("INSERT INTO feedback (event_id, student_email, rating, comments) VALUES (?,?,?,?)",
                     (event_id, student_email, rating, comments))
        conn.commit()
        conn.close()
        flash('Thank you for your feedback!', 'success')
        return redirect(url_for('dashboard'))
    conn = get_db()
    event = conn.execute("SELECT id, title FROM events WHERE id=?", (event_id,)).fetchone()
    conn.close()
    if not event:
        flash('Event not found.', 'danger')
        return redirect(url_for('dashboard'))
    return render_template('feedback.html', event=event)

@app.route('/event/<int:event_id>/print')
@login_required(role='faculty')
def print_event(event_id):
    conn = get_db()
    event = conn.execute("SELECT * FROM events WHERE id=?", (event_id,)).fetchone()
    conn.close()
    if not event:
        flash('Event not found.', 'danger')
        return redirect(url_for('dashboard'))
    html = render_template('print_layout.html', event=event)
    pdf = HTML(string=html).write_pdf()
    response = make_response(pdf)
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = f'inline; filename=event_{event_id}.pdf'
    return response

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out.', 'info')
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)