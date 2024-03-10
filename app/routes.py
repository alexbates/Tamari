from flask import render_template, flash, redirect, url_for, request, send_from_directory, jsonify, make_response
from app import app, db
from app.forms import LoginForm, RegistrationForm, DisplaySettingsForm, AccountForm, EmptyForm, ResetPasswordRequestForm, ResetPasswordForm
from app.forms import AddCategoryForm, AddRecipeForm, EditRecipeForm, AddListForm, AddListItemForm, AddToListForm, AddToMealPlannerForm, ExploreSearchForm, AccountPrefsForm
from flask_login import current_user, login_user, logout_user, login_required
from flask_paginate import Pagination
from app.models import User, Recipe, Category, Shoplist, Listitem, MealRecipe
from app.email import send_password_reset_email
from werkzeug.urls import url_parse
from datetime import datetime
from PIL import Image
from urllib.parse import urlparse
from urllib.request import urlopen, Request
from bs4 import BeautifulSoup
import secrets, time, random, os, imghdr, requests, re, urllib.request

@app.before_request
def before_request():
    if current_user.is_authenticated:
        current_user.last_time = datetime.utcnow()
        db.session.commit()

@app.errorhandler(413)
def photo_too_large(e):
    return "The attached photo is too large.", 413

@app.context_processor
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

@app.route('/recipe-photos/<path:filename>')
def recipePhotos(filename):
    return send_from_directory(app.root_path + '/recipe-photos/', filename)

@app.route('/about')
@login_required
def about():
    return render_template('about.html', title='About')

@app.route('/', methods=['GET', 'POST'])
@app.route('/my-recipes/all', methods=['GET', 'POST'])
@login_required
def allRecipes():
    user = User.query.filter_by(email=current_user.email).first_or_404()
    page = request.args.get('page', 1, type=int)
    if user.pref_sort == 0:
        recipes = user.recipes.order_by(Recipe.title).paginate(page=page,
            per_page=app.config['MAIN_RECIPES_PER_PAGE'], error_out=False)
    elif user.pref_sort == 1:
        recipes = user.recipes.order_by(Recipe.time_created).paginate(page=page,
            per_page=app.config['MAIN_RECIPES_PER_PAGE'], error_out=False)
    else:
        recipes = user.recipes.order_by(Recipe.time_created.desc()).paginate(page=page,
            per_page=app.config['MAIN_RECIPES_PER_PAGE'], error_out=False)
    next_url = url_for('allRecipes', page=recipes.next_num) \
        if recipes.has_next else None
    prev_url = url_for('allRecipes', page=recipes.prev_num) \
        if recipes.has_prev else None
    form = DisplaySettingsForm()
    if form.validate_on_submit():
        user.pref_size = form.recipe_size.data
        user.pref_sort = form.sort_by.data
        db.session.commit()
        return redirect(url_for('allRecipes'))
    return render_template('all-recipes.html', title='All Recipes', user=user, recipes=recipes.items,
        form=form, next_url=next_url, prev_url=prev_url)

@app.route('/api/my-recipes/all')
@login_required
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

@app.route('/my-recipes/favorites', methods=['GET', 'POST'])
@login_required
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
    next_url = url_for('favorites', page=recipes.next_num) \
        if recipes.has_next else None
    prev_url = url_for('favorites', page=recipes.prev_num) \
        if recipes.has_prev else None
    form = DisplaySettingsForm()
    if form.validate_on_submit():
        user.pref_size = form.recipe_size.data
        user.pref_sort = form.sort_by.data
        db.session.commit()
        return redirect(url_for('favorites'))
    return render_template('favorites.html', title='Favorites', user=user, recipes=recipes.items,
        form=form, next_url=next_url, prev_url=prev_url)

@app.route('/recipe/<hexid>/favorite')
@login_required
def favorite(hexid):
    recipe = Recipe.query.filter_by(hex_id=hexid).first()
    if recipe is None:
        flash('Error: recipe does not exist')
        return redirect(url_for('allRecipes'))
    recipe.favorite = 1
    db.session.commit()
    flash('This recipe has been added to your Favorites.')
    return redirect(url_for('recipeDetail', hexid=hexid))

@app.route('/recipe/<hexid>/unfavorite')
@login_required
def unfavorite(hexid):
    recipe = Recipe.query.filter_by(hex_id=hexid).first()
    if recipe is None:
        flash('Error: recipe does not exist')
        return redirect(url_for('allRecipes'))
    recipe.favorite = 0
    db.session.commit()
    flash('This recipe has been removed from your Favorites.')
    return redirect(url_for('recipeDetail', hexid=hexid))

@app.route('/recipe/<hexid>/make-public')
@login_required
def makePublic(hexid):
    recipe = Recipe.query.filter_by(hex_id=hexid).first()
    if recipe is None:
        flash('Error: recipe does not exist')
        return redirect(url_for('allRecipes'))
    recipe.public = 1
    db.session.commit()
    flash('You can now share the URL for this recipe.')
    return redirect(url_for('recipeDetail', hexid=hexid))

@app.route('/recipe/<hexid>/make-private')
@login_required
def makePrivate(hexid):
    recipe = Recipe.query.filter_by(hex_id=hexid).first()
    if recipe is None:
        flash('Error: recipe does not exist')
        return redirect(url_for('allRecipes'))
    recipe.public = 0
    db.session.commit()
    flash('The recipe URL can no longer be shared.')
    return redirect(url_for('recipeDetail', hexid=hexid))

