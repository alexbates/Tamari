from flask_wtf import FlaskForm
from flask_login import current_user
from wtforms import StringField, IntegerField, PasswordField, BooleanField, TextAreaField, SelectField, RadioField, SubmitField
from wtforms.validators import ValidationError, DataRequired, Optional, Email, EqualTo, Length
from app.models import User

# Validation for string and textarea fields
# Prevents input of code that a browser may interpret as HTML, CSS, or Javascript
def disallowed_chars(form, field):
    dis_chars = {'<', '>', '{', '}', '/*', '*/', ';'}
    if any(char in dis_chars for char in field.data):
        raise ValidationError('Cannot contain <, >, {, }, ;, or *')

# Validation for integer fields
def validate_integer(form, field):
    try:
        int(field.data)
    except ValueError:
        raise ValidationError('Must be integer')

class DisplaySettingsForm(FlaskForm):
    recipe_size = RadioField('Recipe Size', choices=[(0, 'Large'),(1, 'Small')], default=lambda: current_user.pref_size)
    sort_by = SelectField(choices=[(0, 'Title'),(1, 'Newest first'),(2, 'Oldest first')], default=lambda: current_user.pref_sort)
    submit = SubmitField('Save')

class AddCategoryForm(FlaskForm):
    category = StringField('Add a Category', validators=[DataRequired(),disallowed_chars])
    submitcat = SubmitField('Submit')

class AddRecipeForm(FlaskForm):
    recipe_name = StringField(validators=[DataRequired(),Length(1,80),disallowed_chars])
    category = SelectField(validators=[DataRequired()], choices=[])
    description = TextAreaField(validators=[Length(0,500),disallowed_chars])
    url = StringField(validators=[Length(0,200),disallowed_chars])
    servings = IntegerField(validators=[Optional(),validate_integer])
    prep_time = IntegerField(validators=[Optional(),validate_integer])
    cook_time = IntegerField(validators=[Optional(),validate_integer])
    total_time = IntegerField(validators=[Optional(),validate_integer])
    n_calories = IntegerField(validators=[Optional(),validate_integer])
    n_carbs = IntegerField(validators=[Optional(),validate_integer])
    n_protein = IntegerField(validators=[Optional(),validate_integer])
    n_fat = IntegerField(validators=[Optional(),validate_integer])
    n_sugar = IntegerField(validators=[Optional(),validate_integer])
    n_cholesterol = IntegerField(validators=[Optional(),validate_integer])
    n_sodium = IntegerField(validators=[Optional(),validate_integer])
    n_fiber = IntegerField(validators=[Optional(),validate_integer])
    ingredients = TextAreaField(validators=[DataRequired(),Length(1,2200),disallowed_chars])
    instructions = TextAreaField(validators=[DataRequired(),Length(1,6600),disallowed_chars])
    submit = SubmitField('Submit')

class EditRecipeForm(FlaskForm):
    recipe_name = StringField(validators=[DataRequired(),Length(1,80),disallowed_chars])
    category = SelectField(validators=[DataRequired()], coerce=str, choices=[])
    description = TextAreaField(validators=[Length(0,500),disallowed_chars])
    url = StringField(validators=[Length(0,200),disallowed_chars])
    servings = IntegerField(validators=[Optional(),validate_integer])
    prep_time = IntegerField(validators=[Optional(),validate_integer])
    cook_time = IntegerField(validators=[Optional(),validate_integer])
    total_time = IntegerField(validators=[Optional(),validate_integer])
    n_calories = IntegerField(validators=[Optional(),validate_integer])
    n_carbs = IntegerField(validators=[Optional(),validate_integer])
    n_protein = IntegerField(validators=[Optional(),validate_integer])
    n_fat = IntegerField(validators=[Optional(),validate_integer])
    n_sugar = IntegerField(validators=[Optional(),validate_integer])
    n_cholesterol = IntegerField(validators=[Optional(),validate_integer])
    n_sodium = IntegerField(validators=[Optional(),validate_integer])
    n_fiber = IntegerField(validators=[Optional(),validate_integer])
    ingredients = TextAreaField(validators=[DataRequired(),Length(1,2200),disallowed_chars])
    instructions = TextAreaField(validators=[DataRequired(),Length(1,6600),disallowed_chars])
    submit = SubmitField('Save')

class AddToListForm(FlaskForm):
    selectlist = SelectField(validators=[DataRequired()], choices=[])
    submit = SubmitField('Submit')

class AddToMealPlannerForm(FlaskForm):
    selectdate = SelectField(validators=[Optional()], choices=[])
    submit = SubmitField('Submit')

class EmptyForm(FlaskForm):
    submit = SubmitField('Submit')
