from flask import render_template, flash, redirect, url_for, request, send_from_directory, jsonify, make_response
from app import app, db, limiter
from app.myrecipes.forms import AddCategoryForm, AddRecipeForm, EditRecipeForm, AddToListForm, AddToMealPlannerForm, DisplaySettingsForm, EmptyForm
from flask_login import current_user, login_user, logout_user, login_required
from flask_paginate import Pagination
from app.models import User, Recipe, Category, Shoplist, Listitem, MealRecipe, NutritionalInfo
from werkzeug.urls import url_parse
from datetime import datetime
from PIL import Image
from urllib.parse import urlparse
from urllib.request import urlopen, Request
from bs4 import BeautifulSoup
import secrets, time, random, os, imghdr, requests, re, urllib.request
from app.myrecipes import bp
from config import Config

@bp.context_processor
def inject_dynrootmargin():
    dynrootmargin = app.config['DYNAMIC_ROOT_MARGIN']
    return dict(dynrootmargin=dynrootmargin)

def validate_image(stream):
    header = stream.read(512)
    stream.seek(0)
    format = imghdr.what(None, header)
    if not format:
        return None
    return '.' + format

@bp.route('/recipe-photos/<path:filename>')
@limiter.limit(Config.DEFAULT_RATE_LIMIT)
def recipePhotos(filename):
    return send_from_directory(app.root_path + '/appdata/recipe-photos/', filename)

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
        ).outerjoin(NutritionalInfo, Recipe.id == NutritionalInfo.recipe_id).filter(Recipe.user_id == user.id).order_by(Recipe.title)
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
    # Populate month array with the next 30 days of month, used for checking scheduled and last prepared
    month = []
    curr_dt = datetime.now()
    timestamp = int(time.mktime(curr_dt.timetuple()))
    for d in month:
        date = datetime.fromtimestamp(timestamp)
        compactdate = date.strftime("%Y-%m-%d")
        month.append(compactdate)
        timestamp += 86400
    # Create recipe_info array that is parallel to recipes object, contains nearest scheduled date and last prepared
    recipe_info = []
    for recipe in recipes:
        # Query all meal plans for the 
        meal_plans = MealRecipe.query.filter_by(recipe_id=recipe.id).all()
        # Find the nearest date
        nearest_date = None
        min_diff = float('inf')
        for plan in meal_plans:
            plan_date = datetime.strptime(plan.date, "%Y-%m-%d")
            for month_date in month:
                diff = abs((plan_date - month_date).days)
                if diff < min_diff:
                    min_diff = diff
                    nearest_date = plan_date
        # If a nearest date is found, query for that specific date
        if nearest_date:
            scheduled_rec = MealRecipe.query.filter_by(recipe_id=recipe.id, date=nearest_date.strftime("%Y-%m-%d")).first()
            scheduled = scheduled_rec.date
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
    return render_template('all-recipes.html', title='All Recipes', user=user, recipes=recipes.items,
        form=form, next_url=next_url, prev_url=prev_url, recipe_info=recipe_info)

@bp.route('/api/my-recipes/all')
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
    if user.pref_sort == 0:
        recipes = user.recipes.filter_by(favorite=1).order_by(Recipe.title).paginate(page=page,
            per_page=app.config['MAIN_RECIPES_PER_PAGE'], error_out=False)
    elif user.pref_sort == 1:
        recipes = user.recipes.filter_by(favorite=1).order_by(Recipe.time_created).paginate(page=page,
            per_page=app.config['MAIN_RECIPES_PER_PAGE'], error_out=False)
    else:
        recipes = user.recipes.filter_by(favorite=1).order_by(Recipe.time_created.desc()).paginate(page=page,
            per_page=app.config['MAIN_RECIPES_PER_PAGE'], error_out=False)
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
    return render_template('favorites.html', title='Favorites', user=user, recipes=recipes.items,
        form=form, next_url=next_url, prev_url=prev_url)

@bp.route('/recipe/<hexid>/favorite')
@login_required
@limiter.limit(Config.DEFAULT_RATE_LIMIT)
def favorite(hexid):
    recipe = Recipe.query.filter_by(hex_id=hexid).first()
    if recipe is None or recipe.user_id != current_user.id:
        flash('Error: recipe does not exist or you do not have permission to modify it.')
        return redirect(url_for('myrecipes.allRecipes'))
    recipe.favorite = 1
    db.session.commit()
    flash('This recipe has been added to your Favorites.')
    return redirect(url_for('myrecipes.recipeDetail', hexid=hexid))