@app.route('/recipe/<hexid>', methods=['GET', 'POST'])
def recipeDetail(hexid):
    recipe = Recipe.query.filter_by(hex_id=hexid).first()
    form = AddToListForm()
    form2 = AddToMealPlannerForm(prefix='a')
    w, h = 2, 30
    month = [[0 for x in range(w)] for y in range(h)]
    curr_dt = datetime.now()
    timestamp = int(time.mktime(curr_dt.timetuple()))
    days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
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
        timestamp += 86400
    if current_user.is_authenticated:
        choices = []
        user = User.query.filter_by(email=current_user.email).first_or_404()
        lists = user.shop_lists.all()
        select_length = 0
        for list in lists:
            curr_list = list.label
            choices.append(curr_list)
            select_length += 1
        form.selectlist.choices = choices
    if recipe is None:
        recipe_title = 'Error'
        owner = 0
        ingredients = ''
        instructions = ''
    else:
        recipe_title = recipe.title
        owner = recipe.user_id
        ingred = recipe.ingredients
        ingredients = ingred.split('\n')
        instruc = recipe.instructions
        instructions = instruc.split('\n')
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
    if form2.validate_on_submit():
        # Get value from select field which has name attribute of selectdate
        # This is needed since select field is written manually instead of using {{ form2.selectdate }} in template
        selectdate = request.form.get('selectdate')
        hex_valid2 = 0
        while hex_valid2 == 0:
            hex_string2 = secrets.token_hex(5)
            hex_exist2 = MealRecipe.query.filter_by(hex_id=hex_string2).first()
            if hex_exist2 is None:
                hex_valid2 = 1
        newmealplan = MealRecipe(hex_id=hex_string2, date=selectdate, recipe_id=recipe.id, user_id=current_user.id)
        planexist = MealRecipe.query.filter_by(user_id=current_user.id, recipe_id=recipe.id, date=selectdate).first()
        if planexist is None:
            if any(selectdate in sublist for sublist in month):
                db.session.add(newmealplan)
                db.session.commit()
                flash('This recipe has been added to your meal plan.')
            else:
                flash('Error: ' + selectdate)
        else:
            flash('Error: this recipe is already scheduled for the selected date.')
    return render_template('recipe-detail.html', title=recipe_title, recipe=recipe, choices=choices, owner=owner, ingredients=ingredients,
        instructions=instructions, form=form, form2=form2, month=month) 

@app.route('/my-recipes/categories', methods=['GET', 'POST'])
@login_required
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
    next_url = url_for('categories', page=recipes.next_num, c=query_string) \
        if recipes.has_next else None
    prev_url = url_for('categories', page=recipes.prev_num, c=query_string) \
        if recipes.has_prev else None
    recipe_count = len(rec_count)
    form = DisplaySettingsForm()
    form2 = AddCategoryForm(prefix='a')
    cats = []
    for cat in categories:
        curr_cat = cat.label
        cats.append(curr_cat)
    if form.submit.data and form.validate_on_submit():
        user.pref_size = form.recipe_size.data
        user.pref_sort = form.sort_by.data
        db.session.commit()
        return redirect(url_for('categories'))
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
        return redirect(url_for('categories'))
    return render_template('categories.html', title='Categories', user=user, categories=categories, query_string=query_string,
        recipes=recipes.items, recipe_count=recipe_count, form=form, form2=form2, cats=cats, next_url=next_url, prev_url=prev_url)

@app.route('/m/category/<catname>')
@login_required
def mobileCategory(catname):
    user = User.query.filter_by(email=current_user.email).first_or_404()
    page = request.args.get('page', 1, type=int)
    rec_count = user.recipes.filter_by(category=catname).all()
    if user.pref_sort == 0:
        recipes = user.recipes.filter_by(category=catname).order_by(Recipe.title).paginate(page=page,
            per_page=app.config['CAT_RECIPES_PER_PAGE'], error_out=False)
    elif user.pref_sort == 1:
        recipes = user.recipes.filter_by(category=catname).order_by(Recipe.time_created).paginate(page=page,
            per_page=app.config['CAT_RECIPES_PER_PAGE'], error_out=False)
    else:
        recipes = user.recipes.filter_by(category=catname).order_by(Recipe.time_created.desc()).paginate(page=page,
            per_page=app.config['CAT_RECIPES_PER_PAGE'], error_out=False)
    next_url = url_for('mobileCategory', catname=catname, page=recipes.next_num) \
        if recipes.has_next else None
    prev_url = url_for('mobileCategory', catname=catname, page=recipes.prev_num) \
        if recipes.has_prev else None
    recipe_count = len(rec_count)
    return render_template('mobile-category.html', title=catname, user=user, recipes=recipes.items,
        recipe_count=recipe_count, catname=catname, next_url=next_url, prev_url=prev_url)

@app.route('/remove-category/<catid>')
@login_required
def removeCategory(catid):
    category = Category.query.filter_by(hex_id=catid).first()
    user = User.query.filter_by(email=current_user.email).first()
    recipes = user.recipes.all()
    if category is None:
        flash('Error: category does not exist.')
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
    return redirect(url_for('categories'))

@app.route('/remove-recipe/<hexid>')
@login_required
def removeRecipe(hexid):
    delrecipe = Recipe.query.filter_by(hex_id=hexid).first()
    if delrecipe is None:
        flash('Error: recipe does not exist')
        return redirect(url_for('allRecipes'))
    defaults = ['default01.png', 'default02.png', 'default03.png', 'default04.png', 'default05.png', 'default06.png', 'default07.png',
        'default08.png', 'default09.png', 'default10.png', 'default11.png', 'default12.png', 'default13.png', 'default14.png',
        'default15.png', 'default16.png', 'default17.png', 'default18.png', 'default19.png', 'default20.png', 'default21.png',
        'default22.png', 'default23.png', 'default24.png', 'default25.png', 'default26.png', 'default27.png']
    fullpath = app.config['UPLOAD_FOLDER'] + '/' + delrecipe.photo
    if delrecipe.photo not in defaults:
        os.remove(fullpath)
    db.session.delete(delrecipe)
    db.session.commit()
    flash('Recipe has been removed.')
    return redirect(url_for('allRecipes'))

