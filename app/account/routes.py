from flask import render_template, flash, redirect, url_for, request, send_from_directory, jsonify, make_response
from flask_babel import _
from app import app, db, limiter
from app.account.forms import LoginForm, RegistrationForm, AccountForm, EmptyForm, ResetPasswordRequestForm, ResetPasswordForm, AccountPrefsForm
from flask_login import current_user, login_user, logout_user, login_required
from app.models import User, Recipe, NutritionalInfo, Category, Shoplist, Listitem, MealRecipe
from app.account.email import send_password_reset_email
from app.account.demo import reset_demo_account
from werkzeug.urls import url_parse
from io import StringIO, BytesIO, TextIOWrapper
import csv
from datetime import datetime, timedelta
from urllib.request import urlopen, Request
import secrets, time, random, os, imghdr, requests, re, urllib.request, zipfile
from app.account import bp
from config import Config
from version import __version__

@bp.before_request
def before_request():
    if current_user.is_authenticated:
        current_user.last_time = datetime.utcnow()
        db.session.commit()

# Used to validate images when restoring recipes from ZIP backup
def validate_image(stream):
    header = stream.read(512)
    stream.seek(0)
    format = imghdr.what(None, header)
    if not format:
        return None
    return '.' + format

@bp.route('/favicon.ico')
@limiter.limit(Config.DEFAULT_RATE_LIMIT)
def favicon():
    return redirect(url_for('static', filename='favicon.ico'))

@bp.route('/about')
@login_required
@limiter.limit(Config.DEFAULT_RATE_LIMIT)
def about():
    return render_template('about.html', title=_('About'),
        mdescription=_('Credits, changelog, and other information about the Tamari web app.'), app_version=__version__)

@limiter.limit(Config.LOGIN_RATE_LIMIT)
def rate_limited_login():
    return True

@bp.route('/login', methods=['GET', 'POST'])
@limiter.limit(Config.DEFAULT_RATE_LIMIT)
def login():
    if current_user.is_authenticated:
        return redirect(url_for('myrecipes.allRecipes'))
    form = LoginForm()
    # Minor redundancy in login process is intentional
    # This is due to previously allowing duplicate email accounts with different cases
    # The current solution allows existing duplicates to log in but prevents new duplicates from being registered
    if form.validate_on_submit():
        # Call rate limited function to effectively impose rate limit on registration attempts
        if rate_limited_login():
            # Attempt login with exact email provided by the user
            user = User.query.filter_by(email=form.email.data.strip()).first()
            # If no matching user is found, check using the lowercase email
            if user is None:
                email_lower = form.email.data.lower().strip()
                if email_lower != form.email.data.strip():
                    user = User.query.filter_by(email=email_lower).first()
            # Check login
            if user is None or not user.check_password(form.password.data.strip()):
                flash(_('Invalid email or password'))
                return redirect(url_for('account.login'))
            # Login the found user
            login_user(user, remember=form.remember_me.data)
            next_page = request.args.get('next')
            if not next_page or url_parse(next_page).netloc != '':
                next_page = url_for('myrecipes.allRecipes')
            return redirect(next_page)
    return render_template('login.html', title=_('Sign In'), mdescription=_('Sign In to the Tamari web app.'), form=form)

@bp.route('/logout')
@limiter.limit(Config.DEFAULT_RATE_LIMIT)
def logout():
    logout_user()
    flash(_('You have successfully signed out.'))
    return redirect(url_for('account.login'))

@limiter.limit(Config.REGISTRATION_RATE_LIMIT)
def rate_limited_registration():
    return True

