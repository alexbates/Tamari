from flask import render_template, flash, redirect, url_for, request, send_from_directory, jsonify, make_response
from flask_babel import _
from app import app, db, limiter
from app.myrecipes.forms import AddCategoryForm, AddRecipeForm, AutofillRecipeForm, EditRecipeForm, AddToListForm, AddToMealPlannerForm, DisplaySettingsForm, EmptyForm, AdvancedSearchForm
from flask_login import current_user, login_user, logout_user, login_required
from flask_paginate import Pagination
from app.models import User, Recipe, Category, Shoplist, Listitem, MealRecipe, NutritionalInfo
from werkzeug.urls import url_parse
from datetime import datetime
from PIL import Image
from sqlalchemy import func, and_, or_
from sqlalchemy.sql import false
from urllib.parse import urlparse
from urllib.request import urlopen, Request
from bs4 import BeautifulSoup
from fake_useragent import UserAgent
from weasyprint import HTML
import secrets, time, random, os, imghdr, requests, re, urllib.request
from app.myrecipes import bp
from config import Config

@bp.context_processor
def inject_dynrootmargin():
    dynrootmargin = app.config['DYNAMIC_ROOT_MARGIN']
    return dict(dynrootmargin=dynrootmargin)

# New validation function for validating images on Add Recipe and Edit Recipe pages
def validate_image(stream):
    try:
        img = Image.open(stream)
        img.verify()
        format = img.format.lower()
        if format == 'jpeg':
            return '.jpg'
        return f'.{format}'
    except:
        return None

@bp.route('/recipe-photos/<path:filename>')
@limiter.limit(Config.DEFAULT_RATE_LIMIT)
def recipePhotos(filename):
    response = make_response(send_from_directory(app.root_path + '/appdata/recipe-photos/', filename))
    response.headers['Cache-Control'] = 'public, max-age=864000' # Cache for 1 month
    return response

# The get_recipe_info function is used by All Recipes, Favorites, Categories, and Mobile Category routes
# to build a recipe_info 2D array that is parallel to recipes object. It contains nearest scheduled date
# and last prepared date in MM/DD/YYYY format. If no date exists the array contains empty string in place of it.
def get_recipe_info(recipes):
    # Populate month array with the next 30 days of month, used for checking scheduled and last prepared
    month = []
    curr_dt = datetime.now()
    timestamp = int(time.mktime(curr_dt.timetuple()))
    # Loop 30 times
    for _ in range(30):
        date = datetime.fromtimestamp(timestamp)
        compactdate = date.strftime("%Y-%m-%d")
        month.append(compactdate)
        timestamp += 86400
    # Create recipe_info array that is parallel to recipes object, contains nearest scheduled date and last prepared
    recipe_info = []
    for recipe in recipes:
        # Query all meal plans for the current recipe
        meal_plans = MealRecipe.query.filter_by(recipe_id=recipe.id).all()
        # Find the nearest date
        nearest_date = None
        min_diff = float('inf')
        for plan in meal_plans:
            plan_date = datetime.strptime(plan.date, "%Y-%m-%d")
            for month_date in month:
                month_date_dt = datetime.strptime(month_date, "%Y-%m-%d")
                diff = abs((plan_date - month_date_dt).days)
                if diff < min_diff:
                    min_diff = diff
                    nearest_date = plan_date
        # If a nearest date is found, query for that specific date
        # Scheduled only includes recipes that are scheduled for today or in the future
        today = datetime.now().date()
        if nearest_date and nearest_date.date() >= today:
            scheduled_rec = MealRecipe.query.filter_by(recipe_id=recipe.id, date=nearest_date.strftime("%Y-%m-%d")).first()
            if scheduled_rec:
                scheduled_date = datetime.strptime(scheduled_rec.date, "%Y-%m-%d")
                # Convert to the desired MM/DD/YYYY format for display
                scheduled = scheduled_date.strftime("%m/%d/%Y")
            else:
                scheduled = None
        else:
            scheduled = None
        # create array that will store meal dates, excluding future planned meals
        meals_prepared = []
        for meal in meal_plans:
            if meal.date not in month:
                meals_prepared.append(meal.date)
        if meals_prepared:
            meal_count = len(meals_prepared)
            # Get last element of meals_prepared array
            last_date = meals_prepared[-1]
            # Convert date of last prepared meal to preferred format
            last_prepared = datetime.strptime(last_date, '%Y-%m-%d').strftime('%m/%d/%Y')
        else:
            meal_count = None
            last_prepared = None
        # Create array that contains scheduled date and last prepared and will be appended to recipe_info array
        recipe_info_single = []
        recipe_info_single.append(scheduled if scheduled else "")
        recipe_info_single.append(last_prepared if last_prepared else "")
        recipe_info.append(recipe_info_single)
    # Return recipe_info array to All Recipes, Favorites, Categories routes
    return recipe_info

@bp.route('/', methods=['GET', 'POST'])
@bp.route('/my-recipes/all', methods=['GET', 'POST'])
@login_required
@limiter.limit(Config.DEFAULT_RATE_LIMIT)
def allRecipes():
    user = User.query.filter_by(email=current_user.email).first_or_404()
    page = request.args.get('page', 1, type=int)
    # per_page variable is used for paginating the recipes object
    per_page = app.config['MAIN_RECIPES_PER_PAGE']
    # Query recipes for the current user depending on user sort preference
    # Select specific fields from Recipe and NutritionalInfo tables
    # Use outer join (left join) to prevent recipes that don't have calories from being excluded
    if user.pref_sort == 0:
        recipes_query = db.session.query(
            Recipe.id,
            Recipe.title,
            Recipe.category,
            Recipe.hex_id,
            Recipe.photo,
            Recipe.prep_time,
            Recipe.cook_time,
            Recipe.total_time,
            Recipe.time_created,
            NutritionalInfo.calories
        ).outerjoin(NutritionalInfo, Recipe.id == NutritionalInfo.recipe_id).filter(Recipe.user_id == user.id).order_by(func.lower(Recipe.title))
    elif user.pref_sort == 1:
        recipes_query = db.session.query(
            Recipe.id,
            Recipe.title,
            Recipe.category,
            Recipe.hex_id,
            Recipe.photo,
            Recipe.prep_time,
            Recipe.cook_time,
            Recipe.total_time,
            Recipe.time_created,
            NutritionalInfo.calories
        ).outerjoin(NutritionalInfo, Recipe.id == NutritionalInfo.recipe_id).filter(Recipe.user_id == user.id).order_by(func.lower(Recipe.title.desc()))
    elif user.pref_sort == 2:
        recipes_query = db.session.query(
            Recipe.id,
            Recipe.title,
            Recipe.category,
            Recipe.hex_id,
            Recipe.photo,
            Recipe.prep_time,
            Recipe.cook_time,
            Recipe.total_time,
            Recipe.time_created,
            NutritionalInfo.calories
        ).outerjoin(NutritionalInfo, Recipe.id == NutritionalInfo.recipe_id).filter(Recipe.user_id == user.id).order_by(func.lower(Recipe.category))
    elif user.pref_sort == 3:
        recipes_query = db.session.query(
            Recipe.id,
            Recipe.title,
            Recipe.category,
            Recipe.hex_id,
            Recipe.photo,
            Recipe.prep_time,
            Recipe.cook_time,
            Recipe.total_time,
            Recipe.time_created,
            NutritionalInfo.calories
        ).outerjoin(NutritionalInfo, Recipe.id == NutritionalInfo.recipe_id).filter(Recipe.user_id == user.id).order_by(func.lower(Recipe.category.desc()))
    elif user.pref_sort == 4:
        recipes_query = db.session.query(
            Recipe.id,
            Recipe.title,
            Recipe.category,
            Recipe.hex_id,
            Recipe.photo,
            Recipe.prep_time,
            Recipe.cook_time,
            Recipe.total_time,
            Recipe.time_created,
            NutritionalInfo.calories
        ).outerjoin(NutritionalInfo, Recipe.id == NutritionalInfo.recipe_id).filter(Recipe.user_id == user.id).order_by(Recipe.time_created)
    else:
        recipes_query = db.session.query(
            Recipe.id,
            Recipe.title,
            Recipe.category,
            Recipe.hex_id,
            Recipe.photo,
            Recipe.prep_time,
            Recipe.cook_time,
            Recipe.total_time,
            Recipe.time_created,
            NutritionalInfo.calories
        ).outerjoin(NutritionalInfo, Recipe.id == NutritionalInfo.recipe_id).filter(Recipe.user_id == user.id).order_by(Recipe.time_created.desc())
    # Paginate the queried recipes
    recipes = recipes_query.paginate(page=page, per_page=per_page, error_out=False)
    # Build recipe_info array using external function
    recipe_info = get_recipe_info(recipes)
    # Paginate the recipe_info array in the same way that recipes is paginated
    start_index = (page - 1) * per_page
    end_index = start_index + per_page
    recipe_info_paginated = recipe_info[start_index:end_index]
    next_url = url_for('myrecipes.allRecipes', page=recipes.next_num) \
        if recipes.has_next else None
    prev_url = url_for('myrecipes.allRecipes', page=recipes.prev_num) \
        if recipes.has_prev else None
    form = DisplaySettingsForm()
    if form.validate_on_submit():
        user.pref_size = form.recipe_size.data
        user.pref_sort = form.sort_by.data
        db.session.commit()
        return redirect(url_for('myrecipes.allRecipes'))
    return render_template('all-recipes.html', title=_('All Recipes'),
        mdescription=_('View all recipes saved in your account. This is the home page of the Tamari web app.'), user=user,
        recipes=recipes.items, form=form, next_url=next_url, prev_url=prev_url, recipe_info_paginated=recipe_info_paginated)

@bp.route('/old-api/my-recipes/all')
@login_required
@limiter.limit(Config.DEFAULT_RATE_LIMIT)
def apiAllRecipes():
    user = User.query.filter_by(email=current_user.email).first_or_404()
    page = request.args.get('page', 1, type=int)
    if user.pref_sort == 0:
        recipes = user.recipes.order_by(Recipe.title)
    elif user.pref_sort == 1:
        recipes = user.recipes.order_by(Recipe.time_created)
    else:
        recipes = user.recipes.order_by(Recipe.time_created.desc())
    rec_dict_comb = []
    rec_dict = {}
    for recipe in recipes:
        rec_dict = {'hex_id':recipe.hex_id,'title':recipe.title,'category':recipe.category,'photo':recipe.photo}
        rec_dict_comb.append(rec_dict)
    return make_response(jsonify(rec_dict_comb), 200)