@app.route('/add-recipe', methods=['GET', 'POST'])
@login_required
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
            img.save(app.config['UPLOAD_FOLDER'] + '/' + new_file)
            recipe = Recipe(hex_id=hex_string, title=form.recipe_name.data, category=form.category.data, photo=new_file,
                description=form.description.data, url=form.url.data, prep_time=form.prep_time.data, cook_time=form.cook_time.data,
                total_time=form.total_time.data, ingredients=form.ingredients.data, instructions=form.instructions.data, favorite=0, public=0, user_id=current_user.id)
        else:
            recipe = Recipe(hex_id=hex_string, title=form.recipe_name.data, category=form.category.data, photo=rand_default,
                description=form.description.data, url=form.url.data, prep_time=form.prep_time.data, cook_time=form.cook_time.data,
                total_time=form.total_time.data, ingredients=form.ingredients.data, instructions=form.instructions.data, favorite=0, public=0, user_id=current_user.id)
        db.session.add(recipe)
        db.session.commit()
        flash('The recipe has been added.')
        return redirect(url_for('addRecipe'))
    return render_template('add-recipe.html', title='Add a New Recipe', form=form, choices=choices)

@app.route('/edit-recipe/<hexid>', methods=['GET', 'POST'])
@login_required
def editRecipe(hexid):
    recipe = Recipe.query.filter_by(hex_id=hexid).first()
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
            img.save(app.config['UPLOAD_FOLDER'] + '/' + new_file)
            if recipe.photo not in defaults:
                os.remove(old_path)
            recipe.photo = new_file
        db.session.commit()
        flash('The recipe has been updated.')
        return redirect(url_for('recipeDetail', hexid=hexid))
    return render_template('edit-recipe.html', title='Edit Recipe', form=form, recipe=recipe, choices=choices)

@app.route('/shopping-lists', methods=['GET', 'POST'])
def shoppingLists():
    user = User.query.filter_by(email=current_user.email).first_or_404()
    lists = user.shop_lists.order_by(Shoplist.label).all()
    query_string = request.args.get('list')
    if query_string is None:
        list = user.shop_lists.filter_by(label='Miscellaneous').first()
    else:
        list = user.shop_lists.filter_by(label=query_string).first()
    items = list.list_items.order_by(Listitem.item).all()
    items_tobuy = user.list_items.filter_by(list_id=list.id, complete=0).all()
    items_comp = user.list_items.filter_by(list_id=list.id, complete=1).all()
    form = AddListForm()
    form2 = AddListItemForm(prefix='a')
    lists_arr = []
    for thing in lists:
        curr_list = thing.label
        lists_arr.append(curr_list)
    items_arr = []
    for thing in items:
        curr_item = thing.item
        items_arr.append(curr_item)
    if form.submitlist.data and form.validate_on_submit():
        if form.newlist.data in lists_arr:
            flash('Error: the shopping list you entered already exists.')
        elif len(lists_arr) > 19:
            flash('Error: you are limited to 20 shopping lists.')
        else:
            hex_valid = 0
            while hex_valid == 0:
                hex_string = secrets.token_hex(4)
                hex_exist = Shoplist.query.filter_by(hex_id=hex_string).first()
                if hex_exist is None:
                    hex_valid = 1
            sel_list = Shoplist(hex_id=hex_string, label=form.newlist.data, user_id=current_user.id)
            db.session.add(sel_list)
            db.session.commit()
            flash('The shopping list has been added.')
        return redirect(url_for('shoppingLists', list=list.label))
    if form2.submititem.data and form2.validate_on_submit():
        if form2.newitem.data in items_arr:
            flash('Error: the list item you entered already exists.')
        elif len(items_arr) > 69:
            flash('Error: you are limited to 70 items per list.')
        else:
            hex_valid2 = 0
            while hex_valid2 == 0:
                hex_string2 = secrets.token_hex(5)
                hex_exist2 = Listitem.query.filter_by(hex_id=hex_string2).first()
                if hex_exist2 is None:
                    hex_valid2 = 1
            sel_item = Listitem(hex_id=hex_string2, item=form2.newitem.data, user_id=current_user.id, complete=0, list_id=list.id)
            db.session.add(sel_item)
            db.session.commit()
            flash('The item has been added.')
        return redirect(url_for('shoppingLists', list=list.label))
    return render_template('shopping-lists.html', title='Shopping Lists', lists=lists, query_string=query_string, list=list,
        lists_arr=lists_arr, items=items, items_tobuy=items_tobuy, items_comp=items_comp, form=form, form2=form2)

@app.route('/m/shopping-list/<listname>', methods=['GET', 'POST'])
@login_required
def mobileList(listname):
    user = User.query.filter_by(email=current_user.email).first_or_404()
    list = user.shop_lists.filter_by(label=listname).first()
    if list is None:
        flash('Error: the list you requested does not exist.')
    items = list.list_items.order_by(Listitem.item).all()
    items_tobuy = user.list_items.filter_by(list_id=list.id, complete=0).all()
    items_comp = user.list_items.filter_by(list_id=list.id, complete=1).all()
    form = AddListItemForm()
    items_arr = []
    for thing in items:
        curr_item = thing.item
        items_arr.append(curr_item)
    if form.submititem.data and form.validate_on_submit():
        if form.newitem.data in items_arr:
            flash('Error: the list item you entered already exists.')
        elif len(items_arr) > 69:
            flash('Error: you are limited to 70 items per list.')
        else:
            hex_valid = 0
            while hex_valid == 0:
                hex_string = secrets.token_hex(5)
                hex_exist = Listitem.query.filter_by(hex_id=hex_string).first()
                if hex_exist is None:
                    hex_valid = 1
            sel_item = Listitem(hex_id=hex_string, item=form.newitem.data, user_id=current_user.id, complete=0, list_id=list.id)
            db.session.add(sel_item)
            db.session.commit()
            flash('The item has been added.')
        return redirect(url_for('mobileList', listname=list.label))
    return render_template('mobile-shopping-list.html', title=listname, list=list, items=items, items_tobuy=items_tobuy,
        items_comp=items_comp, form=form)

