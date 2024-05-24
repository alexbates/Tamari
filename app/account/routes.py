from flask import render_template, flash, redirect, url_for, request, send_from_directory, jsonify, make_response
from app import app, db, limiter
from app.account.forms import LoginForm, RegistrationForm, AccountForm, EmptyForm, ResetPasswordRequestForm, ResetPasswordForm, AccountPrefsForm
from flask_login import current_user, login_user, logout_user, login_required
from app.models import User, Recipe, Category, Shoplist, Listitem, MealRecipe
from app.account.email import send_password_reset_email
from werkzeug.urls import url_parse
from datetime import datetime
from urllib.request import urlopen, Request
import secrets, time, random, os, imghdr, requests, re, urllib.request
from app.account import bp
from config import Config

@bp.before_request
def before_request():
    if current_user.is_authenticated:
        current_user.last_time = datetime.utcnow()
        db.session.commit()
    
@bp.route('/favicon.ico')
def favicon():
    return redirect(url_for('static', filename='favicon.ico'))

@bp.route('/about')
@login_required
def about():
    return render_template('about.html', title='About')

@bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('myrecipes.allRecipes'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        # Check login
        if user is None or not user.check_password(form.password.data):
            flash('Invalid email or password')
            return redirect(url_for('account.login'))
        login_user(user, remember=form.remember_me.data)
        next_page = request.args.get('next')
        if not next_page or url_parse(next_page).netloc != '':
            next_page = url_for('myrecipes.allRecipes')
        return redirect(next_page)
    return render_template('login.html', title='Sign In', form=form)

@bp.route('/logout')
def logout():
    logout_user()
    flash('You have successfully signed out.')
    return redirect(url_for('account.login'))

@limiter.limit(Config.DEFAULT_RATE_LIMIT)
@bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('myrecipes.allRecipes'))
    form = RegistrationForm()
    if form.validate_on_submit():
        # Apply rate limit to POST requests that validate to prevent spamming database
        limiter.limit(Config.REGISTRATION_RATE_LIMIT)(lambda: None)()
        # Check if email is already registered
        checkemail = User.query.filter_by(email=form.email.data).first()
        # Validate email
        regex = re.compile(r'([A-Za-z0-9]+[.-_])*[A-Za-z0-9]+@[A-Za-z0-9-]+(\.[A-Z|a-z]{2,})+')
        emailisvalid = re.fullmatch(regex, form.email.data)
        # Check length of email
        if len(form.email.data) < 3 or len(form.email.data) > 254:
            emailisvalid = False        
        # Error if email is registered
        if checkemail:
            flash('Error: email is already taken.')
        # Error if email is invalid for any reason
        elif emailisvalid is None or emailisvalid == False:
            flash('Error: email is invalid.')
        # Error if passwords do not match
        elif form.password.data != form.password2.data:
            flash('Error: passwords do not match.')
        # Error if password length out of range
        elif len(form.password.data) < 3 or len(form.password.data) > 64:
            flash('Error: password must be 3-64 characters.')
        # Process registration
        else:
            logout_user()
            user = User(email=form.email.data)
            user.set_password(form.password.data)
            user.reg_time = datetime.utcnow()
            user.pref_size = 0
            user.pref_sort = 0
            user.pref_picture = 0
            user.pref_color = 0
            user.pref_theme = 0
            db.session.add(user)
            cats = ['Miscellaneous', 'Entrees', 'Sides']
            for cat in cats:
                hex_valid = 0
                while hex_valid == 0:
                    hex_string = secrets.token_hex(4)
                    hex_exist = Category.query.filter_by(hex_id=hex_string).first()
                    if hex_exist is None:
                        hex_valid = 1
                new_cat = Category(hex_id=hex_string, label=cat, user=user)
                db.session.add(new_cat)
            lists = ['Miscellaneous']
            for list in lists:
                hex_valid2 = 0
                while hex_valid2 == 0:
                    hex_string2 = secrets.token_hex(4)
                    hex_exist2 = Shoplist.query.filter_by(hex_id=hex_string2).first()
                    if hex_exist2 is None:
                        hex_valid2 = 1
                new_list = Shoplist(hex_id=hex_string2, label=list, user=user)
                db.session.add(new_list)
            db.session.commit()
            flash('You have been registerd! Please sign in.')
            return redirect(url_for('account.login'))
    return render_template('register.html', title='Register', form=form)