@bp.route('/my-recipes/favorites', methods=['GET', 'POST'])
@login_required
@limiter.limit(Config.DEFAULT_RATE_LIMIT)
def favorites():
    user = User.query.filter_by(email=current_user.email).first_or_404()
    page = request.args.get('page', 1, type=int)
    # per_page variable is used for paginating the recipes object
    per_page = app.config['MAIN_RECIPES_PER_PAGE']
    # Query recipes for the current user depending on user sort preference
    # Select specific fields from Recipe and NutritionalInfo tables
    # Use outer join (left join) to prevent recipes that don't have calories from being excluded
    if user.pref_sort == 0:
        recipes_query = db.session.query(
            Recipe.id,
            Recipe.title,
            Recipe.category,
            Recipe.hex_id,
            Recipe.photo,
            Recipe.prep_time,
            Recipe.cook_time,
            Recipe.total_time,
            Recipe.time_created,
            NutritionalInfo.calories
        ).outerjoin(NutritionalInfo, Recipe.id == NutritionalInfo.recipe_id).filter(Recipe.user_id == user.id, Recipe.favorite == 1).order_by(func.lower(Recipe.title))
    elif user.pref_sort == 1:
        recipes_query = db.session.query(
            Recipe.id,
            Recipe.title,
            Recipe.category,
            Recipe.hex_id,
            Recipe.photo,
            Recipe.prep_time,
            Recipe.cook_time,
            Recipe.total_time,
            Recipe.time_created,
            NutritionalInfo.calories
        ).outerjoin(NutritionalInfo, Recipe.id == NutritionalInfo.recipe_id).filter(Recipe.user_id == user.id, Recipe.favorite == 1).order_by(func.lower(Recipe.title.desc()))
    elif user.pref_sort == 2:
        recipes_query = db.session.query(
            Recipe.id,
            Recipe.title,
            Recipe.category,
            Recipe.hex_id,
            Recipe.photo,
            Recipe.prep_time,
            Recipe.cook_time,
            Recipe.total_time,
            Recipe.time_created,
            NutritionalInfo.calories
        ).outerjoin(NutritionalInfo, Recipe.id == NutritionalInfo.recipe_id).filter(Recipe.user_id == user.id, Recipe.favorite == 1).order_by(func.lower(Recipe.category))
    elif user.pref_sort == 3:
        recipes_query = db.session.query(
            Recipe.id,
            Recipe.title,
            Recipe.category,
            Recipe.hex_id,
            Recipe.photo,
            Recipe.prep_time,
            Recipe.cook_time,
            Recipe.total_time,
            Recipe.time_created,
            NutritionalInfo.calories
        ).outerjoin(NutritionalInfo, Recipe.id == NutritionalInfo.recipe_id).filter(Recipe.user_id == user.id, Recipe.favorite == 1).order_by(func.lower(Recipe.category.desc()))
    elif user.pref_sort == 4:
        recipes_query = db.session.query(
            Recipe.id,
            Recipe.title,
            Recipe.category,
            Recipe.hex_id,
            Recipe.photo,
            Recipe.prep_time,
            Recipe.cook_time,
            Recipe.total_time,
            Recipe.time_created,
            NutritionalInfo.calories
        ).outerjoin(NutritionalInfo, Recipe.id == NutritionalInfo.recipe_id).filter(Recipe.user_id == user.id, Recipe.favorite == 1).order_by(Recipe.time_created)
    else:
        recipes_query = db.session.query(
            Recipe.id,
            Recipe.title,
            Recipe.category,
            Recipe.hex_id,
            Recipe.photo,
            Recipe.prep_time,
            Recipe.cook_time,
            Recipe.total_time,
            Recipe.time_created,
            NutritionalInfo.calories
        ).outerjoin(NutritionalInfo, Recipe.id == NutritionalInfo.recipe_id).filter(Recipe.user_id == user.id, Recipe.favorite == 1).order_by(Recipe.time_created.desc())
    # Paginate the queried recipes
    recipes = recipes_query.paginate(page=page, per_page=per_page, error_out=False)
    # Build recipe_info array using external function
    recipe_info = get_recipe_info(recipes)
    # Paginate the recipe_info array in the same way that recipes is paginated
    start_index = (page - 1) * per_page
    end_index = start_index + per_page
    recipe_info_paginated = recipe_info[start_index:end_index]
    next_url = url_for('myrecipes.favorites', page=recipes.next_num) \
        if recipes.has_next else None
    prev_url = url_for('myrecipes.favorites', page=recipes.prev_num) \
        if recipes.has_prev else None
    form = DisplaySettingsForm()
    if form.validate_on_submit():
        user.pref_size = form.recipe_size.data
        user.pref_sort = form.sort_by.data
        db.session.commit()
        return redirect(url_for('myrecipes.favorites'))
    return render_template('favorites.html', title=_('Favorites'),
        mdescription=_('View all recipes that have been marked as favorites in your Tamari account.'), user=user,
        recipes=recipes.items, form=form, next_url=next_url, prev_url=prev_url, recipe_info_paginated=recipe_info_paginated)

@bp.route('/my-recipes/recents', methods=['GET', 'POST'])
@login_required
@limiter.limit(Config.DEFAULT_RATE_LIMIT)
def recents():
    user = User.query.filter_by(email=current_user.email).first_or_404()
    page = request.args.get('page', 1, type=int)
    # per_page variable is used for paginating the recipes object
    per_page = app.config['MAIN_RECIPES_PER_PAGE']
    # Query recipes for the current user depending on user sort preference
    # Select specific fields from Recipe and NutritionalInfo tables
    # Use outer join (left join) to prevent recipes that don't have calories from being excluded
    recipes_query = db.session.query(
        Recipe.id,
        Recipe.title,
        Recipe.category,
        Recipe.hex_id,
        Recipe.photo,
        Recipe.prep_time,
        Recipe.cook_time,
        Recipe.total_time,
        Recipe.time_created,
        Recipe.last_time_viewed,
        NutritionalInfo.calories
    ).outerjoin(NutritionalInfo, Recipe.id == NutritionalInfo.recipe_id).filter(Recipe.user_id == user.id, Recipe.last_time_viewed.isnot(None)).order_by(Recipe.last_time_viewed.desc())
    # Paginate the queried recipes
    recipes = recipes_query.paginate(page=page, per_page=per_page, error_out=False)
    # Build recipe_info array using external function
    recipe_info = get_recipe_info(recipes)
    # Paginate the recipe_info array in the same way that recipes is paginated
    start_index = (page - 1) * per_page
    end_index = start_index + per_page
    recipe_info_paginated = recipe_info[start_index:end_index]
    next_url = url_for('myrecipes.recents', page=recipes.next_num) \
        if recipes.has_next else None
    prev_url = url_for('myrecipes.recents', page=recipes.prev_num) \
        if recipes.has_prev else None
    form = DisplaySettingsForm()
    if form.validate_on_submit():
        user.pref_size = form.recipe_size.data
        db.session.commit()
        return redirect(url_for('myrecipes.recents'))
    return render_template('recents.html', title=_('Recents'),
        mdescription=_('See all recently viewed recipes.'), user=user,
        recipes=recipes.items, form=form, next_url=next_url, prev_url=prev_url, recipe_info_paginated=recipe_info_paginated)

@bp.route('/recipe/<hexid>/favorite')
@login_required
@limiter.limit(Config.DEFAULT_RATE_LIMIT)
def favorite(hexid):
    recipe = Recipe.query.filter_by(hex_id=hexid).first()
    if recipe is None or recipe.user_id != current_user.id:
        flash('Error: ' + _('recipe does not exist or you do not have permission to modify it.'))
        return redirect(url_for('myrecipes.allRecipes'))
    recipe.favorite = 1
    db.session.commit()
    flash(_('This recipe has been added to your Favorites.'))
    return redirect(url_for('myrecipes.recipeDetail', hexid=hexid))

@bp.route('/recipe/<hexid>/unfavorite')
@login_required
@limiter.limit(Config.DEFAULT_RATE_LIMIT)
def unfavorite(hexid):
    recipe = Recipe.query.filter_by(hex_id=hexid).first()
    if recipe is None or recipe.user_id != current_user.id:
        flash('Error: ' + _('recipe does not exist or you do not have permission to modify it.'))
        return redirect(url_for('myrecipes.allRecipes'))
    recipe.favorite = 0
    db.session.commit()
    flash(_('This recipe has been removed from your Favorites.'))
    return redirect(url_for('myrecipes.recipeDetail', hexid=hexid))

@bp.route('/recipe/<hexid>/make-public')
@login_required
@limiter.limit(Config.DEFAULT_RATE_LIMIT)
def makePublic(hexid):
    recipe = Recipe.query.filter_by(hex_id=hexid).first()
    if recipe is None or recipe.user_id != current_user.id:
        flash('Error: ' + _('recipe does not exist or you do not have permission to modify it.'))
        return redirect(url_for('myrecipes.allRecipes'))
    recipe.public = 1
    db.session.commit()
    flash(_('You can now share the URL for this recipe.'))
    return redirect(url_for('myrecipes.recipeDetail', hexid=hexid))

@bp.route('/recipe/<hexid>/make-private')
@login_required
@limiter.limit(Config.DEFAULT_RATE_LIMIT)
def makePrivate(hexid):
    recipe = Recipe.query.filter_by(hex_id=hexid).first()
    if recipe is None or recipe.user_id != current_user.id:
        flash('Error: ' + _('recipe does not exist or you do not have permission to modify it.'))
        return redirect(url_for('myrecipes.allRecipes'))
    recipe.public = 0
    db.session.commit()
    flash(_('The recipe URL can no longer be shared.'))
    return redirect(url_for('myrecipes.recipeDetail', hexid=hexid))

@bp.route("/recipe/<hexid>/pdf")
def generatePDF(hexid):
    # Retrieve recipe data
    recipe = Recipe.query.filter_by(hex_id=hexid).first()
    if recipe is None:
        recipe_title = 'Recipe Not Found'
        owner = 0
        ingredients = ''
        instructions = ''
        nutrition = None
    else:
        recipe_title = recipe.title
        owner = recipe.user_id
        ingred = recipe.ingredients
        ingredientsdirty = ingred.split('\n')
        # Remove all kinds of line breaks from ingredients
        ingredients = []
        for item in ingredientsdirty:
            item = item.replace('\n','')
            item = item.replace('\r','')
            item = item.replace('\f','')
            item = item.replace('\u2028','')
            item = item.replace('\u2029','')
            ingredients.append(item)
        instruc = recipe.instructions
        instructionsdirty = instruc.split('\n')
        # Remove all kinds of line breaks from instructions
        instructions = []
        for item in instructionsdirty:
            item = item.replace('\n','')
            item = item.replace('\r','')
            item = item.replace('\f','')
            item = item.replace('\u2028','')
            item = item.replace('\u2029','')
            instructions.append(item)
        nutrition = NutritionalInfo.query.filter_by(recipe_id=recipe.id).first()
    # Render it with the same template used for printing
    html_str = render_template("print.html", title="Print - " + recipe_title,
        mdescription=_('View details for the selected recipe saved in My Recipes.'), recipe=recipe,
        owner=owner, ingredients=ingredients, instructions=instructions,
        nutrition=nutrition, hexid=hexid)
    # Convert the HTML to PDF using WeasyPrint
    pdf = HTML(string=html_str).write_pdf()
    # Return PDF as a download
    response = make_response(pdf)
    response.headers["Content-Type"] = "application/pdf"
    response.headers["Content-Disposition"] = "attachment; filename=recipe.pdf"
    return response