@app.route('/remove-list/<mobile>/<hexid>')
@login_required
def removeList(hexid, mobile):
    list = Shoplist.query.filter_by(hex_id=hexid).first()
    user = User.query.filter_by(email=current_user.email).first()
    listitems = Listitem.query.filter_by(list_id=list.id).all()
    if list is None:
        flash('Error: shopping list does not exist.')
    elif list.label == 'Miscellaneous':
        flash('Error: Miscellaneous cannot be deleted because it is the default shopping list.')
    else:
        if list.user_id == current_user.id:
            for item in listitems:
                db.session.delete(item)
            db.session.delete(list)
            db.session.commit()
            flash('Shopping list has been removed.')
        else:
            flash('Error: shopping list does not exist.')
    if mobile == '0':
        return redirect(url_for('shoppingLists'))
    else:
        return redirect(url_for('mobileList', listname='Miscellaneous'))

@app.route('/remove-item/<mobile>/<hexid>')
@login_required
def removeListitem(hexid, mobile):
    listitem = Listitem.query.filter_by(hex_id=hexid).first()
    list = Shoplist.query.filter_by(id=listitem.list_id).first()
    if listitem is None:
        flash('Error: item does not exist.')
    else:
        if listitem.user_id == current_user.id:
            db.session.delete(listitem)
            db.session.commit()
            flash('The item has been removed.')
        else:
            flash('Error: item does not exist.')
    if mobile == '0':
        return redirect(url_for('shoppingLists', list=list.label))
    else:
        return redirect(url_for('mobileList', listname=list.label))

@app.route('/mark-item/<mobile>/<hexid>')
@login_required
def markItem(hexid, mobile):
    listitem = Listitem.query.filter_by(hex_id=hexid).first()
    list = Shoplist.query.filter_by(id=listitem.list_id).first()
    if listitem is None:
        flash('Error: item does not exist.')
    else:
        if listitem.user_id == current_user.id:
            if listitem.complete == 0:
                listitem.complete = 1
                db.session.commit()
            else:
                listitem.complete = 0
                db.session.commit()
        else:
            flash('Error: item does not exist.')
    if mobile == '0':
        return redirect(url_for('shoppingLists', list=list.label))
    else:
        return redirect(url_for('mobileList', listname=list.label))

@app.route('/meal-planner')
@login_required
def mealPlanner():
    query_string = request.args.get('day')
    query_string_full = ""
    user = User.query.filter_by(email=current_user.email).first_or_404()
    plannedmeals = user.planned_meals.all()
    # Create 2D array to hold compact date and full date
    w, h = 2, 30
    month = [[0 for x in range(w)] for y in range(h)]
    curr_dt = datetime.now()
    timestamp = int(time.mktime(curr_dt.timetuple()))
    days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
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
        timestamp += 86400
        if d[0] == query_string:
            query_string_full = d[1]
    # Create array to store only compact month, used to validate query string
    compactmonth = []
    for d in month:
        compactmonth.append(d[0])
    # Create 2D array to store recipe info, it will somewhat mirror plannedmeals
    w2, h2 = 3, len(plannedmeals)
    recdetails = [[0 for x in range(w2)] for y in range(h2)]
    mealiteration = 0
    for meal in plannedmeals:
        recipe = Recipe.query.filter_by(id=meal.recipe_id).first_or_404()
        recdetails[mealiteration][0] = recipe.title
        recdetails[mealiteration][1] = recipe.category
        recdetails[mealiteration][2] = recipe.hex_id
        mealiteration += 1
    # Create array to store dates that meals are planned for, used by template to hide days with no meals
    dayswithmeals = []
    for meal in plannedmeals:
        if meal.date not in dayswithmeals:
            dayswithmeals.append(meal.date)
    # Create query_count variable to store number of meals for particular day, used by template to show error if no meals
    query_count = 0
    for meal in plannedmeals:
        if meal.date == query_string:
            query_count += 1
    return render_template('meal-planner.html', title='Meal Planner', plannedmeals=plannedmeals, recdetails=recdetails, dayswithmeals=dayswithmeals,
	month=month, query_string=query_string, query_string_full=query_string_full, query_count=query_count, compactmonth=compactmonth)

@app.route('/remove-plan/<hexid>')
@login_required
def removePlan(hexid):
    mealplan = MealRecipe.query.filter_by(hex_id=hexid).first()
    if mealplan is None:
        flash('Error: meal plan does not exist or you lack permission to remove it.')
    else:
        if mealplan.user_id == current_user.id:
            db.session.delete(mealplan)
            db.session.commit()
            flash('The meal plan has been deleted.')
        else:
            flash('Error: meal plan does not exist or you lack permission to remove it.')
    return redirect(url_for('mealPlanner'))

@app.route('/explore', methods=['GET', 'POST'])
@login_required
def explore():
    files = ['/static/explore-all-randomized.txt', '/static/explore-beef-randomized.txt', '/static/explore-breakfast-randomized.txt',
        '/static/explore-chicken-randomized.txt', '/static/explore-desserts-randomized.txt', '/static/explore-salads-randomized.txt',
        '/static/explore-seafood-randomized.txt', '/static/explore-sides-randomized.txt']
    recipes = []
    for file in files:
        readfile_all = open(app.root_path + file, "r")
        filelines_all = readfile_all.readlines()
        recipes_all = []
        count_all = 1
        for line in filelines_all:
            x_all = line.split(";")
            url_all = urlparse(x_all[0]).netloc
            new_url_all = url_all.replace("www.","")
            newline_all = [x_all[1], new_url_all, x_all[0], count_all]
            recipes_all.append(newline_all)
            count_all += 1
            if count_all > 11:
                break
        readfile_all.close()
        recipes.append(recipes_all)
    rec_all = recipes[0]
    rec_beef = recipes[1]
    rec_breakfast = recipes[2]
    rec_chicken = recipes[3]
    rec_desserts = recipes[4]
    rec_salads = recipes[5]
    rec_seafood = recipes[6]
    rec_sides = recipes[7]
    form = ExploreSearchForm()
    if form.validate_on_submit():
        return redirect(url_for('exploreSearch', query=form.search.data))
    return render_template('explore.html', title='Explore', rec_all=rec_all, rec_beef=rec_beef, rec_breakfast=rec_breakfast,
        rec_chicken=rec_chicken, rec_desserts=rec_desserts, rec_salads=rec_salads, rec_seafood=rec_seafood, rec_sides=rec_sides, form=form)

