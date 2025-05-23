from flask_wtf import FlaskForm
from wtforms import StringField, DateField, TextAreaField, SubmitField, SelectField, IntegerField
from wtforms.validators import DataRequired, Email, Length, ValidationError, NumberRange
from datetime import date

class PolicyForm(FlaskForm):
    name = StringField('Policy Name', validators=[
        DataRequired(),
        Length(min=3, max=100)
    ])
    due_date = DateField('Due Date', validators=[DataRequired()], format='%Y-%m-%d')
    details = TextAreaField('Details', validators=[Length(max=500)])
    email = StringField('Notification Email', validators=[
        DataRequired(),
        Email()
    ])
    
    # Time selection fields - using 24-hour format for simplicity
    notification_hour = SelectField(
        'Notification Hour', 
        choices=[(i, f"{i:02d}") for i in range(24)],
        coerce=int,
        default=9
    )
    
    notification_minute = SelectField(
        'Notification Minute',
        choices=[(0, "00"), (15, "15"), (30, "30"), (45, "45")],
        coerce=int,
        default=0
    )
    
    submit = SubmitField('Save Policy')
    
    def validate_due_date(self, field):
        if field.data < date.today():
            raise ValidationError('Due date cannot be in the past.')
    
    def validate_due_date(self, field):
        if field.data < date.today():
            raise ValidationError('Due date cannot be in the past.')