@bp.route('/register', methods=['GET', 'POST'])
@limiter.limit(Config.DEFAULT_RATE_LIMIT)
def register():
    if current_user.is_authenticated:
        return redirect(url_for('myrecipes.allRecipes'))
    reg_disabled = app.config['REGISTRATION_DISABLED']
    form = RegistrationForm()
    if form.validate_on_submit() and not reg_disabled:
        # Call rate limited function to effectively impose rate limit on registration attempts
        if rate_limited_registration():
            # Check if email is already registered
            checkemail = User.query.filter_by(email=form.email.data.strip()).first()
            # Check if email in lowercase is already registered
            # This redundant check exists because account emails were originally case sensitive
            # It is necessary to check whether either variant exists in database
            email_lower = form.email.data.lower().strip()
            checkemail2 = User.query.filter_by(email=email_lower).first()
            # Validate email
            regex = re.compile(r'([A-Za-z0-9]+[.-_])*[A-Za-z0-9]+@[A-Za-z0-9-]+(\.[A-Z|a-z]{2,})+')
            emailisvalid = re.fullmatch(regex, form.email.data.strip())
            # Check length of email
            if len(form.email.data.strip()) < 3 or len(form.email.data.strip()) > 254:
                emailisvalid = False        
            # Error if email is registered
            if checkemail or checkemail2:
                flash('Error: ' + _('email is already taken.'))
            # Error if email is invalid for any reason
            elif emailisvalid is None or emailisvalid == False:
                flash('Error: ' + _('email is invalid.'))
            # Error if passwords do not match
            elif form.password.data.strip() != form.password2.data.strip():
                flash('Error: ' + _('passwords do not match.'))
            # Error if password length out of range
            elif len(form.password.data.strip()) < 3 or len(form.password.data.strip()) > 64:
                flash('Error: ' + _('password must be 3-64 characters.'))
            # Process registration
            else:
                logout_user()
                user = User(email=email_lower)
                user.set_password(form.password.data.strip())
                user.reg_time = datetime.utcnow()
                user.pref_size = 0
                user.pref_sort = 0
                user.pref_picture = 0
                user.pref_color = 0
                user.pref_theme = 0
                user.pref_scaling = 0
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
                flash(_('You have been registered! Please sign in.'))
                return redirect(url_for('account.login'))
    return render_template('register.html', title=_('Register'),
        mdescription=_('Register an account with the Tamari web app.'), form=form, reg_disabled=reg_disabled)

def clean_csv(text):
    try:
        new_text = text.replace("â€™", "'")
        new_text = new_text.replace("Â", "")
        new_text = new_text.replace("Ã—", "x")
    except:
        new_text = ""
    return new_text