@app.route('/explore/search')
@login_required
def exploreSearch():
    query_string = request.args.get('query')
    recipes = []
    all_recipes = []
    count = 1
    if query_string:
        readfile = open(app.root_path + "/static/explore-all-randomized.txt", "r")
        filelines = readfile.readlines()
        for line in filelines:
            x = line.split(";")
            url = urlparse(x[0]).netloc
            new_url = url.replace("www.","")
            newline = [x[1], new_url, x[0], count]
            all_recipes.append(newline)
            count += 1
        readfile.close()
        query_items = query_string.split(" ")
        rec_count = 1
        for recipe in all_recipes:
            is_good = True
            for item in query_items:
                if item not in recipe[0]:
                    is_good = False
            if is_good == True:
                new_rec = recipe
                new_rec.append(rec_count)
                recipes.append(new_rec)
                rec_count += 1
    else:
        filelines = []
    PER_PAGE = app.config['EXPLORE_RECIPES_PER_PAGE']
    page = request.args.get('page', 1, type=int)
    if page:
        curr_page = page
    else:
        curr_page = 1
    i=(page-1)*PER_PAGE
    recipes_page = recipes[i:i+PER_PAGE]
    if len(filelines) > 2:
        rec_first = recipes_page[0]
        rec_first = rec_first[4]
        rec_last = recipes_page[len(recipes_page)-1]
        rec_last = rec_last[4]
    else:
        rec_first = 0
        rec_last = 0
    rec_count = len(recipes)
    pagination = Pagination(page=page, per_page=PER_PAGE, total=len(recipes), search=False, record_name='recipes')
    return render_template('explore-search.html', title='Explore Search', recipes=recipes_page, pagination=pagination, curr_page=curr_page, page=page,
        rec_first=rec_first, rec_last=rec_last, rec_count=rec_count, query_string=query_string)

@app.route('/explore/group/<group>')
@login_required
def exploreGroup(group):
    if group == "all":
        group_title = "All Recipes 🍽️"
        readfile = open(app.root_path + "/static/explore-all-randomized.txt", "r")
    elif group == "beef-entrees":
        group_title = "Beef Entrees 🥩"
        readfile = open(app.root_path + "/static/explore-beef-randomized.txt", "r")
    elif group == "breakfast":
        group_title = "Breakfast 🥞"
        readfile = open(app.root_path + "/static/explore-breakfast-randomized.txt", "r")
    elif group == "chicken-entrees":
        group_title = "Chicken Entrees 🍗"
        readfile = open(app.root_path + "/static/explore-chicken-randomized.txt", "r")
    elif group == "desserts":
        group_title = "Desserts 🍰"
        readfile = open(app.root_path + "/static/explore-desserts-randomized.txt", "r")
    elif group == "salads":
        group_title = "Salads 🥗"
        readfile = open(app.root_path + "/static/explore-salads-randomized.txt", "r")
    elif group == "seafood-entrees":
        group_title = "Seafood Entrees 🍤"
        readfile = open(app.root_path + "/static/explore-seafood-randomized.txt", "r")
    elif group == "side-dishes":
        group_title = "Side Dishes 🌽"
        readfile = open(app.root_path + "/static/explore-sides-randomized.txt", "r")
    else:
        group_title = "Error"
        readfile = open(app.root_path + "/static/explore-blank.txt", "r")
    filelines = readfile.readlines()
    recipes = []
    count = 1
    if len(filelines) > 2:
        for line in filelines:
            x = line.split(";")
            url = urlparse(x[0]).netloc
            new_url = url.replace("www.","")
            newline = [x[1], new_url, x[0], count]
            recipes.append(newline)
            count += 1
    readfile.close()
    PER_PAGE = app.config['EXPLORE_RECIPES_PER_PAGE']
    page = request.args.get('page', 1, type=int)
    if page:
        curr_page = page
    else:
        curr_page = 1
    i=(page-1)*PER_PAGE
    recipes_page = recipes[i:i+PER_PAGE]
    if len(filelines) > 2:
        rec_first = recipes_page[0]
        rec_first = rec_first[3]
        rec_last = recipes_page[len(recipes_page)-1]
        rec_last = rec_last[3]
    else:
        rec_first = 0
        rec_last = 0
    rec_count = len(recipes)
    pagination = Pagination(page=page, per_page=PER_PAGE, total=len(recipes), search=False, record_name='recipes')
    return render_template('explore-group.html', title=group_title, recipes=recipes_page, pagination=pagination, group=group,
        group_title=group_title, curr_page=curr_page, rec_first=rec_first, rec_last=rec_last, rec_count=rec_count)

