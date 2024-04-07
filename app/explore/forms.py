from flask_wtf import FlaskForm
from flask_login import current_user
from wtforms import StringField, IntegerField, PasswordField, BooleanField, TextAreaField, SelectField, RadioField, SubmitField
from wtforms.validators import ValidationError, DataRequired, Optional, Email, EqualTo, Length
from app.models import User

def disallowed_chars(form, field):
    dis_chars = {'<', '>', '{', '}', '/*', '*/', ';'}
    if any(char in dis_chars for char in field.data):
        raise ValidationError('Cannot contain <, >, {, }, ;, or *')

class ExploreSearchForm(FlaskForm):
    search = StringField(validators=[DataRequired(),disallowed_chars])
    submit = SubmitField('Submit')

class EmptyForm(FlaskForm):
    submit = SubmitField('Submit')