@bp.route('/recipe/<hexid>/print', methods=['GET'])
@limiter.limit(Config.DEFAULT_RATE_LIMIT)
def printRecipe(hexid):
    recipe = Recipe.query.filter_by(hex_id=hexid).first()
    if recipe is None:
        recipe_title = 'Recipe Not Found'
        owner = 0
        ingredients = ''
        instructions = ''
        nutrition = None
    else:
        recipe_title = recipe.title
        owner = recipe.user_id
        ingred = recipe.ingredients
        ingredientsdirty = ingred.split('\n')
        # Remove all kinds of line breaks from ingredients
        ingredients = []
        for item in ingredientsdirty:
            item = item.replace('\n','')
            item = item.replace('\r','')
            item = item.replace('\f','')
            item = item.replace('\u2028','')
            item = item.replace('\u2029','')
            ingredients.append(item)
        instruc = recipe.instructions
        instructionsdirty = instruc.split('\n')
        # Remove all kinds of line breaks from instructions
        instructions = []
        for item in instructionsdirty:
            item = item.replace('\n','')
            item = item.replace('\r','')
            item = item.replace('\f','')
            item = item.replace('\u2028','')
            item = item.replace('\u2029','')
            instructions.append(item)
        nutrition = NutritionalInfo.query.filter_by(recipe_id=recipe.id).first()
    return render_template('print.html', title="Print - " + recipe_title,
        mdescription=_('View details for the selected recipe saved in My Recipes.'), recipe=recipe,
        owner=owner, ingredients=ingredients, instructions=instructions,
        nutrition=nutrition, hexid=hexid) 

@bp.route('/recipe/<hexid>', methods=['GET', 'POST'])
@limiter.limit(Config.DEFAULT_RATE_LIMIT)
def recipeDetail(hexid):
    recipe = Recipe.query.filter_by(hex_id=hexid).first()
    # Ensure editedtime exists even when recipe doesn't exist
    editedtime = None
    form = AddToListForm()
    form2 = AddToMealPlannerForm(prefix='a')
    # Create 2D array that contains compact date and full date for Meal Planner scheduling
    w, h = 2, 30
    month = [[0 for x in range(w)] for y in range(h)]
    curr_dt = datetime.now()
    timestamp = int(time.mktime(curr_dt.timetuple()))
    days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    # Create array that is used for checking whether meal is past or future
    days30 = []
    for d in month:
        date = datetime.fromtimestamp(timestamp)
        intDay = date.weekday()
        full_month = date.strftime("%B")
        full_day = date.strftime("%-d")
        compact_month = date.strftime("%m")
        compact_day = date.strftime("%d")
        curr_year = date.strftime("%Y")
        compactdate = curr_year + "-" + compact_month + "-" + compact_day
        fulldate = days[intDay] + ", " + full_month + " " + full_day + ", " + curr_year
        d[0] = compactdate
        d[1] = fulldate
        days30.append(compactdate)
        timestamp += 86400
    # Populate choices for AddToListForm
    choices = []
    if current_user.is_authenticated:
        user = User.query.filter_by(email=current_user.email).first_or_404()
        # Update last time viewed in database, which is used for Recents page
        if current_user.id == recipe.user_id:
            recipe.last_time_viewed = datetime.utcnow()
            db.session.commit()
        lists = user.shop_lists.all()
        select_length = 0
        for list in lists:
            curr_list = list.label
            choices.append(curr_list)
            select_length += 1
        form.selectlist.choices = choices
    # Initialize variables to prevent unexpected errors if recipe is not found
    if recipe is None:
        recipe_title = 'Error'
        owner = 0
        ingredients = ''
        instructions = ''
        nutrition = None
        creationtime = None
        meal_count = None
        last_prepared = None
        scheduled = None
    else:
        recipe_title = recipe.title
        owner = recipe.user_id
        ingred = recipe.ingredients
        ingredientsdirty = ingred.split('\n')
        # Remove all kinds of line breaks from ingredients
        ingredients = []
        for item in ingredientsdirty:
            item = item.replace('\n','')
            item = item.replace('\r','')
            item = item.replace('\f','')
            item = item.replace('\u2028','')
            item = item.replace('\u2029','')
            ingredients.append(item)
        instruc = recipe.instructions
        instructionsdirty = instruc.split('\n')
        # Remove all kinds of line breaks from instructions
        instructions = []
        for item in instructionsdirty:
            item = item.replace('\n','')
            item = item.replace('\r','')
            item = item.replace('\f','')
            item = item.replace('\u2028','')
            item = item.replace('\u2029','')
            instructions.append(item)
        nutrition = NutritionalInfo.query.filter_by(recipe_id=recipe.id).first()
        # creationtime is the date of recipe creation, used for Information modal
        try:
            creationtime = recipe.time_created.strftime('%m/%d/%Y')
        except:
            creationtime = None
        try:
            editedtime = recipe.time_edited.strftime('%m/%d/%Y')
        except:
            editedtime = None
        # query all meals of the current recipe, including future planned meals
        all_meals = MealRecipe.query.filter_by(recipe_id=recipe.id).all()
        # create array that will store meal dates, excluding future planned meals
        meals_prepared = []
        for meal in all_meals:
            if meal.date not in days30:
                meals_prepared.append(meal.date)
        if meals_prepared:
            meal_count = len(meals_prepared)
            # Get last element of meals_prepared array
            last_date = meals_prepared[-1]
            # Convert date of last prepared meal to preferred format
            last_prepared = datetime.strptime(last_date, '%Y-%m-%d').strftime('%m/%d/%Y')
        else:
            meal_count = None
            last_prepared = None
        # Find the nearest date
        nearest_date = None
        min_diff = float('inf')
        for plan in all_meals:
            plan_date = datetime.strptime(plan.date, "%Y-%m-%d")
            for month_date in days30:
                month_date_dt = datetime.strptime(month_date, "%Y-%m-%d")
                diff = abs((plan_date - month_date_dt).days)
                if diff < min_diff:
                    min_diff = diff
                    nearest_date = plan_date
        # If a nearest date is found, query for that specific date
        # Scheduled only includes recipes that are scheduled for today or in the future
        today = datetime.now().date()
        if nearest_date and nearest_date.date() >= today:
            scheduled_rec = MealRecipe.query.filter_by(recipe_id=recipe.id, date=nearest_date.strftime("%Y-%m-%d")).first()
            if scheduled_rec:
                scheduled_date = datetime.strptime(scheduled_rec.date, "%Y-%m-%d")
                # Convert to the desired MM/DD/YYYY format for display
                scheduled = scheduled_date.strftime("%m/%d/%Y")
            else:
                scheduled = None
        else:
            scheduled = None
    # AddToListForm
    if form.validate_on_submit():
        list = Shoplist.query.filter_by(user_id=current_user.id, label=form.selectlist.data).first()
        listitems = list.list_items.all()
        a_listitems = []
        for item in listitems:
            curr_item = item.item
            a_listitems.append(curr_item)
        count = 0
        for ingred_item in ingredients:
            if ingred_item not in a_listitems:
                hex_valid = 0
                while hex_valid == 0:
                    hex_string = secrets.token_hex(5)
                    hex_exist = Listitem.query.filter_by(hex_id=hex_string).first()
                    if hex_exist is None:
                        hex_valid = 1
                listitem = Listitem(hex_id=hex_string, item=ingred_item, rec_title=recipe.title, user_id=current_user.id, complete=0, list_id=list.id)
                db.session.add(listitem)
                count += 1
        db.session.commit()
        if count != 0:
            message = str(count) + _(' items have been added to ') + str(list.label) + _(' shopping list.')
            flash(message)
        else:
            flash('Error: ' + _('all ingredients from this recipe are already on your shopping list.'))
    # If user selects hidden "Choose here" for AddToListForm
    if form.errors and not form2.validate_on_submit():
        flash('Error: ' + _('please select a shopping list.'))
    # AddToMealPlannerForm
    if form2.validate_on_submit():
        # Get value from select field which has name attribute of selectdate
        # This is needed since select field is written manually instead of using {{ form2.selectdate }} in template
        selectdate = request.form.get('selectdate')
        # Prevent form processing if hidden "Choose here" is selected
        if selectdate == '':
            flash('Error: ' + _('please select a date.'))
        else:
            hex_valid2 = 0
            while hex_valid2 == 0:
                hex_string2 = secrets.token_hex(5)
                hex_exist2 = MealRecipe.query.filter_by(hex_id=hex_string2).first()
                if hex_exist2 is None:
                    hex_valid2 = 1
            newmealplan = MealRecipe(hex_id=hex_string2, date=selectdate, recipe_id=recipe.id, user_id=current_user.id)
            # Verify that the recipe does not already exist in Meal Planner for selected day
            planexist = MealRecipe.query.filter_by(user_id=current_user.id, recipe_id=recipe.id, date=selectdate).first()
            if planexist is None:
                if any(selectdate in sublist for sublist in month):
                    db.session.add(newmealplan)
                    db.session.commit()
                    flash(_('This recipe has been added to your meal plan.'))
                else:
                    flash('Error: ' + _('the selected date in invalid.'))
            else:
                flash('Error: ' + _('this recipe is already scheduled for the selected date.'))
    return render_template('recipe-detail.html', title=recipe_title,
        mdescription=_('View details for the selected recipe saved in My Recipes.'), recipe=recipe, choices=choices,
        owner=owner, ingredients=ingredients, instructions=instructions, form=form, form2=form2, month=month, 
        nutrition=nutrition, creationtime=creationtime, editedtime=editedtime, meal_count=meal_count, 
        last_prepared=last_prepared, scheduled=scheduled, hexid=hexid) 

