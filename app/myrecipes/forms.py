from flask_wtf import FlaskForm
from flask_login import current_user
from wtforms import StringField, IntegerField, PasswordField, BooleanField, TextAreaField, SelectField, RadioField, SubmitField
from wtforms.validators import ValidationError, DataRequired, Optional, Email, EqualTo, Length
from app.models import User

def disallowed_chars(form, field):
    dis_chars = {'<', '>', '{', '}'}
    if any(char in disallowed_chars for char in field.data):
        raise ValidationError('Cannot contain <, >, {, or }')

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
    submit = SubmitField('Submit')

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
    submit = SubmitField('Save')

class AddToListForm(FlaskForm):
    selectlist = SelectField(validators=[DataRequired()], choices=[])
    submit = SubmitField('Submit')

class AddToMealPlannerForm(FlaskForm):
    selectdate = SelectField(validators=[Optional()], choices=[])
    submit = SubmitField('Submit')

class EmptyForm(FlaskForm):
    submit = SubmitField('Submit')