@app.route('/explore/recipe/<rec_group>/<recnum>', methods=['GET', 'POST'])
@login_required
def exploreRecipeDetail(rec_group, recnum):
    if rec_group == "all":
        readfile = open(app.root_path + '/static/explore-all-randomized.txt', "r")
    elif rec_group == "beef-entrees":
        readfile = open(app.root_path + '/static/explore-beef-randomized.txt', "r")
    elif rec_group == "breakfast":
        readfile = open(app.root_path + '/static/explore-breakfast-randomized.txt', "r")
    elif rec_group == "chicken-entrees":
        readfile = open(app.root_path + '/static/explore-chicken-randomized.txt', "r")
    elif rec_group == "desserts":
        readfile = open(app.root_path + '/static/explore-desserts-randomized.txt', "r")
    elif rec_group == "salads":
        readfile = open(app.root_path + '/static/explore-salads-randomized.txt', "r")
    elif rec_group == "seafood-entrees":
        readfile = open(app.root_path + '/static/explore-seafood-randomized.txt', "r")
    elif rec_group == "side-dishes":
        readfile = open(app.root_path + '/static/explore-sides-randomized.txt', "r")
    else:
        readfile = open(app.root_path + '/static/explore-blank.txt', "r")
    filelines = readfile.readlines()
    lines = []
    for line in filelines:
        x = line.split(";")
        newline = [x[0], x[1]]
        lines.append(newline)
    readfile.close()
    try:
        rec_num = int(recnum)
    except:
        rec_url = ''
        rec_title = ''
    else:
        try:
            rec_line = lines[rec_num - 1]
        except:
            rec_url = ''
            rec_title = ''
        else:
            rec_url = rec_line[0]
            rec_title = rec_line[1].rstrip()
    if "cookinglsl.com" in rec_url:
        page = requests.get(rec_url)
        soup = BeautifulSoup(page.text, 'html.parser')
        photo_1 = soup.find('div',class_='wprm-recipe-image')
        photo_2 = photo_1.find('img')
        photo = photo_2['data-lazy-src']
        preptime_m = soup.find('span',class_='wprm-recipe-details wprm-recipe-details-minutes wprm-recipe-prep_time wprm-recipe-prep_time-minutes')
        preptime_h = soup.find('span',class_='wprm-recipe-details wprm-recipe-details-hours wprm-recipe-prep_time wprm-recipe-prep_time-hours')
        if preptime_m or preptime_h:
            if preptime_m:
                pt_m = preptime_m.contents[0]
                pt_m = int(pt_m)
            else:
                pt_m = 0
            if preptime_h:
                pt_h = preptime_h.contents[0]
                pt_h = int(pt_h)
            else:
                pt_h = 0
            preptime = pt_m + (pt_h * 60)
        else:
            preptime = ''
        cooktime_m = soup.find('span',class_='wprm-recipe-details wprm-recipe-details-minutes wprm-recipe-cook_time wprm-recipe-cook_time-minutes')
        cooktime_h = soup.find('span',class_='wprm-recipe-details wprm-recipe-details-hours wprm-recipe-cook_time wprm-recipe-cook_time-hours')
        if cooktime_m or cooktime_h:
            if cooktime_m:
                ct_m = cooktime_m.contents[0]
                ct_m = int(ct_m)
            else:
                ct_m = 0
            if cooktime_h:
                ct_h = cooktime_h.contents[0]
                ct_h = int(ct_h)
            else:
                ct_h = 0
            cooktime = ct_m + (ct_h * 60)
        else:
            cooktime = ''
        totaltime_m = soup.find('span',class_='wprm-recipe-details wprm-recipe-details-minutes wprm-recipe-total_time wprm-recipe-total_time-minutes')
        totaltime_h = soup.find('span',class_='wprm-recipe-details wprm-recipe-details-hours wprm-recipe-total_time wprm-recipe-total_time-hours')
        if totaltime_m or totaltime_h:
            if totaltime_m:
                tt_m = totaltime_m.contents[0]
                tt_m = int(tt_m)
            else:
                tt_m = 0
            if totaltime_h:
                tt_h = totaltime_h.contents[0]
                tt_h = int(tt_h)
            else:
                tt_h = 0
            totaltime = tt_m + (tt_h * 60)
        else:
            totaltime = ''
        description_1 = soup.find('div',class_='wprm-recipe-summary wprm-block-text-normal')
        if description_1:
            description = description_1.text
        else:
            description = ''
        ingredients = []
        ingredients_1 = soup.find('div',class_='wprm-recipe-ingredients-container')
        if ingredients_1:
            ingredients_2 = ingredients_1.find_all('li',class_='wprm-recipe-ingredient')
            for ingredient in ingredients_2:
                ingred = ingredient.text
                ingred = ingred.replace("\n"," ")
                ingred = ingred.replace("▢","")
                ingred = ingred.strip()
                ingredients.append(ingred)
        instructions = []
        instructions_1 = soup.find('div',class_='wprm-recipe-instructions-container')
        if instructions_1:
            instructions_2 = instructions_1.find_all('div',class_='wprm-recipe-instruction-group')
            for group in instructions_2:
                instructions_h4 = group.find('h4')
                if instructions_h4:
                    instructions.append(instructions_h4.contents[0])
                inst_steps = group.find_all('div',class_='wprm-recipe-instruction-text')
                for step in inst_steps:
                    inst_step = step.text
                    instructions.append(inst_step)
    elif "lanascooking.com" in rec_url:
        page = requests.get(rec_url)
        soup = BeautifulSoup(page.text, 'html.parser')
        photo_1 = soup.find('img',class_='attachment-full size-full wp-post-image perfmatters-lazy')
        if photo_1:
            photo = photo_1['data-src']
        else:
            photo = ''
        preptime_m = soup.find('span',class_='wprm-recipe-details wprm-recipe-details-minutes wprm-recipe-prep_time wprm-recipe-prep_time-minutes')
        preptime_h = soup.find('span',class_='wprm-recipe-details wprm-recipe-details-hours wprm-recipe-prep_time wprm-recipe-prep_time-hours')
        if preptime_m or preptime_h:
            if preptime_m:
                pt_m = preptime_m.contents[0]
                pt_m = int(pt_m)
            else:
                pt_m = 0
            if preptime_h:
                pt_h = preptime_h.contents[0]
                pt_h = int(pt_h)
            else:
                pt_h = 0
            preptime = pt_m + (pt_h * 60)
        else:
            preptime = ''
        cooktime_m = soup.find('span',class_='wprm-recipe-details wprm-recipe-details-minutes wprm-recipe-cook_time wprm-recipe-cook_time-minutes')
        cooktime_h = soup.find('span',class_='wprm-recipe-details wprm-recipe-details-hours wprm-recipe-cook_time wprm-recipe-cook_time-hours')
        if cooktime_m or cooktime_h:
            if cooktime_m:
                ct_m = cooktime_m.contents[0]
                ct_m = int(ct_m)
            else:
                ct_m = 0
            if cooktime_h:
                ct_h = cooktime_h.contents[0]
                ct_h = int(ct_h)
            else:
                ct_h = 0
            cooktime = ct_m + (ct_h * 60)
        else:
            cooktime = ''
        totaltime_m = soup.find('span',class_='wprm-recipe-details wprm-recipe-details-minutes wprm-recipe-total_time wprm-recipe-total_time-minutes')
        totaltime_h = soup.find('span',class_='wprm-recipe-details wprm-recipe-details-hours wprm-recipe-total_time wprm-recipe-total_time-hours')
        if totaltime_m or totaltime_h:
            if totaltime_m:
                tt_m = totaltime_m.contents[0]
                tt_m = int(tt_m)
            else:
                tt_m = 0
            if totaltime_h:
                tt_h = totaltime_h.contents[0]
                tt_h = int(tt_h)
            else:
                tt_h = 0
            totaltime = tt_m + (tt_h * 60)
        else:
            totaltime = ''
        description_1 = soup.find('meta',attrs={"property": "og:description"})
        if description_1:
            description = description_1['content']
        else:
            description = ''
        ingredients = []
        ingredients_1 = soup.find('div',class_='wprm-recipe-ingredients-container')
        if ingredients_1:
            ingredients_2 = ingredients_1.find_all('li',class_='wprm-recipe-ingredient')
            for ingredient in ingredients_2:
                ingred = ingredient.text
                ingred = ingred.replace("\n"," ")
                ingred = ingred.replace("▢","")
                ingred = ingred.strip()
                ingredients.append(ingred)
        instructions = []
        instructions_1 = soup.find('div',class_='wprm-recipe-instructions-container')
        if instructions_1:
            instructions_2 = instructions_1.find_all('div',class_='wprm-recipe-instruction-group')
            for group in instructions_2:
                instructions_h4 = group.find('h4')
                if instructions_h4:
                    instructions.append(instructions_h4.contents[0])
                inst_steps = group.find_all('div',class_='wprm-recipe-instruction-text')
                for step in inst_steps:
                    inst_step = step.text
                    instructions.append(inst_step)
    elif "justapinch.com" in rec_url:
        page = requests.get(rec_url)
        soup = BeautifulSoup(page.text, 'html.parser')
        photo_1 = soup.find('div',class_='photo-aspect-container')
        if photo_1:
            photo_2 = photo_1.find('img')
            photo = photo_2['src']
        else:
            photo = ''
        preptime_1 = soup.find('span', string='prep time')
        if preptime_1:
            preptime_2 = preptime_1.find_next_siblings('span')
            preptime_3 = preptime_2[0].text
            if "Hr" in preptime_3:
                pt_h = preptime_3[0]
                pt_h = int(pt_h)
                if "Min" in preptime_3:
                    pt_mins = re.search('Hr (.*)Min', preptime_3)
                    pt_m = pt_mins.group(1)
                    pt_m = int(pt_m)
                else:
                    pt_m = 0
            else:
                pt_h = 0
                pt_m = preptime_3.replace(" Min","")
                pt_m = int(pt_m)
            preptime = pt_m + (pt_h * 60)
        else:
            preptime = ''
        cooktime_1 = soup.find('span', string='cook time')
        if cooktime_1:
            cooktime_2 = cooktime_1.find_next_siblings('span')
            cooktime_3 = cooktime_2[0].text
            if "Hr" in cooktime_3:
                ct_h = cooktime_3[0]
                ct_h = int(ct_h)
                if "Min" in cooktime_3:
                    ct_mins = re.search('Hr (.*)Min', cooktime_3)
                    ct_m = ct_mins.group(1)
                    ct_m = int(ct_m)
                else:
                    ct_m = 0
            else:
                ct_h = 0
                ct_m = cooktime_3.replace(" Min","")
                ct_m = int(ct_m)
            cooktime = ct_m + (ct_h * 60)
        else:
            cooktime = ''
        if preptime and cooktime:
            totaltime = preptime + cooktime
        else:
            totaltime = ''
        description_1 = soup.find('div', {'id': 'recipe-notes'})
        if description_1:
            description = description_1.text
        else:
            description = ''
        ingredients = []
        ingredients_1 = soup.find('ul', {'id': 'recipe-ingredients-list'})
        if ingredients_1:
            ingredients_2 = soup.find_all('li',class_='x-checkable')
            for ingredient in ingredients_2:
                ing_amount_1 = ingredient.find('div',class_='text-blue-ribbon text-wrap text-right font-weight-bold mr-2')
                ing_amount = ing_amount_1.text
                ing_amount = ing_amount.strip()
                ing_item_1 = ingredient.find('div',class_='ml-1')
                ing_item = ing_item_1.text
                ingred = ing_amount + ' ' + ing_item
                ingred = ingred.strip()
                ingredients.append(ingred)
        instructions = []
        instructions_1 = soup.find('ul', {'id': 'recipe-preparation'})
        if instructions_1:
            instructions_2 = soup.find_all('div',class_='card-body p-0 py-1')
            for instruction in instructions_2:
                instr_1 = instruction.find('div',class_='flex-fill recipe-direction rcp-ugc-block')
                instr = instr_1.text
                instr = instr.strip()
                instructions.append(instr)
    else:
        preptime = ''
        cooktime = ''
        totaltime = ''
        description = ''
        photo = ''
        ingredients = []
        instructions = []
    form = EmptyForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=current_user.email).first_or_404()
        rec_exist = user.recipes.filter_by(url=rec_url).first()
        if rec_exist is None:
            if ingredients and instructions:
                hex_valid = 0
                while hex_valid == 0:
                    hex_string = secrets.token_hex(4)
                    hex_exist = Recipe.query.filter_by(hex_id=hex_string).first()
                    if hex_exist is None:
                        hex_valid = 1
                if photo:
                    test_photo_1 = Request(photo, headers={'User-Agent': 'Mozilla/5.0'})
                    test_photo_2 = urlopen(test_photo_1)
                    ext = test_photo_2.info()['Content-Type'].split("/")[-1]
                    if ext == 'jpeg':
                        file_extension = '.jpeg'
                    elif ext == 'jpg':
                        file_extension = '.jpg'
                    elif ext == 'png':
                        file_extension = '.png'
                    else:
                        file_extension = ''
                else:
                    file_extension = ''
                if photo and file_extension:
                    hex_valid2 = 0
                    while hex_valid2 == 0:
                        hex_string2 = secrets.token_hex(8)
                        hex_exist2 = Recipe.query.filter(Recipe.photo.contains(hex_string2)).first()
                        if hex_exist2 is None:
                            hex_valid2 = 1
                    i_photo = hex_string2 + file_extension
                    r = requests.get(photo)
                    with open(app.config['UPLOAD_FOLDER'] + '/' + i_photo, 'wb') as outfile:
                        outfile.write(r.content)
                    img = Image.open(app.config['UPLOAD_FOLDER'] + '/' + i_photo)
                    img_width, img_height = img.size
                    if img_width > img_height:
                        if img_width > 1500:
                            basewidth = 1500
                            wpercent = (basewidth/float(img.size[0]))
                            hsize = int((float(img.size[1])*float(wpercent)))
                            img = img.resize((basewidth,hsize), Image.Resampling.LANCZOS)
                    else:
                        if img_height > 1500:
                            baseheight = 1500
                            hpercent = (baseheight/float(img.size[0]))
                            hsize = int((float(img.size[1])*float(wpercent)))
                            img = img.resize((wsize,baseheight), Image.Resampling.LANCZOS)
                    img.save(app.config['UPLOAD_FOLDER'] + '/' + i_photo)
                else:
                    defaults = ['default01.png', 'default02.png', 'default03.png', 'default04.png', 'default05.png', 'default06.png', 'default07.png',
                        'default08.png', 'default09.png', 'default10.png', 'default11.png', 'default12.png', 'default13.png', 'default14.png',
                        'default15.png', 'default16.png', 'default17.png', 'default18.png', 'default19.png', 'default20.png', 'default21.png',
                        'default22.png', 'default23.png', 'default24.png', 'default25.png', 'default26.png', 'default27.png']
                    i_photo = random.choice(defaults)
                try:
                    preptime = int(preptime)
                except:
                    preptime = ''
                try:
                    cooktime = int(cooktime)
                except:
                    cooktime = ''
                try:
                    totaltime = int(totaltime)
                except:
                    totaltime = ''
                i_description = description[:500]
                i_ingredients = ''
                for i in ingredients:
                    i_ingredients = i_ingredients + i + '\n'
                i_ingredients = i_ingredients.strip()
                i_ingredients = i_ingredients[:4400]
                i_instructions = ''
                for i in instructions:
                    i_instructions = i_instructions + i + '\n'
                i_instructions = i_instructions.strip()
                i_instructions = i_instructions[:2200]
                recipe = Recipe(hex_id=hex_string, title=rec_title, category='Miscellaneous', photo=i_photo, description=i_description, url=rec_url,
                    prep_time=preptime, cook_time=cooktime, total_time=totaltime, ingredients=i_ingredients, instructions=i_instructions,
                    favorite=0, public=0, user_id=current_user.id)
                db.session.add(recipe)
                db.session.commit()
                flash('The recipe has been saved to My Recipes.')
            else:
                flash('The recipe is missing ingredients or instructions and cannot be imported.')
        else:
            flash('Error: This recipe is already saved in My Recipes.')
    return render_template('explore-recipe-detail.html', title='Explore Recipe Detail', rec_url=rec_url, rec_title=rec_title, preptime=preptime,
        cooktime=cooktime, totaltime=totaltime, description=description, photo=photo, ingredients=ingredients, instructions=instructions, form=form)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user is None or not user.check_password(form.password.data):
            flash('Invalid email or password')
            return redirect(url_for('login'))
        login_user(user, remember=form.remember_me.data)
        next_page = request.args.get('next')
        if not next_page or url_parse(next_page).netloc != '':
            next_page = url_for('allRecipes')
        return redirect(next_page)
    return render_template('login.html', title='Sign In', form=form)