@bp.route('/account/preferences', methods=['GET', 'POST'])
@login_required
@limiter.limit(Config.DEFAULT_RATE_LIMIT)
def user():
    form = AccountForm(current_user.email)
    form.email.data = current_user.email
    form2 = AccountPrefsForm(prefix='a')
    form3 = EmptyForm(prefix='b')
    form4 = EmptyForm(prefix='c')
    user = User.query.filter_by(email=current_user.email).first_or_404()
    recipes = user.recipes.order_by(Recipe.title)
    rec_count = 0
    for recipe in recipes:
        rec_count += 1
    # AccountForm
    if form.validate_on_submit():
        # If Demo Account, users cannot change email or password
        if current_user.email == 'demo@tamariapp.com':
            flash('Error: ' + _('account changes restricted for demo account.'))
            return redirect(url_for('account.user'))
        # Create variables that will be used for flashed messages
        has_passwords = False
        passwords_match = False
        # Check if form has passwords
        if form.password.data.strip() or form.password2.data.strip():
            has_passwords = True
            # Verify that passwords match
            if form.password.data.strip() == form.password2.data.strip():
                passwords_match = True
        # Validate email, convert to lowercase
        newemail = request.form.get('email').lower().strip()
        regex = re.compile(r'([A-Za-z0-9]+[.-_])*[A-Za-z0-9]+@[A-Za-z0-9-]+(\.[A-Z|a-z]{2,})+')
        emailisvalid = re.fullmatch(regex, newemail)
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
            flash('Error: ' + _('passwords do not match.'))
        # Error if email is invalid for any reason
        elif emailisvalid == False:
            flash('Error: ' + _('email is invalid.'))
        # Error if password length out of range
        elif has_passwords and (len(form.password.data.strip()) < 3 or len(form.password.data.strip()) > 64):
            flash('Error: ' + _('password must be between 3 and 64 characters.'))
        # Process changes
        elif has_passwords or newemail != current_user.email:
            if has_passwords:
                user.set_password(form.password.data.strip())
                # Update time in database for account password change
                user.p_change_time = datetime.utcnow()
            if current_user.email != newemail:
                current_user.email = newemail
                # Update time in database for account email change
                user.e_change_time = datetime.utcnow()
            db.session.commit()
            flash(_('Your changes have been saved.'))
            # Redirect to current page so form email will be updated following change
            return redirect(url_for('account.user'))
        # Notify if there are no errors or changes
        else:
            flash(_('No changes were made.'))
    # AccountPrefsForm
    if form2.validate_on_submit():
        # Get value from two select fields which has name attribute of selecttheme and selectscaling
        # This is needed since select fields are written manually instead of using {{ form2.selecttheme }} in template
        selecttheme = int(request.form['selecttheme'])
        selectscaling = int(request.form['selectscaling'])
        # Prevent form processing if hidden "Choose here" is selected
        if selecttheme == '' or selectscaling == '':
            flash('Error: ' + _('please select theme and scaling.'))
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
            if selectscaling >= 0 and selectscaling <= 2:
                user.pref_scaling = selectscaling
            db.session.commit()
            flash(_('Your changes have been saved.'))
    # Export Account Form
    if form3.submit.data and form3.validate_on_submit():
        # Store CSV data as string in memory, not on disk
        output = StringIO()
        fieldnames= ["title", "category", "photo", "description", "url", "prep_time", "cook_time", "total_time",
            "ingredients", "instructions", "time_created", "favorite", "public"]
        # Specify column headers for the CSV file
        writer = csv.DictWriter(output, fieldnames=fieldnames, quoting=csv.QUOTE_ALL)
        # Write Byte Order Mark (BOM) to output stream so MS Excel will recognize encoding when opening CSV
        output.write('\ufeff')
        # Write the column headers to the CSV file
        writer.writeheader()
        # For each recipe belonging to user, write recipe data as a row in the file
        for recipe in recipes:
            writer.writerow({
                'title': recipe.title,
                'category': recipe.category,
                'photo': recipe.photo,
                'description': recipe.description,
                'url': recipe.url,
                'prep_time': recipe.prep_time,
                'cook_time': recipe.cook_time,
                'total_time': recipe.total_time,
                'ingredients': recipe.ingredients.replace("\n", "<br>"),
                'instructions': recipe.instructions.replace("\n", "<br>"),
                'time_created': recipe.time_created.strftime("%Y-%m-%d %H:%M:%S.%f"),
                'favorite': recipe.favorite,
                'public': recipe.public
            })
        # Generate the zip filename based on current datetime
        current_date = datetime.now().strftime("%m-%d-%Y")
        zip_filename = f"Tamari-Backup-{current_date}.zip"
        # Create a ZIP file in memory
        zip_buffer = BytesIO()
        with zipfile.ZipFile(zip_buffer, mode='w') as zip_file:
            # Write the CSV containing recipes to the ZIP file
            zip_file.writestr("_recipes.csv", output.getvalue())
            # Write every photo associated with each recipe to the ZIP file
            for recipe in recipes:
                photo_path = os.path.join(app.config['UPLOAD_FOLDER'], recipe.photo)
                try:
                    zip_file.write(photo_path, os.path.basename(photo_path))
                except:
                    pass
        # Create a response with the ZIP file
        response = make_response(zip_buffer.getvalue())
        response.headers.set('Content-Type', 'application/zip')
        response.headers.set('Content-Disposition', 'attachment', filename=zip_filename)
        # Start the download
        return response
    # Import Account Form
    if form4.submit.data and form4.validate_on_submit():
        # If Demo Account, users cannot import data
        if current_user.email == 'demo@tamariapp.com':
            flash('Error: ' + _('data import restricted for demo account.'))
            return redirect(url_for('account.user'))
        zipbackup = request.files['zipbackup']
        if request.files and zipbackup.filename != '':
            # Read the uploaded file
            zip_data = zipbackup.read()
            with zipfile.ZipFile(BytesIO(zip_data)) as z:
                # Check if _recipes.csv is in the zip file
                if '_recipes.csv' in z.namelist():
                    # Extract the _recipes.csv file
                    with z.open('_recipes.csv') as csvfile:
                        csv_reader = csv.DictReader(TextIOWrapper(csvfile))
                        required_columns = {'\ufeff"title"', 'category', 'photo', 'description', 'url', 'prep_time',
                            'cook_time', 'total_time', 'ingredients', 'instructions', 'time_created', 'favorite',
                            'public'}
                        # Check is CSV file contains required columns
                        if not required_columns.issubset(csv_reader.fieldnames):
                            flash('Error: ' + _('backup is invalid, _recipes.csv in ZIP is missing columns.'))
                        else:
                            # Create counter that will keep track of how many recipes are imported
                            zip_count = 0
                            # Iterate over each row in the CSV
                            for row in csv_reader:
                                try:
                                    row_timecreated = datetime.strptime(row['time_created'], '%Y-%m-%d %H:%M:%S.%f')
                                except:
                                    # Skip loop iteration, date is not valid
                                    continue
                                recipe = Recipe.query.filter_by(user_id=current_user.id, time_created=row_timecreated).first()
                                if recipe:
                                    # Skip loop iteration, don't import recipe because it already exists
                                    continue
                                else:
                                    # Row is valid and recipe will be added by default
                                    # Made invalid later if fields from CSV columns do not pass checks
                                    invalid_row = False
                                    # Set of disallowed characters for row fields
                                    dis_chars = {'<', '>', '{', '}', '/*', '*/'}
                                    row_title = row['\ufeff"title"']
                                    # Don't add recipe if title length is invalid
                                    if len(row_title) > 80 or len(row_title) < 1:
                                        invalid_row = True
                                    # Don't add recipe if title contains invalid characters
                                    if any(char in row_title for char in dis_chars):
                                        invalid_row = True
                                    row_category = row['category']
                                    # Don't add recipe if category length is invalid
                                    if len(row_category) > 20 or len(row_category) < 1:
                                        invalid_row = True
                                    # Don't add recipe if category contains invalid characters
                                    if any(char in row_category for char in dis_chars):
                                        invalid_row = True
                                    row_photo = row['photo']
                                    row_description = row['description']
                                    # Don't add recipe if description length is invalid
                                    if len(row_description) > 500:
                                        invalid_row = True
                                    # Don't add recipe if description contains invalid characters
                                    if any(char in row_description for char in dis_chars):
                                        invalid_row = True
                                    row_url = row['url']
                                    # Don't add recipe if url length is invalid
                                    if len(row_url) > 200:
                                        invalid_row = True
                                    # Don't add recipe if url contains invalid characters
                                    if any(char in row_url for char in dis_chars):
                                        invalid_row = True
                                    # If times are present, they must be able to convert to int
                                    row_prep = row['prep_time']
                                    if row_prep:
                                        try:
                                            row_prep = int(row_prep)
                                        except:
                                            invalid_row = True
                                    row_cook = row['cook_time']
                                    if row_cook:
                                        try:
                                            row_cook = int(row_cook)
                                        except:
                                            invalid_row = True
                                    row_total = row['total_time']
                                    if row_total:
                                        try:
                                            row_total = int(row_total)
                                        except:
                                            invalid_row = True
                                    # Convert and validate ingredients
                                    row_ingredients = row['ingredients']
                                    row_ingredients = row_ingredients.replace("<br>", "\n")
                                    if len(row_ingredients) > 2200 or len(row_ingredients) < 1:
                                        invalid_row = True
                                    if any(char in row_ingredients for char in dis_chars):
                                        invalid_row = True
                                    row_instructions = row['instructions']
                                    row_instructions = row_instructions.replace("<br>", "\n")
                                    if len(row_instructions) > 6600 or len(row_instructions) < 1:
                                        invalid_row = True
                                    if any(char in row_instructions for char in dis_chars):
                                        invalid_row = True
                                    # Favorite and Public must be either a 0 or 1
                                    row_favorite = row['favorite']
                                    try:
                                        row_favorite = int(row_favorite)
                                        if row_favorite != 0 and row_favorite != 1:
                                            invalid_row = True
                                    except:
                                        invalid_row = True
                                    row_public = row['public']
                                    try:
                                        row_public = int(row_public)
                                        if row_public != 0 and row_public != 1:
                                            invalid_row = True
                                    except:
                                        invalid_row = True
                                    if invalid_row == False:
                                        # Create hexid for recipe that is going to be added
                                        hex_valid = 0
                                        while hex_valid == 0:
                                            hex_string = secrets.token_hex(4)
                                            hex_exist = Recipe.query.filter_by(hex_id=hex_string).first()
                                            if hex_exist is None:
                                                hex_valid = 1
                                        # Check if category exists for current user
                                        cat_exist = Category.query.filter(Category.label == row_category,
                                            Category.user_id == current_user.id).first()
                                        if cat_exist:
                                            pass
                                        # If category does not exist, add it to database
                                        else:
                                            cat_hex_valid = 0
                                            while cat_hex_valid == 0:
                                                cat_hex_string = secrets.token_hex(4)
                                                cat_hex_exist = Category.query.filter_by(hex_id=cat_hex_string).first()
                                                if cat_hex_exist is None:
                                                    cat_hex_valid = 1
                                            new_category = Category(hex_id=cat_hex_string, label=row_category, user_id=current_user.id)
                                            db.session.add(new_category)
                                            db.session.commit()
                                        bad_photo = False
                                        if row_photo and row_photo in z.namelist():
                                            with z.open(row_photo) as photo_file:
                                                file_extension = os.path.splitext(row_photo)[1].lower()
                                                val_ext = validate_image(photo_file)
                                                val_exts = []
                                                if val_ext == '.jpg':
                                                    val_exts.extend(['.jpg', '.jpeg'])
                                                elif val_ext == '.jpeg':
                                                    val_exts.extend(['.jpeg', '.jpg'])
                                                else:
                                                    val_exts.append(val_ext)
                                                if file_extension in val_exts:
                                                    hex_valid2 = 0
                                                    while hex_valid2 == 0:
                                                        hex_string2 = secrets.token_hex(8)
                                                        hex_exist2 = Recipe.query.filter(Recipe.photo.contains(hex_string2)).first()
                                                        if hex_exist2 is None:
                                                            hex_valid2 = 1
                                                    filename = hex_string2 + file_extension
                                                    new_file = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                                                    photo_file.seek(0)  # Reset file pointer
                                                    with open(new_file, 'wb') as f:
                                                        f.write(photo_file.read())
                                                else:
                                                    bad_photo = True
                                        else:
                                            bad_photo = True
                                        if bad_photo:
                                            defaults = ['default01.png', 'default02.png', 'default03.png', 'default04.png',
                                                'default05.png', 'default06.png', 'default07.png', 'default08.png', 'default09.png',
                                                'default10.png', 'default11.png', 'default12.png', 'default13.png', 'default14.png',
                                                'default15.png', 'default16.png', 'default17.png', 'default18.png', 'default19.png',
                                                'default20.png', 'default21.png', 'default22.png', 'default23.png', 'default24.png',
                                                'default25.png', 'default26.png', 'default27.png']
                                            filename = random.choice(defaults)
                                        # Add recipe to database
                                        recipe = Recipe(hex_id=hex_string, title=row_title, category=row_category,
                                            photo=filename, description=row_description, url=row_url, prep_time=row_prep,
                                            cook_time=row_cook, total_time=row_total, ingredients=row_ingredients,
                                            instructions=row_instructions, time_created=row_timecreated, favorite=row_favorite,
                                            public=row_public, user_id=current_user.id)
                                        db.session.add(recipe)
                                        db.session.commit()
                                        # Add 1 to the counter, which is used to inform user how many recipes are imported
                                        zip_count += 1
                            if zip_count == 0:
                                flash(_('No new recipes added. All recipes in the backup are already present.'))
                            else:
                                flash(_('Success: ') + str(zip_count) + _(' recipes have been imported.'))
                else:
                    flash('Error: ' + _('backup is invalid, _recipes.csv is missing from ZIP.'))
    return render_template('account-preferences.html', title=_('Account Preferences'),
        mdescription=_('View and modify account preferences for your Tamari account.'),
        user=user, form=form, form2=form2, form3=form3, form4=form4, rec_count=rec_count)
    