@bp.route('/recipe/<hexid>/unfavorite')
@login_required
@limiter.limit(Config.DEFAULT_RATE_LIMIT)
def unfavorite(hexid):
    recipe = Recipe.query.filter_by(hex_id=hexid).first()
    if recipe is None or recipe.user_id != current_user.id:
        flash('Error: recipe does not exist or you do not have permission to modify it.')
        return redirect(url_for('myrecipes.allRecipes'))
    recipe.favorite = 0
    db.session.commit()
    flash('This recipe has been removed from your Favorites.')
    return redirect(url_for('myrecipes.recipeDetail', hexid=hexid))

@bp.route('/recipe/<hexid>/make-public')
@login_required
@limiter.limit(Config.DEFAULT_RATE_LIMIT)
def makePublic(hexid):
    recipe = Recipe.query.filter_by(hex_id=hexid).first()
    if recipe is None or recipe.user_id != current_user.id:
        flash('Error: recipe does not exist or you do not have permission to modify it.')
        return redirect(url_for('myrecipes.allRecipes'))
    recipe.public = 1
    db.session.commit()
    flash('You can now share the URL for this recipe.')
    return redirect(url_for('myrecipes.recipeDetail', hexid=hexid))

@bp.route('/recipe/<hexid>/make-private')
@login_required
@limiter.limit(Config.DEFAULT_RATE_LIMIT)
def makePrivate(hexid):
    recipe = Recipe.query.filter_by(hex_id=hexid).first()
    if recipe is None or recipe.user_id != current_user.id:
        flash('Error: recipe does not exist or you do not have permission to modify it.')
        return redirect(url_for('myrecipes.allRecipes'))
    recipe.public = 0
    db.session.commit()
    flash('The recipe URL can no longer be shared.')
    return redirect(url_for('myrecipes.recipeDetail', hexid=hexid))

@bp.route('/recipe/<hexid>', methods=['GET', 'POST'])
@limiter.limit(Config.DEFAULT_RATE_LIMIT)
def recipeDetail(hexid):
    recipe = Recipe.query.filter_by(hex_id=hexid).first()
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
        creationtime = recipe.time_created.strftime('%m/%d/%Y')
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
            message = str(count) + " items have been added to " + str(list.label) + " shopping list."
            flash(message)
        else:
            flash('Error: all ingredients from this recipe are already on your shopping list.')
    # If user selects hidden "Choose here" for AddToListForm
    if form.errors and not form2.validate_on_submit():
        flash('Error: please select a shopping list.')
    # AddToMealPlannerForm
    if form2.validate_on_submit():
        # Get value from select field which has name attribute of selectdate
        # This is needed since select field is written manually instead of using {{ form2.selectdate }} in template
        selectdate = request.form.get('selectdate')
        # Prevent form processing if hidden "Choose here" is selected
        if selectdate == '':
            flash('Error: please select a date.')
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
                    flash('This recipe has been added to your meal plan.')
                else:
                    flash('Error: the selected date in invalid.')
            else:
                flash('Error: this recipe is already scheduled for the selected date.')
    return render_template('recipe-detail.html', title=recipe_title, recipe=recipe, choices=choices, owner=owner, 
        ingredients=ingredients, instructions=instructions, form=form, form2=form2, month=month, 
        nutrition=nutrition, creationtime=creationtime, meal_count=meal_count, last_prepared=last_prepared) 