@bp.route('/my-recipes/categories', methods=['GET', 'POST'])
@login_required
@limiter.limit(Config.DEFAULT_RATE_LIMIT)
def categories():
    user = User.query.filter_by(email=current_user.email).first_or_404()
    categories = user.categories.order_by(Category.label).all()
    query_string = request.args.get('c')
    page = request.args.get('page', 1, type=int)
    # per_page variable is used for paginating the recipes object
    per_page = app.config['MAIN_RECIPES_PER_PAGE']
    # Query recipes for the current user depending on user sort preference
    # Select specific fields from Recipe and NutritionalInfo tables
    # Use outer join (left join) to prevent recipes that don't have calories from being excluded
    if query_string is None:
        rec_count = user.recipes.filter_by(category='Miscellaneous').all()
        if user.pref_sort == 0:
            recipes_query = db.session.query(
                Recipe.id,
                Recipe.title,
                Recipe.category,
                Recipe.hex_id,
                Recipe.photo,
                Recipe.prep_time,
                Recipe.cook_time,
                Recipe.total_time,
                Recipe.time_created,
                NutritionalInfo.calories
            ).outerjoin(NutritionalInfo, Recipe.id == NutritionalInfo.recipe_id).filter(Recipe.user_id == user.id, Recipe.category == 'Miscellaneous').order_by(func.lower(Recipe.title))
        elif user.pref_sort == 1:
            recipes_query = db.session.query(
                Recipe.id,
                Recipe.title,
                Recipe.category,
                Recipe.hex_id,
                Recipe.photo,
                Recipe.prep_time,
                Recipe.cook_time,
                Recipe.total_time,
                Recipe.time_created,
                NutritionalInfo.calories
            ).outerjoin(NutritionalInfo, Recipe.id == NutritionalInfo.recipe_id).filter(Recipe.user_id == user.id, Recipe.category == 'Miscellaneous').order_by(func.lower(Recipe.title.desc()))
        elif user.pref_sort == 2:
            recipes_query = db.session.query(
                Recipe.id,
                Recipe.title,
                Recipe.category,
                Recipe.hex_id,
                Recipe.photo,
                Recipe.prep_time,
                Recipe.cook_time,
                Recipe.total_time,
                Recipe.time_created,
                NutritionalInfo.calories
            ).outerjoin(NutritionalInfo, Recipe.id == NutritionalInfo.recipe_id).filter(Recipe.user_id == user.id, Recipe.category == 'Miscellaneous').order_by(func.lower(Recipe.category))
        elif user.pref_sort == 3:
            recipes_query = db.session.query(
                Recipe.id,
                Recipe.title,
                Recipe.category,
                Recipe.hex_id,
                Recipe.photo,
                Recipe.prep_time,
                Recipe.cook_time,
                Recipe.total_time,
                Recipe.time_created,
                NutritionalInfo.calories
            ).outerjoin(NutritionalInfo, Recipe.id == NutritionalInfo.recipe_id).filter(Recipe.user_id == user.id, Recipe.category == 'Miscellaneous').order_by(func.lower(Recipe.category.desc()))
        elif user.pref_sort == 4:
            recipes_query = db.session.query(
                Recipe.id,
                Recipe.title,
                Recipe.category,
                Recipe.hex_id,
                Recipe.photo,
                Recipe.prep_time,
                Recipe.cook_time,
                Recipe.total_time,
                Recipe.time_created,
                NutritionalInfo.calories
            ).outerjoin(NutritionalInfo, Recipe.id == NutritionalInfo.recipe_id).filter(Recipe.user_id == user.id, Recipe.category == 'Miscellaneous').order_by(Recipe.time_created)
        else:
            recipes_query = db.session.query(
                Recipe.id,
                Recipe.title,
                Recipe.category,
                Recipe.hex_id,
                Recipe.photo,
                Recipe.prep_time,
                Recipe.cook_time,
                Recipe.total_time,
                Recipe.time_created,
                NutritionalInfo.calories
            ).outerjoin(NutritionalInfo, Recipe.id == NutritionalInfo.recipe_id).filter(Recipe.user_id == user.id, Recipe.category == 'Miscellaneous').order_by(Recipe.time_created.desc())
    else:
        rec_count = user.recipes.filter_by(category=query_string).all()
        if user.pref_sort == 0:
            recipes_query = db.session.query(
                Recipe.id,
                Recipe.title,
                Recipe.category,
                Recipe.hex_id,
                Recipe.photo,
                Recipe.prep_time,
                Recipe.cook_time,
                Recipe.total_time,
                Recipe.time_created,
                NutritionalInfo.calories
            ).outerjoin(NutritionalInfo, Recipe.id == NutritionalInfo.recipe_id).filter(Recipe.user_id == user.id, Recipe.category == query_string).order_by(func.lower(Recipe.title))
        elif user.pref_sort == 1:
            recipes_query = db.session.query(
                Recipe.id,
                Recipe.title,
                Recipe.category,
                Recipe.hex_id,
                Recipe.photo,
                Recipe.prep_time,
                Recipe.cook_time,
                Recipe.total_time,
                Recipe.time_created,
                NutritionalInfo.calories
            ).outerjoin(NutritionalInfo, Recipe.id == NutritionalInfo.recipe_id).filter(Recipe.user_id == user.id, Recipe.category == query_string).order_by(func.lower(Recipe.title.desc()))
        elif user.pref_sort == 2:
            recipes_query = db.session.query(
                Recipe.id,
                Recipe.title,
                Recipe.category,
                Recipe.hex_id,
                Recipe.photo,
                Recipe.prep_time,
                Recipe.cook_time,
                Recipe.total_time,
                Recipe.time_created,
                NutritionalInfo.calories
            ).outerjoin(NutritionalInfo, Recipe.id == NutritionalInfo.recipe_id).filter(Recipe.user_id == user.id, Recipe.category == query_string).order_by(func.lower(Recipe.category))
        elif user.pref_sort == 3:
            recipes_query = db.session.query(
                Recipe.id,
                Recipe.title,
                Recipe.category,
                Recipe.hex_id,
                Recipe.photo,
                Recipe.prep_time,
                Recipe.cook_time,
                Recipe.total_time,
                Recipe.time_created,
                NutritionalInfo.calories
            ).outerjoin(NutritionalInfo, Recipe.id == NutritionalInfo.recipe_id).filter(Recipe.user_id == user.id, Recipe.category == query_string).order_by(func.lower(Recipe.category.desc()))
        elif user.pref_sort == 4:
            recipes_query = db.session.query(
                Recipe.id,
                Recipe.title,
                Recipe.category,
                Recipe.hex_id,
                Recipe.photo,
                Recipe.prep_time,
                Recipe.cook_time,
                Recipe.total_time,
                Recipe.time_created,
                NutritionalInfo.calories
            ).outerjoin(NutritionalInfo, Recipe.id == NutritionalInfo.recipe_id).filter(Recipe.user_id == user.id, Recipe.category == query_string).order_by(Recipe.time_created)
        else:
            recipes_query = db.session.query(
                Recipe.id,
                Recipe.title,
                Recipe.category,
                Recipe.hex_id,
                Recipe.photo,
                Recipe.prep_time,
                Recipe.cook_time,
                Recipe.total_time,
                Recipe.time_created,
                NutritionalInfo.calories
            ).outerjoin(NutritionalInfo, Recipe.id == NutritionalInfo.recipe_id).filter(Recipe.user_id == user.id, Recipe.category == query_string).order_by(Recipe.time_created.desc())
    # Paginate the queried recipes
    recipes = recipes_query.paginate(page=page, per_page=per_page, error_out=False)
    # Build recipe_info array using external function
    recipe_info = get_recipe_info(recipes)
    # Paginate the recipe_info array in the same way that recipes is paginated
    start_index = (page - 1) * per_page
    end_index = start_index + per_page
    recipe_info_paginated = recipe_info[start_index:end_index]
    next_url = url_for('myrecipes.categories', page=recipes.next_num, c=query_string) \
        if recipes.has_next else None
    prev_url = url_for('myrecipes.categories', page=recipes.prev_num, c=query_string) \
        if recipes.has_prev else None
    recipe_count = len(rec_count)
    form = DisplaySettingsForm()
    form2 = AddCategoryForm(prefix='a')
    cats = []
    for cat in categories:
        curr_cat = cat.label
        cats.append(curr_cat)
    # DisplaySettingsForm
    if form.submit.data and form.validate_on_submit():
        user.pref_size = form.recipe_size.data
        user.pref_sort = form.sort_by.data
        db.session.commit()
        return redirect(url_for('myrecipes.categories'))
    # AddCategoryForm
    if form2.validate_on_submit():
        if form2.category.data in cats:
            flash('Error: ' + _('the category you entered already exists.'))
        elif len(cats) > 39:
            flash('Error: ' + _('you are limited to 40 categories.'))
        else:
            hex_valid = 0
            while hex_valid == 0:
                hex_string = secrets.token_hex(4)
                hex_exist = Category.query.filter_by(hex_id=hex_string).first()
                if hex_exist is None:
                    hex_valid = 1
            category = Category(hex_id=hex_string, label=form2.category.data, user=current_user)
            db.session.add(category)
            db.session.commit()
            flash(_('The category has been added.'))
        return redirect(url_for('myrecipes.categories'))
    return render_template('categories.html', title=_('Categories'),
        mdescription=_('Displays a list of your saved categories and all recipes saved in the selected category.'), user=user,
        categories=categories, query_string=query_string, recipes=recipes.items, recipe_count=recipe_count, form=form,
        form2=form2, cats=cats, next_url=next_url, prev_url=prev_url, recipe_info_paginated=recipe_info_paginated)

@bp.route('/m/category/<catname>')
@login_required
@limiter.limit(Config.DEFAULT_RATE_LIMIT)
def mobileCategory(catname):
    user = User.query.filter_by(email=current_user.email).first_or_404()
    page = request.args.get('page', 1, type=int)
    rec_count = user.recipes.filter_by(category=catname).all()
    # Check whether requested category exists
    # If it doesn't set invalidcat to True, which is used by template to display error message
    category = user.categories.filter_by(label=catname).first()
    invalidcat = False
    if category is None:
        invalidcat = True
    # per_page variable is used for paginating the recipes object
    per_page = app.config['MAIN_RECIPES_PER_PAGE']
    # Query recipes for the current user depending on user sort preference
    # Select specific fields from Recipe and NutritionalInfo tables
    # Use outer join (left join) to prevent recipes that don't have calories from being excluded
    if user.pref_sort == 0:
        recipes_query = db.session.query(
            Recipe.id,
            Recipe.title,
            Recipe.category,
            Recipe.hex_id,
            Recipe.photo,
            Recipe.prep_time,
            Recipe.cook_time,
            Recipe.total_time,
            Recipe.time_created,
            NutritionalInfo.calories
        ).outerjoin(NutritionalInfo, Recipe.id == NutritionalInfo.recipe_id).filter(Recipe.user_id == user.id, Recipe.category == catname).order_by(func.lower(Recipe.title))
    elif user.pref_sort == 1:
        recipes_query = db.session.query(
            Recipe.id,
            Recipe.title,
            Recipe.category,
            Recipe.hex_id,
            Recipe.photo,
            Recipe.prep_time,
            Recipe.cook_time,
            Recipe.total_time,
            Recipe.time_created,
            NutritionalInfo.calories
        ).outerjoin(NutritionalInfo, Recipe.id == NutritionalInfo.recipe_id).filter(Recipe.user_id == user.id, Recipe.category == catname).order_by(func.lower(Recipe.title.desc()))
    elif user.pref_sort == 2:
        recipes_query = db.session.query(
            Recipe.id,
            Recipe.title,
            Recipe.category,
            Recipe.hex_id,
            Recipe.photo,
            Recipe.prep_time,
            Recipe.cook_time,
            Recipe.total_time,
            Recipe.time_created,
            NutritionalInfo.calories
        ).outerjoin(NutritionalInfo, Recipe.id == NutritionalInfo.recipe_id).filter(Recipe.user_id == user.id, Recipe.category == catname).order_by(func.lower(Recipe.category))
    elif user.pref_sort == 3:
        recipes_query = db.session.query(
            Recipe.id,
            Recipe.title,
            Recipe.category,
            Recipe.hex_id,
            Recipe.photo,
            Recipe.prep_time,
            Recipe.cook_time,
            Recipe.total_time,
            Recipe.time_created,
            NutritionalInfo.calories
        ).outerjoin(NutritionalInfo, Recipe.id == NutritionalInfo.recipe_id).filter(Recipe.user_id == user.id, Recipe.category == catname).order_by(func.lower(Recipe.category.desc()))
    elif user.pref_sort == 4:
        recipes_query = db.session.query(
            Recipe.id,
            Recipe.title,
            Recipe.category,
            Recipe.hex_id,
            Recipe.photo,
            Recipe.prep_time,
            Recipe.cook_time,
            Recipe.total_time,
            Recipe.time_created,
            NutritionalInfo.calories
        ).outerjoin(NutritionalInfo, Recipe.id == NutritionalInfo.recipe_id).filter(Recipe.user_id == user.id, Recipe.category == catname).order_by(Recipe.time_created)
    else:
        recipes_query = db.session.query(
            Recipe.id,
            Recipe.title,
            Recipe.category,
            Recipe.hex_id,
            Recipe.photo,
            Recipe.prep_time,
            Recipe.cook_time,
            Recipe.total_time,
            Recipe.time_created,
            NutritionalInfo.calories
        ).outerjoin(NutritionalInfo, Recipe.id == NutritionalInfo.recipe_id).filter(Recipe.user_id == user.id, Recipe.category == catname).order_by(Recipe.time_created.desc())
    # Paginate the queried recipes
    recipes = recipes_query.paginate(page=page, per_page=per_page, error_out=False)
    # Build recipe_info array using external function
    recipe_info = get_recipe_info(recipes)
    # Paginate the recipe_info array in the same way that recipes is paginated
    start_index = (page - 1) * per_page
    end_index = start_index + per_page
    recipe_info_paginated = recipe_info[start_index:end_index]
    next_url = url_for('myrecipes.mobileCategory', catname=catname, page=recipes.next_num) \
        if recipes.has_next else None
    prev_url = url_for('myrecipes.mobileCategory', catname=catname, page=recipes.prev_num) \
        if recipes.has_prev else None
    recipe_count = len(rec_count)
    return render_template('mobile-category.html',
        title=catname, mdescription=_('Displays a list of your saved categories and all recipes in the selected category.'),
        user=user, recipes=recipes.items, recipe_count=recipe_count, catname=catname, next_url=next_url, prev_url=prev_url,
        invalidcat=invalidcat, recipe_info_paginated=recipe_info_paginated)

