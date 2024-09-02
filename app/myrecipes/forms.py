from flask_wtf import FlaskForm
from flask_login import current_user
from flask_babel import lazy_gettext as _l
from wtforms import StringField, IntegerField, PasswordField, BooleanField, TextAreaField, SelectField, RadioField, SubmitField
from wtforms.validators import ValidationError, DataRequired, Optional, Email, EqualTo, Length
from app.models import User
import re

# Validation for string and textarea fields
# Prevents input of code that a browser may interpret as HTML, CSS, or Javascript
def disallowed_chars(form, field):
    dis_chars = {'<', '>', '{', '}', '/*', '*/', ';'}
    try:
        if any(char in dis_chars for char in field.data):
            raise ValidationError(_l('Cannot contain <, >, {, }, ;, or *'))
    except:
        pass

# Validate URL in AutofillRecipeForm
def valid_url(form, field):
    url_pattern = re.compile(r'^(https?://)?(www\.)?([a-zA-Z0-9]+(\.[a-zA-Z0-9]+)+.*)$')
    try:
        if not url_pattern.match(field.data):
            raise ValidationError(_l('Invalid URL.'))
    except:
        pass

class DisplaySettingsForm(FlaskForm):
    recipe_size = RadioField(_l('Recipe Size'), choices=[(0, _l('Large')),(1, _l('Small')),(2, _l('Details'))], default=lambda: current_user.pref_size)
    sort_by = SelectField(choices=[(0, _l('Title')),(1, _l('Title (desc)')),(2, _l('Category')),(3, _l('Category (desc)')),(4, _l('Oldest first')),(5, _l('Newest first'))], default=lambda: current_user.pref_sort)
    submit = SubmitField(_l('Save'))

class AddCategoryForm(FlaskForm):
    category = StringField(_l('Add a Category'), validators=[DataRequired(),disallowed_chars])
    submitcat = SubmitField(_l('Submit'))

class AddRecipeForm(FlaskForm):
    recipe_name = StringField(validators=[DataRequired(),Length(1,80),disallowed_chars])
    category = SelectField(validators=[DataRequired()], choices=[])
    description = TextAreaField(validators=[Length(0,500),disallowed_chars])
    url = StringField(validators=[Length(0,200),disallowed_chars])
    servings = IntegerField(validators=[Optional()])
    prep_time = IntegerField(validators=[Optional()])
    cook_time = IntegerField(validators=[Optional()])
    total_time = IntegerField(validators=[Optional()])
    n_calories = IntegerField(validators=[Optional()])
    n_carbs = IntegerField(validators=[Optional()])
    n_protein = IntegerField(validators=[Optional()])
    n_fat = IntegerField(validators=[Optional()])
    n_sugar = IntegerField(validators=[Optional()])
    n_cholesterol = IntegerField(validators=[Optional()])
    n_sodium = IntegerField(validators=[Optional()])
    n_fiber = IntegerField(validators=[Optional()])
    ingredients = TextAreaField(validators=[DataRequired(),Length(1,2200),disallowed_chars])
    instructions = TextAreaField(validators=[DataRequired(),Length(1,6600),disallowed_chars])
    submit = SubmitField(_l('Submit'))
    
class AutofillRecipeForm(FlaskForm):
    autofillurl = StringField(validators=[Length(0,200),disallowed_chars,valid_url])
    submit = SubmitField(_l('Submit'))

class EditRecipeForm(FlaskForm):
    recipe_name = StringField(validators=[DataRequired(),Length(1,80),disallowed_chars])
    category = SelectField(validators=[DataRequired()], coerce=str, choices=[])
    description = TextAreaField(validators=[Length(0,500),disallowed_chars])
    url = StringField(validators=[Length(0,200),disallowed_chars])
    servings = IntegerField(validators=[Optional()])
    prep_time = IntegerField(validators=[Optional()])
    cook_time = IntegerField(validators=[Optional()])
    total_time = IntegerField(validators=[Optional()])
    n_calories = IntegerField(validators=[Optional()])
    n_carbs = IntegerField(validators=[Optional()])
    n_protein = IntegerField(validators=[Optional()])
    n_fat = IntegerField(validators=[Optional()])
    n_sugar = IntegerField(validators=[Optional()])
    n_cholesterol = IntegerField(validators=[Optional()])
    n_sodium = IntegerField(validators=[Optional()])
    n_fiber = IntegerField(validators=[Optional()])
    ingredients = TextAreaField(validators=[DataRequired(),Length(1,2200),disallowed_chars])
    instructions = TextAreaField(validators=[DataRequired(),Length(1,6600),disallowed_chars])
    submit = SubmitField(_l('Save'))

class AddToListForm(FlaskForm):
    selectlist = SelectField(validators=[DataRequired()], choices=[])
    submit = SubmitField(_l('Submit'))

class AddToMealPlannerForm(FlaskForm):
    selectdate = SelectField(validators=[Optional()], choices=[])
    submit = SubmitField(_l('Submit'))

class EmptyForm(FlaskForm):
    submit = SubmitField(_l('Submit'))
