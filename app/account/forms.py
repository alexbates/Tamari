from flask_wtf import FlaskForm
from flask_login import current_user
from wtforms import StringField, IntegerField, PasswordField, BooleanField, TextAreaField, SelectField, RadioField, SubmitField
from wtforms.validators import ValidationError, DataRequired, Optional, Email, EqualTo, Length
from app.models import User

class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember_me = BooleanField('Remember Me')
    submit = SubmitField('Sign In')

class RegistrationForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired(), Length(3,64,message='Must be 3-64 characters long.')])
    password2 = PasswordField(
        'Repeat Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Register')

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user is not None:
            raise ValidationError('Please use a different email address.')

class AccountForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired()])
    password = PasswordField('New Password')
    password2 = PasswordField('Confirm Password', validators=[EqualTo('password')])
    submit = SubmitField('Save Changes')

    def __init__(self, original_email, *args, **kwargs):
        super(AccountForm, self).__init__(*args, **kwargs)
        self.original_email = original_email

    def validate_email(self, email):
        if email.data != self.original_email:
            user = User.query.filter_by(email=email.data).first()
            if user is not None:
                raise ValidationError('Please use a different email address.')

class AccountPrefsForm(FlaskForm):
    propicture = RadioField(default=lambda: current_user.pref_picture, choices=[], validate_choice=False)
    accentcolor = RadioField(default=lambda: current_user.pref_color, choices=[], validate_choice=False)
    submit2 = SubmitField('Save Changes')

class ResetPasswordRequestForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    submit = SubmitField('Request Reset')

class ResetPasswordForm(FlaskForm):
    password = PasswordField('Password', validators=[DataRequired(), Length(3,64,message='Must be 3-64 characters long.')])
    password2 = PasswordField(
        'Repeat Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Set Password')

class EmptyForm(FlaskForm):
    submit = SubmitField('Submit')