@bp.route('/account/history')
@login_required
@limiter.limit(Config.DEFAULT_RATE_LIMIT)
def accountHistory():
    # Create 2d events array which stores created recipes, edited recipes, account creation, email change, password change
    # Array format: event timestamp [0], event h1 [1], event h4 [2], event image [3], event description [4]
    events = []
    user = User.query.filter_by(email=current_user.email).first_or_404()
    # Get page number from URL query string
    page = request.args.get('page', 1, type=int)
    # per_page variable is used for paginating the recipes object
    per_page = app.config['ACCOUNT_EVENTS_PER_PAGE']
    recipes = user.recipes.order_by(Recipe.title)
    # Create an Event for every recipe created
    for recipe in recipes:
        event = []
        timestamp = recipe.time_created
        event_h1 = 'Created Recipe'
        event_h4 = recipe.title
        event_image = recipe.photo
        event_desc = 'Category: ' + recipe.category
        event.append(timestamp)
        event.append(event_h1)
        event.append(event_h4)
        event.append(event_image)
        event.append(event_desc)
        events.append(event)
    # Create an Event for edited recipes
    # but only if span between created and edited time is greater than 24 hours
    for recipe in recipes:
        if recipe.time_edited and (recipe.time_edited - recipe.time_created) >= timedelta(hours=24):
            event = []
            timestamp = recipe.time_edited
            event_h1 = 'Edited Recipe'
            event_h4 = recipe.title
            event_image = recipe.photo
            event_desc = _('Category: ') + recipe.category
            event.append(timestamp)
            event.append(event_h1)
            event.append(event_h4)
            event.append(event_image)
            event.append(event_desc)
            events.append(event)
    # Create account creation event
    if user.reg_time:
        event = []
        timestamp = user.reg_time
        event_h1 = 'Account Created'
        event_h4 = None
        event_image = None
        event_desc = _('Account registered with Tamari.')
        event.append(timestamp)
        event.append(event_h1)
        event.append(event_h4)
        event.append(event_image)
        event.append(event_desc)
        events.append(event)
    # Create account email change event
    if user.e_change_time:
        event = []
        timestamp = user.e_change_time
        event_h1 = 'Account Email Changed'
        event_h4 = None
        event_image = None
        event_desc = _('New Email: ') + user.email
        event.append(timestamp)
        event.append(event_h1)
        event.append(event_h4)
        event.append(event_image)
        event.append(event_desc)
        events.append(event)
    # Create account password change event
    if user.p_change_time:
        event = []
        timestamp = user.p_change_time
        event_h1 = 'Account Password Changed'
        event_h4 = None
        event_image = None
        event_desc = _('Changed Tamari password. Devices remained signed in.')
        event.append(timestamp)
        event.append(event_h1)
        event.append(event_h4)
        event.append(event_image)
        event.append(event_desc)
        events.append(event)
    # Sort events by most recent first
    sorted_events = sorted(events, key=lambda event: event[0], reverse=True)
    # Calculate the start and end indices for pagination
    start_index = (page - 1) * per_page
    end_index = start_index + per_page
    # Paginate the sorted_events array
    sorted_events_paginated = sorted_events[start_index:end_index]
    # Step 6: Create next and previous URLs for pagination
    next_url = url_for('account.accountHistory', page=page + 1) if end_index < len(sorted_events) else None
    prev_url = url_for('account.accountHistory', page=page - 1) if start_index > 0 else None
    # Create integer variables for year of first event and year of last event
    try:
        first_event_year = sorted_events_paginated[0][0].year
        last_event_year = sorted_events_paginated[-1][0].year
    except:
        first_event_year = None
        last_event_year = None
    # Create dictionary to effectively sort events by year
    events_by_year = {}
    # Build dictionary from sorted_events
    for event in sorted_events_paginated:
        try:
            event_year = event[0].year
            if event_year not in events_by_year:
                events_by_year[event_year] = []
            events_by_year[event_year].append(event)
        except:
            pass
    return render_template('account-history.html', title=_('Account History'),
        mdescription=_('Account History displays a timeline of events, or changes to your account.'),
        user=user, sorted_events=sorted_events, first_event_year=first_event_year, last_event_year=last_event_year,
        events_by_year=events_by_year, sorted_events_paginated=sorted_events_paginated, next_url=next_url, prev_url=prev_url)