@app.route('/logout')
def logout():
    logout_user()
    flash('You have successfully signed out.')
    return redirect(url_for('login'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('allRecipes'))
    form = RegistrationForm()
    if form.validate_on_submit():
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
        return redirect(url_for('login'))
    return render_template('register.html', title='Register', form=form)

@app.route('/account', methods=['GET', 'POST'])
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
    if form.validate_on_submit():
        current_user.email = form.email.data
        if form.password.data or form.password2.data:
            user.set_password(form.password.data)
        db.session.commit()
        flash('Your changes have been saved.')
    if form2.validate_on_submit():
        propicture = int(request.form['propicture'])
        accentcolor = int(request.form['accentcolor'])
        if propicture >= 0 and propicture <= 3 and accentcolor >= 0 and accentcolor <= 3:
            user.pref_picture = propicture
            user.pref_color = accentcolor
        else:
            user.pref_picture = 0
            user.pref_color = 0
        db.session.commit()
        flash('Your changes have been saved.')
    return render_template('account.html', title='Account', user=user, form=form, form2=form2, rec_count=rec_count)

@app.route('/account/process-delete')
@login_required
def deleteAccount():
    user = User.query.filter_by(email=current_user.email).first()
    if user is None:
        flash('Error: there was a problem deleting your account')
        return redirect(url_for('user'))
    logout_user()
    db.session.delete(user)
    db.session.commit()
    flash('Your account has been deleted.')
    return redirect(url_for('login'))

@app.route('/request-reset', methods=['GET', 'POST'])
def request_reset():
    if current_user.is_authenticated:
        return redirect(url_for('allRecipes'))
    form = ResetPasswordRequestForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user:
            send_password_reset_email(user)
        flash('Check your email for instructions.')
        return redirect(url_for('login'))
    return render_template('request-reset.html', title='Reset Password', form=form)

@app.route('/set-password/<token>', methods=['GET', 'POST'])
def set_password(token):
    if current_user.is_authenticated:
        return redirect(url_for('allRecipes'))
    user = User.verify_reset_password_token(token)
    if not user:
        flash('Password reset token is invalid.')
        return redirect(url_for('login'))
    form = ResetPasswordForm()
    if form.validate_on_submit():
        user.set_password(form.password.data)
        db.session.commit()
        flash('Your new password has been set.')
        return redirect(url_for('login'))
    return render_template('set-password.html', title='Set Password', form=form)