@bp.route('/account', methods=['GET', 'POST'])
@login_required
def user():
    form = AccountForm(current_user.email)
    form.email.data = current_user.email
    form2 = AccountPrefsForm(prefix='a')
    user = User.query.filter_by(email=current_user.email).first_or_404()
    recipes = user.recipes.order_by(Recipe.title)
    rec_count = 0
    for recipe in recipes:
        rec_count += 1
    # AccountForm
    if form.validate_on_submit():
        # Create variables that will be used for flashed messages
        has_passwords = False
        passwords_match = False
        # Check if form has passwords
        if form.password.data or form.password2.data:
            has_passwords = True
            # Verify that passwords match
            if form.password.data == form.password2.data:
                passwords_match = True
        # Validate email
        newemail = request.form.get('email')
        regex = re.compile(r'([A-Za-z0-9]+[.-_])*[A-Za-z0-9]+@[A-Za-z0-9-]+(\.[A-Z|a-z]{2,})+')
        emailisvalid = re.fullmatch(regex, form.email.data)
        if emailisvalid is None:
            emailisvalid = False
        # Check length of email
        if len(newemail) < 3 or len(newemail) > 254:
            emailisvalid = False
        # Check if new email exists in database
        if emailisvalid and newemail != current_user.email:
            checkuser = User.query.filter_by(email=newemail).first()
            if checkuser:
                emailisvalid = False
        # Error if there are passwords and they do not match
        if has_passwords and passwords_match == False:
            flash('Error: passwords do not match.')
        # Error if email is invalid for any reason
        elif emailisvalid == False:
            flash('Error: email is invalid.')
        # Error if password length out of range
        elif has_passwords and (len(form.password.data) < 3 or len(form.password.data) > 64):
            flash('Error: password must be between 3 and 64 characters.')
        # Process changes
        elif has_passwords or newemail != current_user.email:
            if has_passwords:
                user.set_password(form.password.data)
            if newemail != current_user.email:
                current_user.email = newemail
            db.session.commit()
            flash('Your changes have been saved.')
            # Redirect to current page so form email will be updated following change
            return redirect(url_for('account.user'))
        # Notify if there are no errors or changes
        else:
            flash('No changes were made.')
    # AccountPrefsForm
    if form2.validate_on_submit():
        # Get value from select field which has name attribute of selecttheme
        # This is needed since select field is written manually instead of using {{ form2.selecttheme }} in template
        selecttheme = int(request.form['selecttheme'])
        # Prevent form processing if hidden "Choose here" is selected
        if selecttheme == '':
            flash('Error: please select a theme.')
        else:
            propicture = int(request.form['propicture'])
            accentcolor = int(request.form['accentcolor'])
            # Change profile picture and accent color if values are valid
            if propicture >= 0 and propicture <= 3 and accentcolor >= 0 and accentcolor <= 3:
                user.pref_picture = propicture
                user.pref_color = accentcolor
            else:
                user.pref_picture = 0
                user.pref_color = 0
            if selecttheme >= 0 and selecttheme <= 2:
                user.pref_theme = selecttheme
            db.session.commit()
            flash('Your changes have been saved.')
    return render_template('account.html', title='Account', user=user, form=form, form2=form2, rec_count=rec_count)

@bp.route('/account/process-delete')
@login_required
def deleteAccount():
    # Get user and handle if user doesn't exist
    user = User.query.filter_by(email=current_user.email).first()
    if user is None:
        flash('Error: there was a problem deleting your account')
        return redirect(url_for('account.user'))
    # Logout before delete
    logout_user()
    # Delete account and redirect to login page
    db.session.delete(user)
    db.session.commit()
    flash('Your account has been deleted.')
    return redirect(url_for('account.login'))

@bp.route('/request-reset', methods=['GET', 'POST'])
def request_reset():
    # Don't display page if user is signed in
    if current_user.is_authenticated:
        return redirect(url_for('myrecipes.allRecipes'))
    form = ResetPasswordRequestForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user:
            send_password_reset_email(user)
        flash('Check your email for instructions.')
        return redirect(url_for('account.login'))
    return render_template('request-reset.html', title='Reset Password', form=form)

@bp.route('/set-password/<token>', methods=['GET', 'POST'])
def set_password(token):
    # Don't display page if user is signed in
    if current_user.is_authenticated:
        flash('Please sign out before setting a new password.')
        return redirect(url_for('myrecipes.allRecipes'))
    user = User.verify_reset_password_token(token)
    if not user:
        flash('Password reset token is invalid.')
        return redirect(url_for('account.login'))
    form = ResetPasswordForm()
    if form.validate_on_submit():
        user.set_password(form.password.data)
        db.session.commit()
        flash('Your new password has been set.')
        return redirect(url_for('account.login'))
    return render_template('set-password.html', title='Set Password', form=form)