@bp.route('/account/process-delete')
@login_required
@limiter.limit(Config.DEFAULT_RATE_LIMIT)
def deleteAccount():
    # If Demo Account, users cannot delete account
    if current_user.email == 'demo@tamariapp.com':
        flash('Error: ' + _('account deletion restricted for demo account.'))
        return redirect(url_for('account.user'))
    # Get user and handle if user doesn't exist
    user = User.query.filter_by(email=current_user.email).first()
    if user is None:
        flash('Error: ' + _('there was a problem deleting your account'))
        return redirect(url_for('account.user'))
    # Logout before delete
    logout_user()
    # Delete all recipes belonging to the current user
    recipes = Recipe.query.filter_by(user_id=user.id).all()
    # When deleting photos from recipe-photos directory, the photos are only deleted
    # if not one of the defaults
    defaults = ['default01.png', 'default02.png', 'default03.png', 'default04.png', 'default05.png', 'default06.png', 'default07.png',
        'default08.png', 'default09.png', 'default10.png', 'default11.png', 'default12.png', 'default13.png', 'default14.png',
        'default15.png', 'default16.png', 'default17.png', 'default18.png', 'default19.png', 'default20.png', 'default21.png',
        'default22.png', 'default23.png', 'default24.png', 'default25.png', 'default26.png', 'default27.png']
    for recipe in recipes:
        fullpath = app.config['UPLOAD_FOLDER'] + '/' + recipe.photo
        if recipe.photo not in defaults:
            try:
                os.remove(fullpath)
            except:
                pass
        db.session.delete(recipe)
    # Delete all other records belonging to the current user
    nutritional_infos = NutritionalInfo.query.filter_by(user_id=user.id).all()
    for nutritional_info in nutritional_infos:
        db.session.delete(nutritional_info)
    categories = Category.query.filter_by(user_id=user.id).all()
    for category in categories:
        db.session.delete(category)
    shoplists = Shoplist.query.filter_by(user_id=user.id).all()
    for shoplist in shoplists:
        db.session.delete(shoplist)
    listitems = Listitem.query.filter_by(user_id=user.id).all()
    for listitem in listitems:
        db.session.delete(listitem)
    mealrecipes = MealRecipe.query.filter_by(user_id=user.id).all()
    for mealrecipe in mealrecipes:
        db.session.delete(mealrecipe)
    # Delete account and redirect to login page
    db.session.delete(user)
    db.session.commit()
    flash(_('Your account has been deleted.'))
    return redirect(url_for('account.login'))

