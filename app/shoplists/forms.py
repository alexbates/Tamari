from flask_wtf import FlaskForm
from flask_login import current_user
from wtforms import StringField, IntegerField, PasswordField, BooleanField, TextAreaField, SelectField, RadioField, SubmitField
from wtforms.validators import ValidationError, DataRequired, Optional, Email, EqualTo, Length
from app.models import User

class AddListForm(FlaskForm):
    newlist = StringField('Add a List', validators=[DataRequired()])
    submitlist = SubmitField('Submit')

class AddListItemForm(FlaskForm):
    newitem = StringField(validators=[DataRequired()])
    submititem = SubmitField('Add Item')

class EmptyForm(FlaskForm):
    submit = SubmitField('Submit')