@bp.route('/remove-category/<catid>')
@login_required
@limiter.limit(Config.DEFAULT_RATE_LIMIT)
def removeCategory(catid):
    category = Category.query.filter_by(hex_id=catid).first()
    user = User.query.filter_by(email=current_user.email).first()
    recipes = user.recipes.all()
    if category is None or category.user_id != current_user.id:
        flash('Error: ' + _('category does not exist or you do not have permission to remove it.'))
    elif category.label == 'Miscellaneous':
        flash('Error: ' + _('Miscellaneous cannot be deleted because it is the default category.'))
    else:
        if category.user_id == current_user.id:
            for recipe in recipes:
                if recipe.category == category.label:
                    recipe.category = 'Miscellaneous'
            db.session.delete(category)
            db.session.commit()
            flash(_('Category has been removed.'))
        else:
            flash('Error: ' + _('category does not exist.'))
    return redirect(url_for('myrecipes.categories'))

@bp.route('/remove-recipe/<hexid>')
@login_required
@limiter.limit(Config.DEFAULT_RATE_LIMIT)
def removeRecipe(hexid):
    # Query the recipe by hexid
    delrecipe = Recipe.query.filter_by(hex_id=hexid).first()
    if delrecipe is None or delrecipe.user_id != current_user.id:
        flash('Error: ' + _('recipe does not exist or you do not have permission to delete it.'))
        return redirect(url_for('myrecipes.allRecipes'))
    defaults = ['default01.png', 'default02.png', 'default03.png', 'default04.png', 'default05.png', 'default06.png', 'default07.png',
        'default08.png', 'default09.png', 'default10.png', 'default11.png', 'default12.png', 'default13.png', 'default14.png',
        'default15.png', 'default16.png', 'default17.png', 'default18.png', 'default19.png', 'default20.png', 'default21.png',
        'default22.png', 'default23.png', 'default24.png', 'default25.png', 'default26.png', 'default27.png', 'demo1.jpg', 'demo2.jpg',
        'demo3.jpg', 'demo4.jpg', 'demo5.jpg', 'demo6.jpg', 'demo7.jpg', 'demo8.jpg', 'demo9.jpg', 'demo10.jpg', 'demo11.jpg', 'demo12.jpg']
    fullpath = app.config['UPLOAD_FOLDER'] + '/' + delrecipe.photo
    if delrecipe.photo not in defaults:
        try:
            os.remove(fullpath)
        except:
            pass
    # Query and delete NutritionalInfo for specified recipe
    delnutrition = NutritionalInfo.query.filter_by(recipe_id=delrecipe.id).first()
    if delnutrition is not None:
        db.session.delete(delnutrition)
    # Query and deleted Meal Plans for specified recipe
    delmealrecipes = MealRecipe.query.filter_by(recipe_id=delrecipe.id).all()
    for mealrecipe in delmealrecipes:
        db.session.delete(mealrecipe)
    # Delete recipe and commit changes
    db.session.delete(delrecipe)
    db.session.commit()
    flash(_('Recipe has been removed.'))
    return redirect(url_for('myrecipes.allRecipes'))