@bp.route('/request-reset', methods=['GET', 'POST'])
@limiter.limit(Config.DEFAULT_RATE_LIMIT)
def request_reset():
    # Don't display page if user is signed in
    if current_user.is_authenticated:
        return redirect(url_for('myrecipes.allRecipes'))
    form = ResetPasswordRequestForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data.strip()).first()
        if not user:
            email_lower = form.email.data.lower().strip()
            user = User.query.filter_by(email=email_lower).first()
        if user:
            # If Demo Account, users cannot delete account
            if user.email.lower() == 'demo@tamariapp.com':
                flash(_('Password reset disabled for demo.'))
                return redirect(url_for('account.login'))
            send_password_reset_email(user)
        flash(_('Check your email for instructions.'))
        return redirect(url_for('account.login'))
    return render_template('request-reset.html', title=_('Reset Password'),
        mdescription=_('Reset the password for your Tamari account.'), form=form)

@bp.route('/set-password/<token>', methods=['GET', 'POST'])
@limiter.limit(Config.DEFAULT_RATE_LIMIT)
def set_password(token):
    # Don't display page if user is signed in
    if current_user.is_authenticated:
        flash(_('Please sign out before setting a new password.'))
        return redirect(url_for('myrecipes.allRecipes'))
    user = User.verify_reset_password_token(token)
    if not user:
        flash(_('Password reset token is invalid.'))
        return redirect(url_for('account.login'))
    form = ResetPasswordForm()
    if form.validate_on_submit():
        user.set_password(form.password.data.strip())
        db.session.commit()
        flash(_('Your new password has been set.'))
        return redirect(url_for('account.login'))
    return render_template('set-password.html', title=_('Set Password'),
        mdescription=_('Set a new password for your Tamari account.'), form=form)
