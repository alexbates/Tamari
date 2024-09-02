from flask_wtf import FlaskForm
from flask_login import current_user
from flask_babel import lazy_gettext as _l
from wtforms import StringField, IntegerField, PasswordField, BooleanField, TextAreaField, SelectField, RadioField, SubmitField
from wtforms.validators import ValidationError, DataRequired, Optional, Email, EqualTo, Length
from app.models import User

def disallowed_chars(form, field):
    dis_chars = {'<', '>', '{', '}', '/*', '*/', ';'}
    try:
        if any(char in dis_chars for char in field.data):
            raise ValidationError(_l('Cannot contain <, >, {, }, ;, or *'))
    except:
        pass

class ExploreSearchForm(FlaskForm):
    search = StringField(validators=[DataRequired(),disallowed_chars])
    submit = SubmitField(_l('Submit'))

class EmptyForm(FlaskForm):
    submit = SubmitField(_l('Submit'))