@bp.route('/add-recipe', methods=['GET', 'POST'])
@login_required
@limiter.limit(Config.DEFAULT_RATE_LIMIT)
def addRecipe():
    form = AddRecipeForm()
    form2 = AutofillRecipeForm(prefix='a')
    choices = []
    user = User.query.filter_by(email=current_user.email).first_or_404()
    cats = user.categories.all()
    for cat in cats:
        curr_cat = cat.label
        choices.append(curr_cat)
    form.category.choices = choices
    # Autofill the Add to Recipe form from URL
    if form2.submit.data and form2.validate_on_submit():
        autofill_url = request.form['a-autofillurl']
        if autofill_url:
            headers = {
                'User-Agent': UserAgent().random,
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Accept-Encoding': 'gzip, deflate',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
            }
            try:
                page = requests.get(autofill_url, timeout=16, headers=headers)
                soup = BeautifulSoup(page.text, 'html.parser')
            except:
                page = None
                soup = BeautifulSoup('<html><body></body></html>', 'html.parser')
            # INITIALIZE VARIABLES PRIOR TO EXTRACTION
            title = None
            description = None
            servings = None
            preptime = None
            cooktime = None
            totaltime = None
            # EXTRACT TITLE
            title_1 = soup.find('meta',attrs={"property": "og:title"})
            if title_1:
                title = title_1['content']
            else:
                title_2 = soup.title
                title_2 = title_2.string if title_2 else ""
                title = title_2.split(' - ')[0] if ' - ' in title_2 else title_2
            # EXTRACT DESCRIPTION
            description_1 = soup.find('meta',attrs={"name": "description"})
            if description_1:
                description = description_1['content']
            else:
                description_2 = soup.find('meta',attrs={"property": "og:description"})
                if description_2:
                    description = description_2['content']
                else:
                    description = ''
            # EXTRACT SERVINGS
            # servings - wprm sites (type 1)
            servings_1 = soup.find('span',class_='wprm-recipe-servings-with-unit')
            # servings - wprm sites (type 2)
            servings_2 = soup.find('span',class_='wprm-recipe-servings-adjustable-tooltip')
            # servings - justapinch
            servings_3 = soup.find('span', class_='small text-uppercase', string='yield')
            # servings - pinchofyum
            servings_4 = soup.find('span',class_='tasty-recipes-yeild')
            # servings - tasty.co
            servings_5 = soup.find('p',class_='servings-display')
            # servings - food52
            servings_6 = soup.find('span',class_='recipe__details-heading', text='Serves')
            # servings - tasteofhome
            servings_7 = soup.find('div',class_='makes')
            # servings - taste.com.au
            servings_8 = soup.find('li', text='Serves')
            # servings - wprm sites (type 1)
            if servings_1:
                try:
                    servings_wprm = servings_1.find('span',class_='wprm-recipe-servings')
                except:
                    servings_wprm = None
                if servings_wprm:
                    try:
                        servings = servings_wprm.get_text()
                        servings = int(servings)
                    except:
                        servings = None
                else:
                    servings = None
            # servings - wprm sites (type 2)
            elif servings_2:
                try:
                    servings = servings_2.get_text()
                    servings = int(servings)
                except:
                    servings = None
            # servings - justapinch
            elif servings_3:
                try:
                    servings_jap = servings_3.find_next_siblings('span')
                    servings_jap2 = servings_jap[0].text
                    servings = servings_jap2.replace(' serving(s)', '').replace('serving', '').strip()
                    servings = int(servings)
                except:
                    servings = None
            # servings - pinchofyum
            elif servings_4:
                try:
                    servings_poy = servings_4.find('span', attrs={'data-amount': True})
                    servings = servings_poy[0].text
                    servings = int(servings)
                except:
                    servings = None
            # servings - tasty.co
            elif servings_5:
                try:
                    servings = servings_5.text
                    servings = servings.replace('for', '').replace('servings', '').replace('serving', '').replace(' ', '').strip()
                    servings = int(servings)
                except:
                    servings = None
            # servings - food52
            elif servings_6:
                try:
                    servings = servings_6.parent
                    servings = servings.text
                    servings = servings.replace('Serves', '').replace(' ', '').strip()
                    servings = re.match(r'\d+', servings)
                    servings = servings.group() if servings else None
                    servings = int(servings)
                except:
                    servings = None
            # servings - tasteofhome
            elif servings_7:
                try:
                    servings = servings_7.find('p')
                    servings = servings.text
                    servings = servings.replace('servings', '').replace('serving', '').replace(' ', '').strip()
                    servings = int(servings)
                except:
                    servings = None
            # servings - taste.com.au
            elif servings_8:
                try:
                    servings = servings_8.find('span')
                    servings = servings.text
                    servings = int(servings)
                except:
                    servings = None
            # EXTRACT PREP TIME
            # prep time - wprm sites
            preptime_1_m = soup.find('span',class_='wprm-recipe-details wprm-recipe-details-minutes wprm-recipe-prep_time wprm-recipe-prep_time-minutes')
            preptime_1_h = soup.find('span',class_='wprm-recipe-details wprm-recipe-details-hours wprm-recipe-prep_time wprm-recipe-prep_time-hours')
            # prep time - justapinch
            preptime_2 = soup.find('span', string='prep time')
            # prep time - pinchofyum
            preptime_3 = soup.find('span', class_='tasty-recipes-prep-time')
            # prep time - food52
            preptime_4 = soup.find('span',class_='recipe__details-heading', text='Prep time')
            # prep time - wprm sites
            if preptime_1_m or preptime_1_h:
                if preptime_1_m:
                    pt_m = preptime_1_m.contents[0]
                    pt_m = int(pt_m)
                else:
                    pt_m = 0
                if preptime_1_h:
                    pt_h = preptime_1_h.contents[0]
                    pt_h = int(pt_h)
                else:
                    pt_h = 0
                preptime = pt_m + (pt_h * 60)
            # prep time - justapinch
            elif preptime_2:
                preptime_jap = preptime_2.find_next_siblings('span')
                preptime_jap2 = preptime_jap[0].text
                if "Hr" in preptime_jap2:
                    pt_h = preptime_jap2[0]
                    pt_h = int(pt_h)
                    if "Min" in preptime_jap2:
                        pt_mins = re.search('Hr (.*)Min', preptime_jap2)
                        pt_m = pt_mins.group(1)
                        pt_m = int(pt_m)
                    else:
                        pt_m = 0
                else:
                    pt_h = 0
                    pt_m = preptime_jap2.replace(" Min","")
                    pt_m = int(pt_m)
                preptime = pt_m + (pt_h * 60)
            # prep time - pinchofyum
            elif preptime_3:
                preptime_poy = preptime_3.text
                # Extract all numbers
                preptime_poy2 = re.findall(r'\d+', preptime_poy)
                try:
                    preptime = int(preptime_poy2[0])
                except:
                    preptime = ''
            # prep time - food52
            elif preptime_4:
                try:
                    preptime = preptime_4.parent
                    preptime = preptime.text
                    preptime = preptime.replace('Prep time', '').replace('minutes', '').replace('minute', '').replace(' ', '').strip()
                    preptime = re.match(r'\d+', preptime)
                    preptime = preptime.group() if preptime else None
                    preptime = int(preptime)
                except:
                    preptime = ''
            # EXTRACT COOK TIME
            # cook time - wprm sites
            cooktime_m_1 = soup.find('span',class_='wprm-recipe-details wprm-recipe-details-minutes wprm-recipe-cook_time wprm-recipe-cook_time-minutes')
            cooktime_h_1 = soup.find('span',class_='wprm-recipe-details wprm-recipe-details-hours wprm-recipe-cook_time wprm-recipe-cook_time-hours')
            # cook time - justapinch
            cooktime_2 = soup.find('span', string='cook time')
            # cook time - pinchofyum
            cooktime_3 = soup.find('span', class_='tasty-recipes-cook-time')
            # cook time - food52
            cooktime_4 = soup.find('span',class_='recipe__details-heading', text='Cook time')
            # cook time - wprm sites
            if cooktime_m_1 or cooktime_h_1:
                if cooktime_m_1:
                    ct_m = cooktime_m_1.contents[0]
                    ct_m = int(ct_m)
                else:
                    ct_m = 0
                if cooktime_h_1:
                    ct_h = cooktime_h_1.contents[0]
                    ct_h = int(ct_h)
                else:
                    ct_h = 0
                cooktime = ct_m + (ct_h * 60)
            # cook time - justapinch
            if cooktime_2:
                cooktime_jap = cooktime_2.find_next_siblings('span')
                cooktime_jap2 = cooktime_jap[0].text
                if "Hr" in cooktime_jap2:
                    ct_h = cooktime_jap2[0]
                    ct_h = int(ct_h)
                    if "Min" in cooktime_jap2:
                        ct_mins = re.search('Hr (.*)Min', cooktime_jap2)
                        ct_m = ct_mins.group(1)
                        ct_m = int(ct_m)
                    else:
                        ct_m = 0
                else:
                    ct_h = 0
                    ct_m = cooktime_jap2.replace(" Min","")
                    ct_m = int(ct_m)
                cooktime = ct_m + (ct_h * 60)
            # cook time - pinchofyum
            if cooktime_3:
                cooktime_poy = cooktime_3.text
                # Extract all numbers
                cooktime_poy2 = re.findall(r'\d+', cooktime_poy)
                try:
                    cooktime = int(cooktime_poy2[0])
                except:
                    cooktime = ''
            # cook time - food52
            if cooktime_4:
                cooktime = cooktime_4.parent
                cooktime = cooktime.text
                cooktime = cooktime.replace('Cook time', '').replace('minutes', '').replace('minute', '').replace(' ', '').strip()
                cooktime = re.match(r'\d+', cooktime)
                cooktime = cooktime.group() if cooktime else None
                try:
                    cooktime = int(cooktime)
                except:
                    cooktime = ''
            # EXTRACT TOTAL TIME
            # total time - wprm sites
            totaltime_m_1 = soup.find('span',class_='wprm-recipe-details wprm-recipe-details-minutes wprm-recipe-total_time wprm-recipe-total_time-minutes')
            totaltime_h_1 = soup.find('span',class_='wprm-recipe-details wprm-recipe-details-hours wprm-recipe-total_time wprm-recipe-total_time-hours')
            # total time - wprm sites
            if totaltime_m_1 or totaltime_h_1:
                if totaltime_m_1:
                    tt_m = totaltime_m_1.contents[0]
                    tt_m = int(tt_m)
                else:
                    tt_m = 0
                if totaltime_h_1:
                    tt_h = totaltime_h_1.contents[0]
                    tt_h = int(tt_h)
                else:
                    tt_h = 0
                totaltime = tt_m + (tt_h * 60)
            # total time - all other sites
            else:
                if preptime and cooktime:
                    totaltime = preptime + cooktime
                elif preptime:
                    totaltime = preptime
                elif cooktime:
                    totaltime = cooktime
            # EXTRACT INGREDIENTS
            ingredients = []
            # ingredients - wprm sites
            ingredients_1 = soup.find('div',class_='wprm-recipe-ingredients-container')
            # ingredients - pinchofyum
            ingredients_2 = soup.find_all('li',attrs={'data-tr-ingredient-checkbox': True})
            # ingredients - justapinch
            ingredients_3 = soup.find('ul', {'id': 'recipe-ingredients-list'})
            # ingredients - tastyco
            ingredients_4 = soup.find('div',class_='ingredients__section')
            # ingredients - food52
            ingredients_5 = soup.find('div',class_='recipe__list--ingredients')
            # ingredients - tasteofhome
            ingredients_6 = soup.find('ul',class_='recipe-ingredients__list')
            # ingredients - taste.com.au
            ingredients_7 = soup.find('div',class_='recipe-ingredients-section')
            # ingredients - allrecipes
            ingredients_8 = soup.find('ul',class_='mntl-structured-ingredients__list')
            if ingredients_8 is None:
                ingredients_8 = soup.find('ul',class_='mm-recipes-structured-ingredients__list')
            # ingredients - foodnetwork
            ingredients_9 = soup.find_all('span',class_='o-Ingredients__a-Ingredient--CheckboxLabel')
            # ingredients - delish, thepioneerwoman
            ingredients_10 = soup.find('ul',class_='ingredient-lists')
            # ingredients - onceuponachef
            ingredients_11 = soup.find('div',class_='ingredients')
            # ingredients - wprm sites
            if ingredients_1:
                ingredients_wprm = ingredients_1.find_all('li',class_='wprm-recipe-ingredient')
                for ingredient in ingredients_wprm:
                    ingred = ingredient.text
                    ingred = ingred.replace("\n"," ")
                    ingred = ingred.replace("▢","")
                    ingred = ingred.strip()
                    ingredients.append(ingred)
            # ingredients - pinchofyum
            elif ingredients_2:
                for ingredient in ingredients_2:
                    ingred = ingredient.text
                    ingred = ingred.strip()
                    ingredients.append(ingred)
            # ingredients - justapinch
            elif ingredients_3:
                ingredients_justa = soup.find_all('li',class_='x-checkable')
                for ingredient in ingredients_justa:
                    ing_amount_1 = ingredient.find('div',class_='text-blue-ribbon text-wrap text-right font-weight-bold mr-2')
                    ing_amount = ing_amount_1.text
                    ing_amount = ing_amount.strip()
                    ing_item_1 = ingredient.find('div',class_='ml-1')
                    ing_item = ing_item_1.text
                    ingred = ing_amount + ' ' + ing_item
                    ingred = ingred.strip()
                    ingredients.append(ingred)
            # ingredients - tastyco
            elif ingredients_4:
                ingredients_tastyco = ingredients_4.find_all('li',class_='ingredient')
                for ingredient in ingredients_tastyco:
                    ingred = ingredient.text
                    ingred = ingred.strip()
                    ingredients.append(ingred)
            # ingredients - food52
            elif ingredients_5:
                ingredients_food52 = ingredients_5.find_all('li')
                for ingredient in ingredients_food52:
                    ingred = ingredient.text
                    ingred = ingred.replace('\n\n', ' ').replace('\n', ' ')
                    ingred = ingred.strip()
                    ingredients.append(ingred)
            # ingredients - tasteofhome
            elif ingredients_6:
                ingredients_toh = ingredients_6.find_all('li')
                for ingredient in ingredients_toh:
                    ingred = ingredient.text
                    ingred = ingred.strip()
                    ingredients.append(ingred)
            # ingredients - taste.com.au
            elif ingredients_7:
                ingredients_tcau = ingredients_7.find_all('div',class_='ingredient-description')
                for ingredient in ingredients_tcau:
                    ingred = ingredient.text
                    ingred = ingred.strip()
                    ingredients.append(ingred)
            # ingredients - allrecipes
            elif ingredients_8:
                ingredients_allrec = ingredients_8.find_all('li')
                for ingredient in ingredients_allrec:
                    try:
                        ingred_quantity = ingredient.find('span', {'data-ingredient-quantity': 'true'}).get_text(strip=True) if ingredient.find('span', {'data-ingredient-quantity': 'true'}) else ''
                        ingred_unit = ingredient.find('span', {'data-ingredient-unit': 'true'}).get_text(strip=True) if ingredient.find('span', {'data-ingredient-unit': 'true'}) else ''
                        ingred_name = ingredient.find('span', {'data-ingredient-name': 'true'}).get_text(strip=True) if ingredient.find('span', {'data-ingredient-name': 'true'}) else ''
                        ingredients.append(f"{ingred_quantity} {ingred_unit} {ingred_name}".strip())
                    except:
                        pass
            # ingredients - foodnetwork
            elif ingredients_9:
                for ingredient in ingredients_9:
                    ingred = ingredient.text
                    ingred = ingred.strip()
                    ingredients.append(ingred)
            # ingredients - delish, thepioneerwoman
            elif ingredients_10:
                ingredients_delish = ingredients_10.find_all('li')
                for ingredient in ingredients_delish:
                    ingred = ingredient.text
                    ingred = ingred.replace("\n"," ")
                    ingred = ingred.strip()
                    ingredients.append(ingred)
            # ingredients - onceuponachef
            elif ingredients_11:
                ingredients_ouac = ingredients_11.find_all('li',class_='ingredient')
                for ingredient in ingredients_ouac:
                    ingred = ingredient.text
                    ingred = ingred.replace("\n"," ")
                    ingred = ingred.strip()
                    ingredients.append(ingred)
            # EXTRACT INSTRUCTIONS
            instructions = []
            # instructions - wprm sites
            instructions_1 = soup.find('div',class_='wprm-recipe-instructions-container')
            # instructions - pinchofyum
            instructions_2 = soup.find('div',class_='tasty-recipes-instructions')
            # instructions - justapinch
            instructions_3 = soup.find('ul', {'id': 'recipe-preparation'})
            # instructions - tastyco
            instructions_4 = soup.find('ol',class_='prep-steps')
            # instructions - food52
            instructions_5 = soup.find('div',class_='recipe__list--steps')
            # instructions - tasteofhome
            instructions_6 = soup.find('ol',class_='recipe-directions__list')
            # instructions - taste.com.au
            instructions_7 = soup.find('ul',class_='recipe-method-steps')
            # instructions - allrecipes
            instructions_8 = soup.find('ol',class_='mntl-sc-block-group--OL')
            # instructions - foodnetwork
            instructions_9 = soup.find_all('li',class_='o-Method__m-Step')
            # instructions - delish, thepioneerwoman
            instructions_10 = soup.find('ol',class_='emevuu60')
            # instructions - onceuponachef
            instructions_11 = soup.find('div',class_='instructions')
            # instructions - wprm sites
            if instructions_1:
                instructions_wprm = instructions_1.find_all('div',class_='wprm-recipe-instruction-group')
                for group in instructions_wprm:
                    instructions_h4 = group.find('h4')
                    if instructions_h4:
                        instructions.append(instructions_h4.contents[0])
                    inst_steps = group.find_all('div',class_='wprm-recipe-instruction-text')
                    for step in inst_steps:
                        inst_step = step.text
                        instructions.append(inst_step)
            # instructions - pinchofyum
            elif instructions_2:
                instructions_pinch = instructions_2.find_all('li')
                for instruction in instructions_pinch:
                    instr = instruction.text
                    instr = instr.strip()
                    instructions.append(instr)
            # instructions - justapinch 
            elif instructions_3:
                instructions_justa = soup.find_all('div',class_='card-body p-0 py-1')
                for instruction in instructions_justa:
                    instr_1 = instruction.find('div',class_='flex-fill recipe-direction rcp-ugc-block')
                    instr = instr_1.text
                    instr = instr.strip()
                    instructions.append(instr)
            # instructions - tastyco
            elif instructions_4:
                instructions_tastyco = instructions_4.find_all('li')
                for instruction in instructions_tastyco:
                    instr = instruction.text
                    instr = instr.strip()
                    instructions.append(instr)
            # instructions - food52
            elif instructions_5:
                instructions_food52 = instructions_5.find_all('li',class_='recipe__list-step')
                for instruction in instructions_food52:
                    instr = instruction.text
                    instr = instr.strip()
                    instructions.append(instr)
            # instructions - tasteofhome
            elif instructions_6:
                instructions_toh = instructions_6.find_all('li')
                for instruction in instructions_toh:
                    instr = instruction.text
                    instr = instr.strip()
                    instructions.append(instr)
            # instructions - taste.com.au
            elif instructions_7:
                instructions_tcau = instructions_7.find_all('div',class_='recipe-method-step-content')
                for instruction in instructions_tcau:
                    instr = instruction.text
                    instr = instr.strip()
                    instructions.append(instr)
            # instructions - allrecipes
            elif instructions_8:
                instructions_allrec = instructions_8.find_all('li')
                for instruction in instructions_allrec:
                    instr = instruction.text
                    instr = instr.strip()
                    instructions.append(instr)
            # instructions - foodnetwork
            elif instructions_9:
                for instruction in instructions_9:
                    instr = instruction.text
                    instr = instr.strip()
                    instructions.append(instr)
            # instructions - delish, thepioneerwoman
            elif instructions_10:
                instructions_delish = instructions_10.find_all('li')
                for instruction in instructions_delish:
                    try:
                        for span in instruction.find_all('span', class_=['e1241r8m1', 'e1241r8m0']):
                            span.decompose()
                        instr = instruction.get_text(strip=True)
                        instr = instr.strip()
                        instructions.append(instr)
                    except:
                        pass
            # instructions - onceuponachef
            elif instructions_11:
                instructions_ouac = instructions_11.find_all('li',class_='instruction')
                for instruction in instructions_ouac:
                    instr = instruction.text
                    instr = instr.strip()
                    instructions.append(instr)
            # PREPARE EXTRACTED DATA
            i_description = description[:500]
            i_ingredients = ''
            for i in ingredients:
                i_ingredients = i_ingredients + i + '\n'
            i_ingredients = i_ingredients.strip()
            i_ingredients = i_ingredients[:6600]
            i_instructions = ''
            for i in instructions:
                i_instructions = i_instructions + i + '\n'
            i_instructions = i_instructions.strip()
            i_instructions = i_instructions[:2200]
            # POPULATE FORM FIELDS
            if title:
                form.recipe_name.data = title
            if i_description:
                form.description.data = i_description
            if servings:
                form.servings.data = servings
            if preptime:
                form.prep_time.data = preptime
            if cooktime:
                form.cook_time.data = cooktime
            if totaltime:
                form.total_time.data = totaltime
            if i_ingredients:
                form.ingredients.data = i_ingredients
            if i_instructions:
                form.instructions.data = i_instructions
            if title or i_description or servings or i_ingredients or i_instructions:
                form.url.data = autofill_url
            if title and i_ingredients and i_instructions:
                flash(_('The form was autofilled successfully.'))
            elif title or i_description or servings or i_ingredients or i_instructions:
                flash(_('Some fields have been autofilled, please manually complete the remaining.'))
            else:
                flash(_('Error: could not autofill from the given URL.'))
    # Save recipe to My Recipes
    if form.submit.data and form.validate_on_submit():
        hex_valid = 0
        while hex_valid == 0:
            hex_string = secrets.token_hex(4)
            hex_exist = Recipe.query.filter_by(hex_id=hex_string).first()
            if hex_exist is None:
                hex_valid = 1
        defaults = ['default01.png', 'default02.png', 'default03.png', 'default04.png', 'default05.png', 'default06.png', 'default07.png',
            'default08.png', 'default09.png', 'default10.png', 'default11.png', 'default12.png', 'default13.png', 'default14.png',
            'default15.png', 'default16.png', 'default17.png', 'default18.png', 'default19.png', 'default20.png', 'default21.png',
            'default22.png', 'default23.png', 'default24.png', 'default25.png', 'default26.png', 'default27.png']
        rand_default = random.choice(defaults)
        image = request.files['image']
        if request.files and image.filename != '':
            filename, file_extension = os.path.splitext(image.filename)
            # Convert the file extension to lowercase to handle case variations like ".JPG"
            file_extension = file_extension.lower()
            # Validate image
            val_ext = validate_image(image.stream)
            if file_extension not in app.config['UPLOAD_EXTENSIONS']:
                return "Invalid image: must be a .png, .jpg, .jpeg, .gif, or .webp file", 400
            if not val_ext:
                return "Image validation failed: image is corrupt or format could not be identified", 400
            if val_ext not in app.config['UPLOAD_EXTENSIONS']:
                return "Image validation failed: must be JPG, PNG, GIF, or WEBP format", 400
            hex_valid2 = 0
            while hex_valid2 == 0:
                hex_string2 = secrets.token_hex(8)
                hex_exist2 = Recipe.query.filter(Recipe.photo.contains(hex_string2)).first()
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], hex_string2 + file_extension)
                if hex_exist2 is None and not os.path.exists(file_path):
                    hex_valid2 = 1
            new_file = hex_string2 + file_extension
            # Rewind then save
            image.stream.seek(0)
            image.save(os.path.join(app.config['UPLOAD_FOLDER'], new_file))
            img = Image.open(app.config['UPLOAD_FOLDER'] + '/' + new_file)
            img_width, img_height = img.size
            # Resize image if larger than 1500px
            if img_width > img_height:
                if img_width > 1500:
                    basewidth = 1500
                    wpercent = (basewidth/float(img.size[0]))
                    hsize = int((float(img.size[1])*float(wpercent)))
                    img = img.resize((basewidth,hsize), Image.Resampling.LANCZOS)
            else:
                if img_height > 1500:
                    baseheight = 1500
                    hpercent = (baseheight/float(img.size[1]))
                    wsize = int((float(img.size[0])*float(hpercent)))
                    img = img.resize((wsize,baseheight), Image.Resampling.LANCZOS)
            # Fix the orientation of image before saving to avoid unexpectedly rotated images
            if hasattr(img, '_getexif'):
                orientation = 0x0112
                exifdata = img._getexif()
                if exifdata is not None and orientation in exifdata:
                    orientation = exifdata[orientation]
                    rotations = {
                        3: Image.ROTATE_180,
                        6: Image.ROTATE_270,
                        8: Image.ROTATE_90
                    }
                    if orientation in rotations:
                        img = img.transpose(rotations[orientation])
            # Save image to recipe-photos directory
            img.save(app.config['UPLOAD_FOLDER'] + '/' + new_file)
            recipe = Recipe(hex_id=hex_string, title=form.recipe_name.data, category=form.category.data, photo=new_file,
                description=form.description.data, url=form.url.data, servings=form.servings.data, prep_time=form.prep_time.data, cook_time=form.cook_time.data,
                total_time=form.total_time.data, ingredients=form.ingredients.data, instructions=form.instructions.data, favorite=0, public=0, user_id=current_user.id)
        else:
            recipe = Recipe(hex_id=hex_string, title=form.recipe_name.data, category=form.category.data, photo=rand_default,
                description=form.description.data, url=form.url.data, servings=form.servings.data, prep_time=form.prep_time.data, cook_time=form.cook_time.data,
                total_time=form.total_time.data, ingredients=form.ingredients.data, instructions=form.instructions.data, favorite=0, public=0, user_id=current_user.id)
        # Add recipe to database
        db.session.add(recipe)
        db.session.commit()
        # Get value of Nutrition Checkbox
        if 'n_checkbox' in request.form:
            n_checkbox_value = request.form['n_checkbox']
        else:
            n_checkbox_value = 'off'
        # Check whether there is Nutritional Info
        n_info = False
        if request.form['n_calories'] or request.form['n_carbs'] or request.form['n_protein'] or request.form['n_fat']:
            n_info = True
        if request.form['n_sugar'] or request.form['n_cholesterol'] or request.form['n_sodium'] or request.form['n_fiber']:
            n_info = True
        # If checkbox is checked and Nutritional Info provided create NutritionalInfo record in databse
        if n_checkbox_value == 'on' and n_info == True:
            curr_recipe = Recipe.query.filter_by(hex_id=hex_string).first()
            nutrition = NutritionalInfo(recipe_id=curr_recipe.id, user_id=current_user.id, calories=form.n_calories.data, carbs=form.n_carbs.data,
                protein=form.n_protein.data, fat=form.n_fat.data, sugar=form.n_sugar.data, cholesterol=form.n_cholesterol.data, 
                sodium=form.n_sodium.data, fiber=form.n_fiber.data)
            db.session.add(nutrition)
            db.session.commit()
        flash(_('The recipe has been added.'))
        return redirect(url_for('myrecipes.addRecipe'))
    return render_template('add-recipe.html', title=_('Add a New Recipe'),
        mdescription=_('Use the provided form to add a new recipe to your account.'), form=form, form2=form2, choices=choices)