@bp.route('/my-recipes/categories', methods=['GET', 'POST'])
@login_required
@limiter.limit(Config.DEFAULT_RATE_LIMIT)
def categories():
    user = User.query.filter_by(email=current_user.email).first_or_404()
    categories = user.categories.order_by(Category.label).all()
    query_string = request.args.get('c')
    page = request.args.get('page', 1, type=int)
    if query_string is None:
        rec_count = user.recipes.filter_by(category='Miscellaneous').all()
        if user.pref_sort == 0:
            recipes = user.recipes.filter_by(category='Miscellaneous').order_by(Recipe.title).paginate(page=page,
                per_page=app.config['CAT_RECIPES_PER_PAGE'], error_out=False)
        elif user.pref_sort == 1:
            recipes = user.recipes.filter_by(category='Miscellaneous').order_by(Recipe.time_created).paginate(page=page,
                per_page=app.config['CAT_RECIPES_PER_PAGE'], error_out=False)
        else:
            recipes = user.recipes.filter_by(category='Miscellaneous').order_by(Recipe.time_created.desc()).paginate(page=page,
                per_page=app.config['CAT_RECIPES_PER_PAGE'], error_out=False)
    else:
        rec_count = user.recipes.filter_by(category=query_string).all()
        if user.pref_sort == 0:
            recipes = user.recipes.filter_by(category=query_string).order_by(Recipe.title).paginate(page=page,
                per_page=app.config['CAT_RECIPES_PER_PAGE'], error_out=False)
        elif user.pref_sort == 1:
            recipes = user.recipes.filter_by(category=query_string).order_by(Recipe.time_created).paginate(page=page,
                per_page=app.config['CAT_RECIPES_PER_PAGE'], error_out=False)
        else:
            recipes = user.recipes.filter_by(category=query_string).order_by(Recipe.time_created.desc()).paginate(page=page,
                per_page=app.config['CAT_RECIPES_PER_PAGE'], error_out=False)
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
            flash('Error: the category you entered already exists.')
        elif len(cats) > 39:
            flash('Error: you are limited to 40 categories.')
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
            flash('The category has been added.')
        return redirect(url_for('myrecipes.categories'))
    return render_template('categories.html', title='Categories', user=user, categories=categories, query_string=query_string,
        recipes=recipes.items, recipe_count=recipe_count, form=form, form2=form2, cats=cats, next_url=next_url, prev_url=prev_url)

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
    if user.pref_sort == 0:
        recipes = user.recipes.filter_by(category=catname).order_by(Recipe.title).paginate(page=page,
            per_page=app.config['CAT_RECIPES_PER_PAGE'], error_out=False)
    elif user.pref_sort == 1:
        recipes = user.recipes.filter_by(category=catname).order_by(Recipe.time_created).paginate(page=page,
            per_page=app.config['CAT_RECIPES_PER_PAGE'], error_out=False)
    else:
        recipes = user.recipes.filter_by(category=catname).order_by(Recipe.time_created.desc()).paginate(page=page,
            per_page=app.config['CAT_RECIPES_PER_PAGE'], error_out=False)
    next_url = url_for('myrecipes.mobileCategory', catname=catname, page=recipes.next_num) \
        if recipes.has_next else None
    prev_url = url_for('myrecipes.mobileCategory', catname=catname, page=recipes.prev_num) \
        if recipes.has_prev else None
    recipe_count = len(rec_count)
    return render_template('mobile-category.html', title=catname, user=user, recipes=recipes.items,
        recipe_count=recipe_count, catname=catname, next_url=next_url, prev_url=prev_url, invalidcat=invalidcat)

@bp.route('/remove-category/<catid>')
@login_required
@limiter.limit(Config.DEFAULT_RATE_LIMIT)
def removeCategory(catid):
    category = Category.query.filter_by(hex_id=catid).first()
    user = User.query.filter_by(email=current_user.email).first()
    recipes = user.recipes.all()
    if category is None or category.user_id != current_user.id:
        flash('Error: category does not exist or you do not have permission to remove it.')
    elif category.label == 'Miscellaneous':
        flash('Error: Miscellaneous cannot be deleted because it is the default category.')
    else:
        if category.user_id == current_user.id:
            for recipe in recipes:
                if recipe.category == category.label:
                    recipe.category = 'Miscellaneous'
            db.session.delete(category)
            db.session.commit()
            flash('Category has been removed.')
        else:
            flash('Error: category does not exist.')
    return redirect(url_for('myrecipes.categories'))

