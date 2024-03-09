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
    password = PasswordField('Password', validators=[DataRequired()])
    password2 = PasswordField(
        'Repeat Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Register')

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user is not None:
            raise ValidationError('Please use a different email address.')

class DisplaySettingsForm(FlaskForm):
    recipe_size = RadioField('Recipe Size', choices=[(0, 'Large'),(1, 'Small')], default=lambda: current_user.pref_size)
    sort_by = SelectField(choices=[(0, 'Title'),(1, 'Newest first'),(2, 'Oldest first')], default=lambda: current_user.pref_sort)
    submit = SubmitField('Save')

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

class AddCategoryForm(FlaskForm):
    category = StringField('Add a Category', validators=[DataRequired()])
    submitcat = SubmitField('Submit')

class AddRecipeForm(FlaskForm):
    recipe_name = StringField(validators=[DataRequired(),Length(1,80)])
    category = SelectField(validators=[DataRequired()], choices=[])
    description = TextAreaField(validators=[Length(0,500)])
    url = StringField(validators=[Length(0,200)])
    prep_time = IntegerField(validators=[Optional()])
    cook_time = IntegerField(validators=[Optional()])
    total_time = IntegerField(validators=[Optional()])
    ingredients = TextAreaField(validators=[DataRequired(),Length(1,2200)])
    instructions = TextAreaField(validators=[DataRequired(),Length(1,4400)])
    submit = SubmitField('Submit')

class EditRecipeForm(FlaskForm):
    recipe_name = StringField(validators=[DataRequired(),Length(1,80)])
    category = SelectField(validators=[DataRequired()], coerce=str, choices=[])
    description = TextAreaField(validators=[Length(0,500)])
    url = StringField(validators=[Length(0,200)])
    prep_time = IntegerField(validators=[Optional()])
    cook_time = IntegerField(validators=[Optional()])
    total_time = IntegerField(validators=[Optional()])
    ingredients = TextAreaField(validators=[DataRequired(),Length(1,2200)])
    instructions = TextAreaField(validators=[DataRequired(),Length(1,4400)])
    submit = SubmitField('Save')

class AddListForm(FlaskForm):
    newlist = StringField('Add a List', validators=[DataRequired()])
    submitlist = SubmitField('Submit')

class AddListItemForm(FlaskForm):
    newitem = StringField(validators=[DataRequired()])
    submititem = SubmitField('Add Item')

class AddToListForm(FlaskForm):
    selectlist = SelectField(validators=[DataRequired()], choices=[])
    submit = SubmitField('Submit')

class AddToMealPlannerForm(FlaskForm):
    selectdate = SelectField(validators=[Optional()], choices=[])
    submit = SubmitField('Submit')

class ExploreSearchForm(FlaskForm):
    search = StringField(validators=[DataRequired()])
    submit = SubmitField('Submit')

class EmptyForm(FlaskForm):
    submit = SubmitField('Submit')

class ResetPasswordRequestForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    submit = SubmitField('Request Reset')

class ResetPasswordForm(FlaskForm):
    password = PasswordField('Password', validators=[DataRequired()])
    password2 = PasswordField(
        'Repeat Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Set Password')