@bp.route('/edit-recipe/<hexid>', methods=['GET', 'POST'])
@login_required
@limiter.limit(Config.DEFAULT_RATE_LIMIT)
def editRecipe(hexid):
    # Query the requested recipe as well as its nutritional info
    recipe = Recipe.query.filter_by(hex_id=hexid).first()
    nutrition = NutritionalInfo.query.filter_by(recipe_id=recipe.id).first()
    form = EditRecipeForm()
    choices = []
    user = User.query.filter_by(email=current_user.email).first_or_404()
    cats = user.categories.order_by(Category.label).all()
    for cat in cats:
        curr_cat = cat.label
        choices.append(curr_cat)
    form.category.choices = choices
    if recipe.user_id != current_user.id:
        flash('Error: ' + _('recipe does not exist or you do not have permission to edit it.'))
    if form.validate_on_submit():
        recipe.title = form.recipe_name.data
        recipe.category = form.category.data
        recipe.description = form.description.data
        recipe.url = form.url.data
        recipe.servings = form.servings.data
        recipe.prep_time = form.prep_time.data
        recipe.cook_time = form.cook_time.data
        recipe.total_time = form.total_time.data
        recipe.ingredients = form.ingredients.data
        recipe.instructions = form.instructions.data
        recipe.time_edited = datetime.utcnow()
        image = request.files['image']
        if request.files and image.filename != '':
            old_path = app.config['UPLOAD_FOLDER'] + '/' + recipe.photo
            defaults = ['default01.png', 'default02.png', 'default03.png', 'default04.png', 'default05.png', 'default06.png', 'default07.png',
                'default08.png', 'default09.png', 'default10.png', 'default11.png', 'default12.png', 'default13.png', 'default14.png',
                'default15.png', 'default16.png', 'default17.png', 'default18.png', 'default19.png', 'default20.png', 'default21.png',
                'default22.png', 'default23.png', 'default24.png', 'default25.png', 'default26.png', 'default27.png', 'demo1.jpg', 'demo2.jpg',
                'demo3.jpg', 'demo4.jpg', 'demo5.jpg', 'demo6.jpg', 'demo7.jpg', 'demo8.jpg', 'demo9.jpg', 'demo10.jpg', 'demo11.jpg',
                'demo12.jpg']
            filename, file_extension = os.path.splitext(image.filename)
            # Convert the file extension to lowercase to handle case variations like ".JPG"
            file_extension = file_extension.lower()
            # Validate image
            val_ext = validate_image(image.stream)
            if file_extension not in app.config['UPLOAD_EXTENSIONS']:
                return "Invalid image: must be a .png, .jpg, .jpeg, .gif, or .webp file", 400
            if not val_ext:
                return "Image validation failed: image is corrupt or format could not be identified", 400
            if val_ext not in app.config['UPLOAD_EXTENSIONS']:
                return "Image validation failed: must be JPG, PNG, GIF, or WEBP format", 400
            hex_valid = 0
            while hex_valid == 0:
                hex_string = secrets.token_hex(8)
                hex_exist = Recipe.query.filter(Recipe.photo.contains(hex_string)).first()
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], hex_string + file_extension)
                if hex_exist is None and not os.path.exists(file_path):
                    hex_valid = 1
            new_file = hex_string + file_extension
            # Rewind then save
            image.stream.seek(0)
            image.save(os.path.join(app.config['UPLOAD_FOLDER'], new_file))
            img = Image.open(app.config['UPLOAD_FOLDER'] + '/' + new_file)
            img_width, img_height = img.size
            # Resize image if larger than 1500px
            if img_width > img_height:
                if img_width > 1500:
                    basewidth = 1500
                    wpercent = (basewidth/float(img.size[0]))
                    hsize = int((float(img.size[1])*float(wpercent)))
                    img = img.resize((basewidth,hsize), Image.Resampling.LANCZOS)
            else:
                if img_height > 1500:
                    baseheight = 1500
                    hpercent = (baseheight/float(img.size[1]))
                    wsize = int((float(img.size[0])*float(hpercent)))
                    img = img.resize((wsize,baseheight), Image.Resampling.LANCZOS)
            # Fix the orientation of image before saving to avoid unexpectedly rotated images
            if hasattr(img, '_getexif'):
                orientation = 0x0112
                exifdata = img._getexif()
                if exifdata is not None and orientation in exifdata:
                    orientation = exifdata[orientation]
                    rotations = {
                        3: Image.ROTATE_180,
                        6: Image.ROTATE_270,
                        8: Image.ROTATE_90
                    }
                    if orientation in rotations:
                        img = img.transpose(rotations[orientation])
            # Save image to recipe-photos directory
            img.save(app.config['UPLOAD_FOLDER'] + '/' + new_file)
            if recipe.photo not in defaults:
                os.remove(old_path)
            recipe.photo = new_file
        # Get value of Nutrition Checkbox
        if 'n_checkbox' in request.form:
            n_checkbox_value = request.form['n_checkbox']
        else:
            n_checkbox_value = 'off'
        # Check whether there is Nutritional Info
        n_info = False
        if request.form['n_calories'] or request.form['n_carbs'] or request.form['n_protein'] or request.form['n_fat']:
            n_info = True
        if request.form['n_sugar'] or request.form['n_cholesterol'] or request.form['n_sodium'] or request.form['n_fiber']:
            n_info = True
        # Update NutritionalInfo record if it exists and there is Nutrition info in submitted form
        if n_checkbox_value == 'on' and n_info == True and nutrition is not None:
            nutrition.calories = form.n_calories.data
            nutrition.carbs = form.n_carbs.data
            nutrition.protein = form.n_protein.data
            nutrition.fat = form.n_fat.data
            nutrition.sugar = form.n_sugar.data
            nutrition.cholesterol = form.n_cholesterol.data
            nutrition.sodium = form.n_sodium.data
            nutrition.fiber = form.n_fiber.data
        # Add NutritionalInfo record if it doesn't exist and there is Nutrition info in submitted form
        elif n_checkbox_value == 'on' and n_info == True and nutrition is None:
            new_nutrition = NutritionalInfo(recipe_id=recipe.id, user_id=current_user.id, calories=form.n_calories.data, carbs=form.n_carbs.data,
                protein=form.n_protein.data, fat=form.n_fat.data, sugar=form.n_sugar.data, cholesterol=form.n_cholesterol.data, 
                sodium=form.n_sodium.data, fiber=form.n_fiber.data)
            db.session.add(new_nutrition)
        # Remove NutritionalInfo record if it exists but there is NO Nutrition info in submitted form
        elif nutrition is not None:
            db.session.delete(nutrition)
        # Do nothing if NutritionalInfo record doesn't exist and there is NO Nutrition info in submitted form
        else:
            pass
        # Process database changes
        db.session.commit()
        flash(_('The recipe has been updated.'))
        return redirect(url_for('myrecipes.recipeDetail', hexid=hexid))
    return render_template('edit-recipe.html', title=_('Edit Recipe'),
        mdescription=_('Use the provided form to edit details for the requested recipe.'), form=form, recipe=recipe,
        nutrition=nutrition, choices=choices)

