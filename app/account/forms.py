from flask_wtf import FlaskForm
from flask_login import current_user
from flask_babel import lazy_gettext as _l
from wtforms import StringField, IntegerField, PasswordField, BooleanField, TextAreaField, SelectField, RadioField, SubmitField
from wtforms.validators import ValidationError, DataRequired, Optional, Email, EqualTo, Length
from app.models import User

class LoginForm(FlaskForm):
    email = StringField(_l('Email'), validators=[DataRequired()])
    password = PasswordField(_l('Password'), validators=[DataRequired()])
    remember_me = BooleanField(_l('Remember Me'))
    submit = SubmitField(_l('Sign In'))

class RegistrationForm(FlaskForm):
    email = StringField(_l('Email'), validators=[DataRequired(), Email()])
    password = PasswordField(_l('Password'), validators=[DataRequired(), Length(3,64,message=_l('Must be 3-64 characters long.'))])
    password2 = PasswordField(_l('Repeat Password'), validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField(_l('Register'))

    # Automatically called for email field because matches pattern validate_fieldname
    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user is not None:
            raise ValidationError(_l('Please use a different email address.'))

class AccountForm(FlaskForm):
    email = StringField(_l('Email'), validators=[DataRequired(), Email()])
    password = PasswordField(_l('New Password'))
    password2 = PasswordField(_l('Confirm Password'), validators=[EqualTo('password')])
    submit = SubmitField(_l('Save Changes'))

    def __init__(self, original_email, *args, **kwargs):
        super(AccountForm, self).__init__(*args, **kwargs)
        self.original_email = original_email

    # Automatically called for email field because matches pattern validate_fieldname
    def validate_email(self, email):
        if email.data != self.original_email:
            user = User.query.filter_by(email=email.data).first()
            if user is not None:
                raise ValidationError(_l('Please use a different email address.'))

class AccountPrefsForm(FlaskForm):
    propicture = RadioField(default=lambda: current_user.pref_picture, choices=[], validate_choice=False)
    accentcolor = RadioField(default=lambda: current_user.pref_color, choices=[], validate_choice=False)
    submit2 = SubmitField(_l('Save Changes'))

class ResetPasswordRequestForm(FlaskForm):
    email = StringField(_l('Email'), validators=[DataRequired(), Email()])
    submit = SubmitField(_l('Request Reset'))

class ResetPasswordForm(FlaskForm):
    password = PasswordField(_l('Password'), validators=[DataRequired(), Length(3,64,message=_l('Must be 3-64 characters long.'))])
    password2 = PasswordField(_l('Repeat Password'), validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField(_l('Set Password'))

class EmptyForm(FlaskForm):
    submit = SubmitField(_l('Submit'))