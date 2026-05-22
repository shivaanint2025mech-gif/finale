from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import StringField, SelectField, DateField, URLField, PasswordField, IntegerField
from wtforms.validators import DataRequired, Email, Optional, EqualTo, Length

class RegistrationForm(FlaskForm):
    name = StringField('Full Name', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    role = SelectField('Role', choices=[('student', 'Student'), ('faculty', 'Faculty')], validators=[DataRequired()])
    joining_year = IntegerField('Joining Year (for students)', validators=[Optional()])
    department = StringField('Department (for faculty)', validators=[Optional()])

class EventForm(FlaskForm):
    academic_year = SelectField('Academic Year', choices=[('25-26','25-26'),('26-27','26-27'),('27-28','27-28'),('28-29','28-29')])
    semester = SelectField('Semester', choices=[('odd','Odd'),('even','Even')])
    event_type = SelectField('Event Type', choices=[
        ('FDP','FDP'),('guest lecture','Guest Lecture'),('conference','Conference'),
        ('workshop','Workshop'),('value added course','Value Added Course'),
        ('training program','Training Program'),('hands on session','Hands On Session'),('others','Others')
    ])
    other_event_type = StringField('Specify Other Type')
    title = StringField('Event Title', validators=[DataRequired()])
    start_date = DateField('Start Date', format='%Y-%m-%d', validators=[DataRequired()])
    end_date = DateField('End Date', format='%Y-%m-%d', validators=[DataRequired()])
    start_time = StringField('Start Time (HH:MM)', validators=[DataRequired()])
    end_time = StringField('End Time (HH:MM)', validators=[DataRequired()])
    duration = StringField('Duration (e.g., 2h 30m)', validators=[DataRequired()])
    venue = StringField('Venue', validators=[DataRequired()])
    coordinator_name = StringField('Coordinator Name', validators=[DataRequired()])
    coordinator_contact = StringField('Coordinator Contact', validators=[DataRequired()])
    coordinator_email = StringField('Coordinator Email', validators=[DataRequired(), Email()])
    joining_year = SelectField('Participant Joining Year', choices=[], coerce=int, validators=[DataRequired()])
    permission_letter = FileField('Permission Letter', validators=[FileAllowed(['pdf','png','jpg','jpeg'], 'PDF/Image only')])
    flier = FileField('Flier', validators=[FileAllowed(['pdf','png','jpg','jpeg'], 'PDF/Image only')])
    chief_guest_name = StringField('Chief Guest Name', validators=[DataRequired()])
    chief_guest_designation = StringField('Designation', validators=[DataRequired()])
    chief_guest_institution = StringField('Institution/Industry', validators=[DataRequired()])
    chief_guest_profile = FileField('Chief Guest Profile (PDF)', validators=[FileAllowed(['pdf'], 'PDF only')])
    optional_url = URLField('Optional URL (Link block)', validators=[Optional()])