@bp.route('/my-recipes/search', methods=['GET', 'POST'])
@login_required
@limiter.limit(Config.DEFAULT_RATE_LIMIT)
def advancedSearch():
    user = User.query.filter_by(email=current_user.email).first_or_404()
    # the query, example is search?query=garlic+shrimp which translates to "garlic shrimp"
    # this defaults to empty string if not provided
    query_string = request.args.get('query', '')
    page = request.args.get('page', 1, type=int)
    # per_page variable is used for paginating the recipes object
    per_page = app.config['MAIN_RECIPES_PER_PAGE']
    # Base query (all recipes belonging to the user)
    recipes_query = db.session.query(
        Recipe.id,
        Recipe.title,
        Recipe.category,
        Recipe.hex_id,
        Recipe.photo,
        Recipe.prep_time,
        Recipe.cook_time,
        Recipe.total_time,
        Recipe.time_created,
        Recipe.ingredients,
        Recipe.instructions
    ).filter(Recipe.user_id == user.id).order_by(func.lower(Recipe.title))
    # If a query string is provided, split it into terms and build search filters
    if query_string and query_string.strip():
        query_terms = query_string.split()
        search_conditions = []
        # Check each search option from GET parameters; default to 'y' (selected)
        if request.args.get('o_title', 'y') == 'y':
            search_conditions.append(
                and_(*[func.lower(Recipe.title).contains(term.lower()) for term in query_terms])
            )
        if request.args.get('o_category', 'y') == 'y':
            search_conditions.append(
                and_(*[func.lower(Recipe.category).contains(term.lower()) for term in query_terms])
            )
        if request.args.get('o_ingredients', 'y') == 'y':
            search_conditions.append(
                and_(*[func.lower(Recipe.ingredients).contains(term.lower()) for term in query_terms])
            )
        if request.args.get('o_instructions', 'y') == 'y':
            search_conditions.append(
                and_(*[func.lower(Recipe.instructions).contains(term.lower()) for term in query_terms])
            )
        # If at least one option is enabled, filter the query
        if search_conditions:
            recipes_query = recipes_query.filter(or_(*search_conditions))
    else:
        # No valid search term provided, query will return no recipes
        recipes_query = recipes_query.filter(false())
    # Paginate the queried recipes
    recipes = recipes_query.paginate(page=page, per_page=per_page, error_out=False)
    # Build recipe_info array using external function
    recipe_info = get_recipe_info(recipes)
    # Paginate the recipe_info array in the same way that recipes is paginated
    start_index = (page - 1) * per_page
    end_index = start_index + per_page
    recipe_info_paginated = recipe_info[start_index:end_index]
    next_url = url_for('myrecipes.advancedSearch', page=recipes.next_num) \
        if recipes.has_next else None
    prev_url = url_for('myrecipes.advancedSearch', page=recipes.prev_num) \
        if recipes.has_prev else None
    form = AdvancedSearchForm()
    if query_string:
        form.search.data = query_string
    if form.validate_on_submit():
        # When the form is submitted, capture the state of each checkbox.
        args = {'query': form.search.data}
        # Include each checkbox parameter if it was checked.
        if request.form.get('o_title'):
            args['o_title'] = request.form.get('o_title')
        if request.form.get('o_category'):
            args['o_category'] = request.form.get('o_category')
        if request.form.get('o_ingredients'):
            args['o_ingredients'] = request.form.get('o_ingredients')
        if request.form.get('o_instructions'):
            args['o_instructions'] = request.form.get('o_instructions')
        # Redirect to the GET route with the search query and checkbox states.
        return redirect(url_for('myrecipes.advancedSearch', **args))
    return render_template('advanced-search.html', title=_('Advanced Search'),
        mdescription=_('Search your recipes by title, category, ingredients, and instructions.'), user=user, query_string=query_string,
        recipes=recipes.items, form=form, next_url=next_url, prev_url=prev_url, recipe_info_paginated=recipe_info_paginated)