@bp.route('/remove-recipe/<hexid>')
@login_required
@limiter.limit(Config.DEFAULT_RATE_LIMIT)
def removeRecipe(hexid):
    # Query the recipe by hexid
    delrecipe = Recipe.query.filter_by(hex_id=hexid).first()
    if delrecipe is None or delrecipe.user_id != current_user.id:
        flash('Error: recipe does not exist or you do not have permission to delete it.')
        return redirect(url_for('myrecipes.allRecipes'))
    defaults = ['default01.png', 'default02.png', 'default03.png', 'default04.png', 'default05.png', 'default06.png', 'default07.png',
        'default08.png', 'default09.png', 'default10.png', 'default11.png', 'default12.png', 'default13.png', 'default14.png',
        'default15.png', 'default16.png', 'default17.png', 'default18.png', 'default19.png', 'default20.png', 'default21.png',
        'default22.png', 'default23.png', 'default24.png', 'default25.png', 'default26.png', 'default27.png']
    fullpath = app.config['UPLOAD_FOLDER'] + '/' + delrecipe.photo
    if delrecipe.photo not in defaults:
        try:
            os.remove(fullpath)
        except:
            pass
    # Query NutritionalInfo by id of recipe that is requested for deletion
    delnutrition = NutritionalInfo.query.filter_by(recipe_id=delrecipe.id).first()
    db.session.delete(delrecipe)
    # Delete NutritionalInfo if it exists for the selected recipe
    if delnutrition is not None:
        db.session.delete(delnutrition)
    db.session.commit()
    flash('Recipe has been removed.')
    return redirect(url_for('myrecipes.allRecipes'))

@bp.route('/add-recipe', methods=['GET', 'POST'])
@login_required
@limiter.limit(Config.DEFAULT_RATE_LIMIT)
def addRecipe():
    form = AddRecipeForm()
    choices = []
    user = User.query.filter_by(email=current_user.email).first_or_404()
    cats = user.categories.all()
    for cat in cats:
        curr_cat = cat.label
        choices.append(curr_cat)
    form.category.choices = choices
    if form.validate_on_submit():
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
            hex_valid2 = 0
            while hex_valid2 == 0:
                hex_string2 = secrets.token_hex(8)
                hex_exist2 = Recipe.query.filter(Recipe.photo.contains(hex_string2)).first()
                if hex_exist2 is None:
                    hex_valid2 = 1
            new_file = hex_string2 + file_extension
            val_ext = validate_image(image.stream)
            val_exts = []
            if val_ext == '.jpg':
                val_exts.append(val_ext)
                val_exts.append('.jpeg')
            elif val_ext == '.jpeg':
                val_exts.append(val_ext)
                val_exts.append('.jpg')
            else:
                val_exts.append(val_ext)
            if file_extension not in app.config['UPLOAD_EXTENSIONS'] or file_extension not in val_exts:
                return "Invalid image", 400
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
        flash('The recipe has been added.')
        return redirect(url_for('myrecipes.addRecipe'))
    return render_template('add-recipe.html', title='Add a New Recipe', form=form, choices=choices)

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
        flash('Error: recipe doesn’t exist or you don’t have permission to edit it.')
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
        image = request.files['image']
        if request.files and image.filename != '':
            old_path = app.config['UPLOAD_FOLDER'] + '/' + recipe.photo
            defaults = ['default01.png', 'default02.png', 'default03.png', 'default04.png', 'default05.png', 'default06.png', 'default07.png',
                'default08.png', 'default09.png', 'default10.png', 'default11.png', 'default12.png', 'default13.png', 'default14.png',
                'default15.png', 'default16.png', 'default17.png', 'default18.png', 'default19.png', 'default20.png', 'default21.png',
                'default22.png', 'default23.png', 'default24.png', 'default25.png', 'default26.png', 'default27.png']
            filename, file_extension = os.path.splitext(image.filename)
            hex_valid = 0
            while hex_valid == 0:
                hex_string = secrets.token_hex(8)
                hex_exist = Recipe.query.filter(Recipe.photo.contains(hex_string)).first()
                if hex_exist is None:
                    hex_valid = 1
            new_file = hex_string + file_extension
            val_ext = validate_image(image.stream)
            val_exts = []
            if val_ext == '.jpg':
                val_exts.append(val_ext)
                val_exts.append('.jpeg')
            elif val_ext == '.jpeg':
                val_exts.append(val_ext)
                val_exts.append('.jpg')
            else:
                val_exts.append(val_ext)
            if file_extension not in app.config['UPLOAD_EXTENSIONS'] or file_extension not in val_exts:
                return "Invalid image", 400
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
        flash('The recipe has been updated.')
        return redirect(url_for('myrecipes.recipeDetail', hexid=hexid))
    return render_template('edit-recipe.html', title='Edit Recipe', form=form, recipe=recipe, nutrition=nutrition, choices=choices)
