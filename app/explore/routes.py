from flask import render_template, flash, redirect, url_for, request
from flask_babel import _
from app import app, db, limiter
from app.explore.forms import ExploreSearchForm, EmptyForm
from flask_login import current_user, login_user, logout_user, login_required
from flask_paginate import Pagination
from app.models import User, Recipe, NutritionalInfo
from werkzeug.urls import url_parse
from PIL import Image
from urllib.parse import urlparse
from urllib.request import urlopen, Request
from bs4 import BeautifulSoup
from fake_useragent import UserAgent
import secrets, time, random, os, imghdr, requests, re, urllib.request, io, base64, cloudscraper
from app.explore import bp
from config import Config

@bp.route('/explore', methods=['GET', 'POST'])
@limiter.limit(Config.DEFAULT_RATE_LIMIT)
def explore():
    files = ['/static/explore-all-randomized.txt']
    recipes = []
    for file in files:
        readfile_all = open(app.root_path + file, "r")
        filelines_all = readfile_all.readlines()
        recipes_all = []
        count_all = 1
        for line in filelines_all:
            x_all = line.split(";")
            if len(x_all) == 2:
                x_all.append(" ")
            url_all = urlparse(x_all[0]).netloc
            new_url_all = url_all.replace("www.","")
            newline_all = [x_all[1], new_url_all, x_all[0], count_all, x_all[2]]
            recipes_all.append(newline_all)
            count_all += 1
            if count_all > 15:
                break
        readfile_all.close()
        recipes.append(recipes_all)
    rec_all = recipes[0]
    defaults = ['default01.png', 'default02.png', 'default03.png', 'default04.png', 'default05.png', 'default06.png', 'default07.png',
        'default08.png', 'default09.png', 'default10.png', 'default11.png', 'default12.png', 'default13.png', 'default14.png',
        'default15.png', 'default16.png', 'default17.png', 'default18.png', 'default19.png', 'default20.png', 'default21.png',
        'default22.png', 'default23.png', 'default24.png', 'default25.png', 'default26.png', 'default27.png']
    random.shuffle(defaults)
    default_photos = (defaults * (100 // len(defaults) + 1))[:100]
    form = ExploreSearchForm()
    if form.validate_on_submit():
        return redirect(url_for('explore.exploreSearch', query=form.search.data))
    return render_template('explore.html', title=_('Explore'),
        mdescription=_('Explore page allows you to browse and search a collection of over 100,000 recipes.'),
        rec_all=rec_all, form=form, default_photos=default_photos)

@bp.route('/explore/search')
@limiter.limit(Config.DEFAULT_RATE_LIMIT)
def exploreSearch():
    # the query, example is search?query=garlic+shrimp which translates to "garlic shrimp"
    query_string = request.args.get('query')
    # subset of all_recipes in which all parts of query string are present in title
    # it has 6 items per recipe: title, shortened url, full url, all_recipes count, photo url, recipes count
    recipes = []
    # 2D array of all recipes in explore-all-randomized.txt file
    # it has 5 items per recipe: title, shortened url, full url, all_recipes count, photo url
    all_recipes = []
    count = 1
    if query_string:
        readfile = open(app.root_path + "/static/explore-all-randomized.txt", "r")
        filelines = readfile.readlines()
        for line in filelines:
            x = line.split(";")
            if len(x) == 2:
                x.append(" ")
            url = urlparse(x[0]).netloc
            new_url = url.replace("www.","")
            newline = [x[1], new_url, x[0], count, x[2]]
            all_recipes.append(newline)
            count += 1
        readfile.close()
        query_items = query_string.split(" ")
        # rec_count is number of recipes in recipes array
        rec_count = 1
        for recipe in all_recipes:
            is_good = True
            for item in query_items:
                if item.lower() not in recipe[0].lower():
                    is_good = False
                    # Break out of inner loop if any item not found in query string, more efficient
                    break
            if is_good == True:
                new_rec = recipe
                # append 6th item (index of 5) to recipes, recipes count
                new_rec.append(rec_count)
                recipes.append(new_rec)
                rec_count += 1
    else:
        filelines = []
    PER_PAGE = app.config['EXPLORE_RECIPES_PER_PAGE']
    # if page parameter not present in query string, it defaults to 1, also converted to int
    page = request.args.get('page', 1, type=int)
    # curr_page is used to build urls for next and previous page in explore search template
    if page:
        curr_page = page
    else:
        curr_page = 1
    # i is the starting index for slicing the recipes list
    i=(page-1)*PER_PAGE
    # subset of recipes, recipes for current page
    recipes_page = recipes[i:i+PER_PAGE]
    # rec_first (x) and rec_last (y) are used for "showing x-y of z" in template
    if len(recipes_page) > 0:
        # make rec_first the recipe count (6th item of recipe) for first recipe on page
        try:
            rec_first = recipes_page[0]
            rec_first = rec_first[5]
        except:
            rec_first = 0
        # make rec_last the recipe count (6th item of recipe) for last recipe on page
        try:
            rec_last = recipes_page[len(recipes_page)-1]
            rec_last = rec_last[5]
        except:
            rec_last = 0
    # if no recipes on current page, set rec_first and rec_last to 0
    else:
        rec_first = 0
        rec_last = 0
    rec_count = len(recipes)
    pagination = Pagination(page=page, per_page=PER_PAGE, total=len(recipes), search=False, record_name='recipes')
    # Default photos are shuffled and displayed immediately on page load
    # Photos are later loaded client side from recipe websites and replace defaults upon successful loading
    defaults = ['default01.png', 'default02.png', 'default03.png', 'default04.png', 'default05.png', 'default06.png', 'default07.png',
        'default08.png', 'default09.png', 'default10.png', 'default11.png', 'default12.png', 'default13.png', 'default14.png',
        'default15.png', 'default16.png', 'default17.png', 'default18.png', 'default19.png', 'default20.png', 'default21.png',
        'default22.png', 'default23.png', 'default24.png', 'default25.png', 'default26.png', 'default27.png']
    random.shuffle(defaults)
    default_photos = (defaults * (100 // len(defaults) + 1))[:100]
    return render_template('explore-search.html', title=_('Explore Search'),
        mdescription=_('Search results for the Explore page, all matching recipes are shown here.'),
        recipes=recipes_page, pagination=pagination, curr_page=curr_page, page=page, rec_first=rec_first, rec_last=rec_last,
        rec_count=rec_count, query_string=query_string, default_photos=default_photos)

@bp.route('/explore/group/<group>')
@limiter.limit(Config.DEFAULT_RATE_LIMIT)
def exploreGroup(group):
    if group == "all":
        group_title = _('All Recipes 🍽️')
        readfile = open(app.root_path + "/static/explore-all-randomized.txt", "r")
    elif group == "30-minute":
        group_title = _('30 Minute')
        readfile = open(app.root_path + "/static/explore-30minute-randomized.txt", "r")
    elif group == "air-fryer":
        group_title = _('Air Fryer')
        readfile = open(app.root_path + "/static/explore-airfryer-randomized.txt", "r")
    elif group == "beef":
        group_title = _('Beef')
        readfile = open(app.root_path + "/static/explore-beef-randomized.txt", "r")
    elif group == "breakfast":
        group_title = _('Breakfast')
        readfile = open(app.root_path + "/static/explore-breakfast-randomized.txt", "r")
    elif group == "chicken":
        group_title = _('Chicken')
        readfile = open(app.root_path + "/static/explore-chicken-randomized.txt", "r")
    elif group == "dessert":
        group_title = _('Dessert')
        readfile = open(app.root_path + "/static/explore-dessert-randomized.txt", "r")
    elif group == "dinner":
        group_title = _('Dinner')
        readfile = open(app.root_path + "/static/explore-dinner-randomized.txt", "r")
    elif group == "drinks":
        group_title = _('Drinks')
        readfile = open(app.root_path + "/static/explore-drinks-randomized.txt", "r")
    elif group == "low-carb":
        group_title = _('Low Carb')
        readfile = open(app.root_path + "/static/explore-lowcarb-randomized.txt", "r")
    elif group == "lunch":
        group_title = _('Lunch')
        readfile = open(app.root_path + "/static/explore-lunch-randomized.txt", "r")
    elif group == "salads":
        group_title = _('Salads')
        readfile = open(app.root_path + "/static/explore-salads-randomized.txt", "r")
    elif group == "seafood":
        group_title = _('Seafood')
        readfile = open(app.root_path + "/static/explore-seafood-randomized.txt", "r")
    elif group == "slow-cooker":
        group_title = _('Slow Cooker')
        readfile = open(app.root_path + "/static/explore-slowcooker-randomized.txt", "r")
    elif group == "snacks":
        group_title = _('Snacks')
        readfile = open(app.root_path + "/static/explore-snacks-randomized.txt", "r")
    elif group == "soup":
        group_title = _('Soup')
        readfile = open(app.root_path + "/static/explore-soup-randomized.txt", "r")
    elif group == "vegetarian":
        group_title = _('Vegetarian')
        readfile = open(app.root_path + "/static/explore-vegetarian-randomized.txt", "r")
    else:
        group_title = _('Error')
        readfile = open(app.root_path + "/static/explore-blank.txt", "r")
    filelines = readfile.readlines()
    recipes = []
    count = 1
    if len(filelines) > 2:
        for line in filelines:
            x = line.split(";")
            if len(x) == 2:
                x.append(" ")
            url = urlparse(x[0]).netloc
            new_url = url.replace("www.","")
            newline = [x[1], new_url, x[0], count, x[2]]
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
        try:
            rec_first = recipes_page[0]
            rec_first = rec_first[3]
        except:
            rec_first = 0
        try:
            rec_last = recipes_page[len(recipes_page)-1]
            rec_last = rec_last[3]
        except:
            rec_last = 0
    else:
        rec_first = 0
        rec_last = 0
    rec_count = len(recipes)
    pagination = Pagination(page=page, per_page=PER_PAGE, total=len(recipes), search=False, record_name='recipes')
    # Default photos are shuffled and displayed immediately on page load
    # Photos are later loaded client side from recipe websites and replace defaults upon successful loading
    defaults = ['default01.png', 'default02.png', 'default03.png', 'default04.png', 'default05.png', 'default06.png', 'default07.png',
        'default08.png', 'default09.png', 'default10.png', 'default11.png', 'default12.png', 'default13.png', 'default14.png',
        'default15.png', 'default16.png', 'default17.png', 'default18.png', 'default19.png', 'default20.png', 'default21.png',
        'default22.png', 'default23.png', 'default24.png', 'default25.png', 'default26.png', 'default27.png']
    random.shuffle(defaults)
    default_photos = (defaults * (100 // len(defaults) + 1))[:100]
    return render_template('explore-group.html', title=group_title, mdescription=_('All recipes are listed for the selected Explore category.'),
        recipes=recipes_page, pagination=pagination, group=group, group_title=group_title, curr_page=curr_page, rec_first=rec_first,
        rec_last=rec_last, rec_count=rec_count, default_photos=default_photos)

# Functions for parsing data from WP Recipe Maker Wordpress plugin
# Used by exploreRecipeDetail route
def get_wprm_servings(soup):
    servings_1 = soup.find('span',class_='wprm-recipe-servings-with-unit')
    try:
        servings_2 = servings_1.find('span',class_='wprm-recipe-servings')
    except:
        servings_2 = None
    if servings_2:
        servings = servings_2.get_text()
        try:
            servings = int(servings)
        except ValueError:
            servings = None
    else:
        servings = None
    return servings
def get_wprm_calories(soup):
    calories_1 = soup.find('span',class_='wprm-nutrition-label-text-nutrition-container-calories')
    try:
        calories_2 = calories_1.find('span',class_='wprm-nutrition-label-text-nutrition-value')
    except:
        calories_2 = None
    if calories_2:
        calories = calories_2.get_text()
        try:
            calories = int(round(float(calories)))
        except ValueError:
            calories = None
    else:
        calories = None
    return calories
def get_wprm_carbs(soup):
    carbs_1 = soup.find('span',class_='wprm-nutrition-label-text-nutrition-container-carbohydrates')
    try:
        carbs_2 = carbs_1.find('span',class_='wprm-nutrition-label-text-nutrition-value')
    except:
        carbs_2 = None
    if carbs_2:
        carbs = carbs_2.get_text()
        try:
            carbs = int(round(float(carbs)))
        except ValueError:
            carbs = None
    else:
        carbs = None
    return carbs    
def get_wprm_protein(soup):
    protein_1 = soup.find('span',class_='wprm-nutrition-label-text-nutrition-container-protein')
    try:
        protein_2 = protein_1.find('span',class_='wprm-nutrition-label-text-nutrition-value')
    except:
        protein_2 = None
    if protein_2:
        protein = protein_2.get_text()
        try:
            protein = int(round(float(protein)))
        except ValueError:
            protein = None
    else:
        protein = None
    return protein
def get_wprm_fat(soup):
    fat_1 = soup.find('span',class_='wprm-nutrition-label-text-nutrition-container-fat')
    try:
        fat_2 = fat_1.find('span',class_='wprm-nutrition-label-text-nutrition-value')
    except:
        fat_2 = None
    if fat_2:
        fat = fat_2.get_text()
        try:
            fat = int(round(float(fat)))
        except ValueError:
            fat = None
    else:
        fat = None
    return fat
def get_wprm_sugar(soup):
    sugar_1 = soup.find('span',class_='wprm-nutrition-label-text-nutrition-container-sugar')
    try:
        sugar_2 = sugar_1.find('span',class_='wprm-nutrition-label-text-nutrition-value')
    except:
        sugar_2 = None
    if sugar_2:
        sugar = sugar_2.get_text()
        try:
            sugar = int(round(float(sugar)))
        except ValueError:
            sugar = None
    else:
        sugar = None
    return sugar
def get_wprm_cholesterol(soup):
    cholesterol_1 = soup.find('span',class_='wprm-nutrition-label-text-nutrition-container-cholesterol')
    try:
        cholesterol_2 = cholesterol_1.find('span',class_='wprm-nutrition-label-text-nutrition-value')
    except:
        cholesterol_2 = None
    if cholesterol_2:
        cholesterol = cholesterol_2.get_text()
        try:
            cholesterol = int(round(float(cholesterol)))
        except ValueError:
            cholesterol = None
    else:
        cholesterol = None
    return cholesterol
def get_wprm_sodium(soup):
    sodium_1 = soup.find('span',class_='wprm-nutrition-label-text-nutrition-container-sodium')
    try:
        sodium_2 = sodium_1.find('span',class_='wprm-nutrition-label-text-nutrition-value')
    except:
        sodium_2 = None
    if sodium_2:
        sodium = sodium_2.get_text()
        try:
            sodium = int(round(float(sodium)))
        except ValueError:
            sodium = None
    else:
        sodium = None
    return sodium
def get_wprm_fiber(soup):
    fiber_1 = soup.find('span',class_='wprm-nutrition-label-text-nutrition-container-fiber')
    try:
        fiber_2 = fiber_1.find('span',class_='wprm-nutrition-label-text-nutrition-value')
    except:
        fiber_2 = None
    if fiber_2:
        fiber = fiber_2.get_text()
        try:
            fiber = int(round(float(fiber)))
        except ValueError:
            fiber = None
    else:
        fiber = None
    return fiber
def get_wprm_preptime(soup):
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
    return preptime
def get_wprm_cooktime(soup):
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
    return cooktime
def get_wprm_totaltime(soup):
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
    return totaltime
def get_wprm_description(soup):
    description_1 = soup.find('div',class_='wprm-recipe-summary wprm-block-text-normal')
    if description_1:
        description = description_1.text
    else:
        description = ''
    return description
def get_wprm_ingredients(soup):
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
    return ingredients
def get_wprm_instructions(soup):
    instructions = []
    instructions_1 = soup.find('div',class_='wprm-recipe-instructions-container')
    if instructions_1:
        instructions_2 = instructions_1.find_all('div',class_='wprm-recipe-instruction-group')
        for group in instructions_2:
            instructions_h4 = group.find('h4')
            if instructions_h4:
                content = str(instructions_h4.contents[0])
                try:
                    content = content.replace("<strong>","")
                    content = content.replace("</strong>","")
                except:
                    pass
                instructions.append(content)
            inst_steps = group.find_all('div',class_='wprm-recipe-instruction-text')
            for step in inst_steps:
                inst_step = str(step.text)
                try:
                    inst_step = inst_step.replace("<strong>","")
                    inst_step = inst_step.replace("</strong>","")
                except:
                    pass
                instructions.append(inst_step)
    return instructions

@bp.route('/explore/recipe/<rec_group>/<recnum>', methods=['GET', 'POST'])
@limiter.limit(Config.DEFAULT_RATE_LIMIT)
def exploreRecipeDetail(rec_group, recnum):
    if rec_group == "all":
        readfile = open(app.root_path + '/static/explore-all-randomized.txt', "r")
    elif rec_group == "30-minute":
        readfile = open(app.root_path + '/static/explore-30minute-randomized.txt', "r")
    elif rec_group == "air-fryer":
        readfile = open(app.root_path + '/static/explore-airfryer-randomized.txt', "r")
    elif rec_group == "beef":
        readfile = open(app.root_path + '/static/explore-beef-randomized.txt', "r")
    elif rec_group == "breakfast":
        readfile = open(app.root_path + '/static/explore-breakfast-randomized.txt', "r")
    elif rec_group == "chicken":
        readfile = open(app.root_path + '/static/explore-chicken-randomized.txt', "r")
    elif rec_group == "dessert":
        readfile = open(app.root_path + '/static/explore-dessert-randomized.txt', "r")
    elif rec_group == "dinner":
        readfile = open(app.root_path + '/static/explore-dinner-randomized.txt', "r")
    elif rec_group == "drinks":
        readfile = open(app.root_path + '/static/explore-drinks-randomized.txt', "r")
    elif rec_group == "low-carb":
        readfile = open(app.root_path + '/static/explore-lowcarb-randomized.txt', "r")
    elif rec_group == "lunch":
        readfile = open(app.root_path + '/static/explore-lunch-randomized.txt', "r")
    elif rec_group == "salads":
        readfile = open(app.root_path + '/static/explore-salads-randomized.txt', "r")
    elif rec_group == "seafood":
        readfile = open(app.root_path + '/static/explore-seafood-randomized.txt', "r")
    elif rec_group == "slow-cooker":
        readfile = open(app.root_path + '/static/explore-slowcooker-randomized.txt', "r")
    elif rec_group == "snacks":
        readfile = open(app.root_path + '/static/explore-snacks-randomized.txt', "r")
    elif rec_group == "soup":
        readfile = open(app.root_path + '/static/explore-soup-randomized.txt', "r")
    elif rec_group == "vegetarian":
        readfile = open(app.root_path + '/static/explore-vegetarian-randomized.txt', "r")
    else:
        readfile = open(app.root_path + '/static/explore-blank.txt', "r")
    filelines = readfile.readlines()
    lines = []
    if len(filelines) > 2:
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
    # List of wprm sites that can be parsed using get_wprm functions, checked with elif statement below
    wprm_sites = ["wellplated.com", "fedandfit.com", "damndelicious.net", "recipetineats.com", "skinnytaste.com",
        "therecipecritic.com", "spendwithpennies.com", "bellyfull.net", "iheartnaptime.net", "daringgourmet.com",
        "lifemadesweeter.com", "iambaker.net", "tastesoflizzyt.com", "thebestblogrecipes.com",
        "favfamilyrecipes.com", "feelgoodfoodie.net", "vegrecipesofindia.com", "theseasonedmom.com",
        "keviniscooking.com", "isabeleats.com", "bakerbynature.com", "minimalistbaker.com",
        "dinneratthezoo.com", "lecremedelacrumb.com", "gonnawantseconds.com", "lilluna.com", "joyfoodsunshine.com",
        "paleorunningmomma.com", "themediterraneandish.com", "deliciousasitlooks.com", "thestayathomechef.com",
        "barefeetinthekitchen.com", "addapinch.com", "thecafesucrefarine.com", "iamhomesteader.com",
        "handletheheat.com", "sipandfeast.com", "askchefdennis.com", "noracooks.com", "greedygirlgourmet.com",
        "thereciperebel.com"]
    # Site specific parsing
    if "cookinglsl.com" in rec_url:
        try:
            page = requests.get(rec_url, timeout=16)
            soup = BeautifulSoup(page.text, 'html.parser')
        except:
            page = None
            soup = BeautifulSoup('<html><body></body></html>', 'html.parser')
        photo_1 = soup.find('div',class_='wprm-recipe-image')
        photo_2 = photo_1.find('img')
        photo = photo_2['data-lazy-src']
        # Assign Servings to integer variable if it is listed on page
        servings_1 = soup.find('span',class_='wprm-recipe-servings-adjustable-tooltip')
        if servings_1:
            servings = servings_1.get_text()
            try:
                servings = int(servings)
            except ValueError:
                servings = None
        else:
            servings = None
        # Assign Nutrition Facts to integer variables if listed on page
        calories = get_wprm_calories(soup)
        carbs = get_wprm_carbs(soup)
        protein = get_wprm_protein(soup)
        fat = get_wprm_fat(soup)
        sugar = get_wprm_sugar(soup)
        cholesterol = get_wprm_cholesterol(soup)
        sodium = get_wprm_sodium(soup)
        fiber = get_wprm_fiber(soup)
        # Extract prep time, cook time, total time
        preptime = get_wprm_preptime(soup)
        cooktime = get_wprm_cooktime(soup)
        totaltime = get_wprm_totaltime(soup)
        description = get_wprm_description(soup)
        ingredients = get_wprm_ingredients(soup)
        instructions = get_wprm_instructions(soup)
    elif "lanascooking.com" in rec_url:
        try:
            page = requests.get(rec_url, timeout=16)
            soup = BeautifulSoup(page.text, 'html.parser')
        except:
            page = None
            soup = BeautifulSoup('<html><body></body></html>', 'html.parser')
        photo_1 = soup.find('img',class_='attachment-full size-full wp-post-image perfmatters-lazy')
        if photo_1:
            photo = photo_1['data-src']
        else:
            photo = ''
        # Assign Servings to integer variable if it is listed on page
        servings = get_wprm_servings(soup)
        # Assign Nutrition Facts to integer variables if listed on page
        calories = get_wprm_calories(soup)
        carbs = get_wprm_carbs(soup)
        protein = get_wprm_protein(soup)
        fat = get_wprm_fat(soup)
        sugar = get_wprm_sugar(soup)
        cholesterol = get_wprm_cholesterol(soup)
        sodium = get_wprm_sodium(soup)
        fiber = get_wprm_fiber(soup)
        # Extract prep time, cook time, total time
        preptime = get_wprm_preptime(soup)
        cooktime = get_wprm_cooktime(soup)
        totaltime = get_wprm_totaltime(soup)
        description_1 = soup.find('meta',attrs={"property": "og:description"})
        if description_1:
            description = description_1['content']
        else:
            description = ''
        ingredients = get_wprm_ingredients(soup)
        instructions = get_wprm_instructions(soup)
    elif "justapinch.com" in rec_url:
        try:
            page = requests.get(rec_url, timeout=16)
            soup = BeautifulSoup(page.text, 'html.parser')
        except:
            page = None
            soup = BeautifulSoup('<html><body></body></html>', 'html.parser')
        photo_1 = soup.find('div',class_='photo-aspect-container')
        if photo_1:
            photo_2 = photo_1.find('img')
            photo = photo_2['src']
        else:
            photo = ''
        # Assign Servings to integer variable if it is listed on page
        servings_1 = soup.find('span', class_='small text-uppercase', string='yield')
        if servings_1:
            servings_2 = servings_1.find_next_siblings('span')
            servings_3 = servings_2[0].text
            servings = servings_3.replace(' serving(s)', '').replace('serving', '').strip()
            try:
                servings = int(servings)
            except ValueError:
                servings = None
        else:
            servings = None
        # This site does not list Nutrition Facts so assign None to each variable
        calories = None
        carbs = None
        protein = None
        fat = None
        sugar = None
        cholesterol = None
        sodium = None
        fiber = None
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
    elif "pinchofyum.com" in rec_url:
        try:
            page = requests.get(rec_url, timeout=16)
            soup = BeautifulSoup(page.text, 'html.parser')
        except:
            page = None
            soup = BeautifulSoup('<html><body></body></html>', 'html.parser')
        photo_1 = soup.find('meta',attrs={"property": "og:image"})
        if photo_1:
            photo = photo_1['content']
        else:
            photo = ''
        # Assign Servings to integer variable if it is listed on page
        servings_1 = soup.find('span',class_='tasty-recipes-yeild')
        if servings_1:
            servings_2 = servings_1.find('span', attrs={'data-amount': True})
            servings = servings_2[0].text
            try:
                servings = int(servings)
            except ValueError:
                servings = None
        else:
            servings = None
        # This site does list Nutrition Facts as float (not int) with units in same span
        # Too difficult to extract, so pass for this site
        calories = None
        carbs = None
        protein = None
        fat = None
        sugar = None
        cholesterol = None
        sodium = None
        fiber = None
        # Extract prep time, cook time, total time
        preptime_1 = soup.find('span', class_='tasty-recipes-prep-time')
        if preptime_1:
            preptime_2 = preptime_1.text
            # Extract all numbers
            preptime_3 = re.findall(r'\d+', preptime_2)
            try:
                preptime = int(preptime_3[0])
            except:
                preptime = ''
        else:
            preptime = ''
        cooktime_1 = soup.find('span', class_='tasty-recipes-cook-time')
        if cooktime_1:
            cooktime_2 = cooktime_1.text
            # Extract all numbers
            cooktime_3 = re.findall(r'\d+', cooktime_2)
            try:
                cooktime = int(cooktime_3[0])
            except:
                cooktime = ''
        else:
            cooktime = ''
        if preptime and cooktime:
            totaltime = preptime + cooktime
        else:
            totaltime = ''
        # Extract description
        description_1 = soup.find('meta',attrs={"name": "description"})
        if description_1:
            description = description_1['content']
        else:
            description = ''
        # Extract ingredients and instructions
        ingredients = []
        ingredients_1 = soup.find_all('li',attrs={'data-tr-ingredient-checkbox': True})
        if ingredients_1:
            for ingredient in ingredients_1:
                ingred = ingredient.text
                ingred = ingred.strip()
                ingredients.append(ingred)
        instructions = []
        instructions_1 = soup.find('div',class_='tasty-recipes-instructions')
        if instructions_1:
            instructions_2 = instructions_1.find_all('li')
            for instruction in instructions_2:
                instr = instruction.text
                instr = instr.strip()
                instructions.append(instr)
    elif "tasty.co" in rec_url:
        try:
            page = requests.get(rec_url, timeout=16)
            soup = BeautifulSoup(page.text, 'html.parser')
        except:
            page = None
            soup = BeautifulSoup('<html><body></body></html>', 'html.parser')
        photo_1 = soup.find('meta',attrs={"property": "og:image"})
        if photo_1:
            photo = photo_1['content']
        else:
            photo = ''
        # Assign Servings to integer variable if it is listed on page
        servings_1 = soup.find('p',class_='servings-display')
        if servings_1:
            servings = servings_1.text
            servings = servings.replace('for', '').replace('servings', '').replace('serving', '').replace(' ', '').strip()
            try:
                servings = int(servings)
            except ValueError:
                servings = None
        else:
            servings = None
        # This site does not list Nutrition Facts so assign None to each variable
        calories = None
        carbs = None
        protein = None
        fat = None
        sugar = None
        cholesterol = None
        sodium = None
        fiber = None
        # Almost all recipes don't have times so pass on extracting
        preptime = ''
        cooktime = ''
        totaltime = ''
        # Extract description
        description_1 = soup.find('meta',attrs={"name": "description"})
        if description_1:
            description = description_1['content']
            description = description[:500]
            description = description.replace('&#x27;', '')
        else:
            description = ''
        # Extract ingredients and instructions
        ingredients = []
        ingredients_1 = soup.find('div',class_='ingredients__section')
        if ingredients_1:
            ingredients_2 = ingredients_1.find_all('li',class_='ingredient')
            for ingredient in ingredients_2:
                ingred = ingredient.text
                ingred = ingred.strip()
                ingredients.append(ingred)
        instructions = []
        instructions_1 = soup.find('ol',class_='prep-steps')
        if instructions_1:
            instructions_2 = instructions_1.find_all('li')
            for instruction in instructions_2:
                instr = instruction.text
                instr = instr.strip()
                instructions.append(instr)
    elif "food52.com" in rec_url:
        try:
            page = requests.get(rec_url, timeout=16)
            soup = BeautifulSoup(page.text, 'html.parser')
        except:
            page = None
            soup = BeautifulSoup('<html><body></body></html>', 'html.parser')
        photo_1 = soup.find('meta',attrs={"property": "og:image"})
        if photo_1:
            photo = photo_1['content']
        else:
            photo = ''
        # Assign Servings to integer variable if it is listed on page
        servings_1 = soup.find('span',class_='recipe__details-heading', text='Serves')
        if servings_1:
            servings = servings_1.parent
            servings = servings.text
            servings = servings.replace('Serves', '').replace(' ', '').strip()
            servings = re.match(r'\d+', servings)
            servings = servings.group() if servings else None
            try:
                servings = int(servings)
            except:
                servings = None
        else:
            servings = None
        # This site does not list Nutrition Facts so assign None to each variable
        calories = None
        carbs = None
        protein = None
        fat = None
        sugar = None
        cholesterol = None
        sodium = None
        fiber = None
        # Extract prep time, cook time, total time
        preptime_1 = soup.find('span',class_='recipe__details-heading', text='Prep time')
        if preptime_1:
            preptime = preptime_1.parent
            preptime = preptime.text
            preptime = preptime.replace('Prep time', '').replace('minutes', '').replace('minute', '').replace(' ', '').strip()
            preptime = re.match(r'\d+', preptime)
            preptime = preptime.group() if preptime else None
            try:
                preptime = int(preptime)
            except:
                preptime = ''
        else:
            preptime = ''
        cooktime_1 = soup.find('span',class_='recipe__details-heading', text='Cook time')
        if cooktime_1:
            cooktime = cooktime_1.parent
            cooktime = cooktime.text
            cooktime = cooktime.replace('Cook time', '').replace('minutes', '').replace('minute', '').replace(' ', '').strip()
            cooktime = re.match(r'\d+', cooktime)
            cooktime = cooktime.group() if cooktime else None
            try:
                cooktime = int(cooktime)
            except:
                cooktime = ''
        else:
            cooktime = ''
        if preptime and cooktime:
            totaltime = preptime + cooktime
        else:
            totaltime = ''
        # Extract description
        description_1 = soup.find('meta',attrs={"name": "description"})
        if description_1:
            description = description_1['content']
            description = description[:500]
        else:
            description = ''
        # Extract ingredients and instructions
        ingredients = []
        ingredients_1 = soup.find('div',class_='recipe__list--ingredients')
        if ingredients_1:
            ingredients_2 = ingredients_1.find_all('li')
            for ingredient in ingredients_2:
                ingred = ingredient.text
                ingred = ingred.replace('\n\n', ' ').replace('\n', ' ')
                ingred = ingred.strip()
                ingredients.append(ingred)
        instructions = []
        instructions_1 = soup.find('div',class_='recipe__list--steps')
        if instructions_1:
            instructions_2 = instructions_1.find_all('li',class_='recipe__list-step')
            for instruction in instructions_2:
                instr = instruction.text
                instr = instr.strip()
                instructions.append(instr)
    elif "tasteofhome.com" in rec_url:
        headers = {
            'User-Agent': UserAgent().random,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        }
        try:
            page = requests.get(rec_url, timeout=16, headers=headers)
            soup = BeautifulSoup(page.text, 'html.parser')
        except:
            page = None
            soup = BeautifulSoup('<html><body></body></html>', 'html.parser')
        photo_1 = soup.find('meta',attrs={"property": "og:image"})
        if photo_1:
            photo = photo_1['content']
        else:
            photo = ''
        # Assign Servings to integer variable if it is listed on page
        servings_1 = soup.find('div',class_='makes')
        if servings_1:
            servings = servings_1.find('p')
            servings = servings.text
            servings = servings.replace('servings', '').replace('serving', '').replace(' ', '').strip()
            try:
                servings = int(servings)
            except:
                servings = None
        else:
            servings = None
        # Extract Nutrition Facts
        nutrition_1 = soup.find('div',class_='recipe-nutrition-facts')
        if nutrition_1:
            nutrition_1 = nutrition_1.text
            calories = re.search(r'(\d+) calories', nutrition_1)
            calories = calories.group(1) if calories else None
            try:
                calories = int(calories)
            except:
                calories = None
            carbs = re.search(r'(\d+)(?:g)? carbohydrate', nutrition_1)
            carbs = carbs.group(1) if carbs else None
            try:
                carbs = int(carbs)
            except:
                carbs = None
            protein = re.search(r'(\d+)(?:g)? protein', nutrition_1)
            protein = protein.group(1) if protein else None
            try:
                protein = int(protein)
            except:
                protein = None
            fat = re.search(r'(\d+)(?:g)? fat', nutrition_1)
            fat = fat.group(1) if fat else None
            try:
                fat = int(fat)
            except:
                fat = None
            sugar = re.search(r'(\d+)(?:g)? sugars', nutrition_1)
            sugar = sugar.group(1) if sugar else None
            try:
                sugar = int(sugar)
            except:
                sugar = None
            cholesterol = re.search(r'(\d+)(?:mg)? cholesterol', nutrition_1)
            cholesterol = cholesterol.group(1) if cholesterol else None
            try:
                cholesterol = int(cholesterol)
            except:
                cholesterol = None
            sodium = re.search(r'(\d+)(?:mg)? sodium', nutrition_1)
            sodium = sodium.group(1) if sodium else None
            try:
                sodium = int(sodium)
            except:
                sodium = None
            fiber = re.search(r'(\d+)(?:g)? fiber', nutrition_1)
            fiber = fiber.group(1) if fiber else None
            try:
                fiber = int(fiber)
            except:
                fiber = None
        else:
            calories = None
            carbs = None
            protein = None
            fat = None
            sugar = None
            cholesterol = None
            sodium = None
            fiber = None
        # Only total time is listed and it is not consistent text, so pass on parsing times
        preptime = ''
        cooktime = ''
        totaltime = ''
        # Extract description
        description_1 = soup.find('div',class_='recipe-tagline__text')
        if description_1:
            description = description_1.text
            description = description[:500]
        else:
            description = ''
        # Extract ingredients and instructions
        ingredients = []
        ingredients_1 = soup.find('ul',class_='recipe-ingredients__list')
        if ingredients_1:
            ingredients_2 = ingredients_1.find_all('li')
            for ingredient in ingredients_2:
                ingred = ingredient.text
                ingred = ingred.strip()
                ingredients.append(ingred)
        instructions = []
        instructions_1 = soup.find('ol',class_='recipe-directions__list')
        if instructions_1:
            instructions_2 = instructions_1.find_all('li')
            for instruction in instructions_2:
                instr = instruction.text
                instr = instr.strip()
                instructions.append(instr)
    elif "taste.com.au" in rec_url:
        headers = {
            'User-Agent': UserAgent().random,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        }
        try:
            page = requests.get(rec_url, timeout=16, headers=headers)
            soup = BeautifulSoup(page.text, 'html.parser')
        except:
            page = None
            soup = BeautifulSoup('<html><body></body></html>', 'html.parser')
        photo_1 = soup.find('meta',attrs={"property": "og:image"})
        if photo_1:
            photo = photo_1['content']
        else:
            photo = ''
        # Assign Servings to integer variable if it is listed on page
        servings_1 = soup.find('li', text='Serves')
        if servings_1:
            servings = servings_1.find('span')
            servings = servings.text
            try:
                servings = int(servings)
            except:
                servings = None
        else:
            servings = None
        # This site does not list Nutrition Facts so assign None to each variable
        calories = None
        carbs = None
        protein = None
        fat = None
        sugar = None
        cholesterol = None
        sodium = None
        fiber = None
        # Times not extracted due to difficulty with finding lis with Beautiful Soup
        preptime = ''
        cooktime = ''
        totaltime = ''
        # Extract description
        try:
            description_1 = soup.find('div',class_='single-asset-description-block').find('div',class_='ellipsis-applied').find('p')
        except:
            try:
                description_1 = soup.find('div',class_='single-asset-description-block').find('div',class_='read-more').find('p')
            except:
                try:
                    description_1 = soup.find('div',class_='single-asset-description-block').find('div',class_='read-more')
                except:
                    description_1 = None
        if description_1:
            description = description_1.text
            description = description[:500]
        else:
            description = ''
        # Extract ingredients and instructions
        ingredients = []
        ingredients_1 = soup.find('div',class_='recipe-ingredients-section')
        if ingredients_1:
            ingredients_2 = ingredients_1.find_all('div',class_='ingredient-description')
            for ingredient in ingredients_2:
                ingred = ingredient.text
                ingred = ingred.strip()
                ingredients.append(ingred)
        instructions = []
        instructions_1 = soup.find('ul',class_='recipe-method-steps')
        if instructions_1:
            instructions_2 = instructions_1.find_all('div',class_='recipe-method-step-content')
            for instruction in instructions_2:
                instr = instruction.text
                instr = instr.strip()
                instructions.append(instr)
    elif "damndelicious.net" in rec_url:
        scraper = cloudscraper.create_scraper()
        try:
            page = scraper.get(rec_url, timeout=16)
            soup = BeautifulSoup(page.text, 'html.parser')
        except:
            page = None
            soup = BeautifulSoup('<html><body></body></html>', 'html.parser')
        photo_1 = soup.find('meta',attrs={"property": "og:image"})
        if photo_1:
            photo = photo_1['content']
        else:
            photo = ''
        # Assign Servings to integer variable if it is listed on page
        servings = get_wprm_servings(soup)
        # Assign Nutrition Facts to integer variables if listed on page
        calories = get_wprm_calories(soup)
        carbs = get_wprm_carbs(soup)
        protein = get_wprm_protein(soup)
        fat = get_wprm_fat(soup)
        sugar = get_wprm_sugar(soup)
        cholesterol = get_wprm_cholesterol(soup)
        sodium = get_wprm_sodium(soup)
        fiber = get_wprm_fiber(soup)
        # Extract prep time, cook time, total time
        preptime = get_wprm_preptime(soup)
        cooktime = get_wprm_cooktime(soup)
        totaltime = get_wprm_totaltime(soup)
        # Extract description
        description = get_wprm_description(soup)
        # Extract ingredients and instructions
        ingredients = get_wprm_ingredients(soup)
        instructions = get_wprm_instructions(soup)
    elif "easypeasyfoodie.com" in rec_url:
        scraper = cloudscraper.create_scraper()
        try:
            page = scraper.get(rec_url, timeout=16)
            soup = BeautifulSoup(page.text, 'html.parser')
        except:
            page = None
            soup = BeautifulSoup('<html><body></body></html>', 'html.parser')
        photo_1 = soup.find('meta',attrs={"property": "og:image"})
        if photo_1:
            photo = photo_1['content']
        else:
            photo = ''
        # Assign Servings to integer variable if it is listed on page
        servings = get_wprm_servings(soup)
        # Assign Nutrition Facts to integer variables if listed on page
        calories = get_wprm_calories(soup)
        carbs = get_wprm_carbs(soup)
        protein = get_wprm_protein(soup)
        fat = get_wprm_fat(soup)
        sugar = get_wprm_sugar(soup)
        cholesterol = get_wprm_cholesterol(soup)
        sodium = get_wprm_sodium(soup)
        fiber = get_wprm_fiber(soup)
        # Extract prep time, cook time, total time
        preptime = get_wprm_preptime(soup)
        cooktime = get_wprm_cooktime(soup)
        totaltime = get_wprm_totaltime(soup)
        # Extract description
        description = get_wprm_description(soup)
        # Extract ingredients and instructions
        ingredients = get_wprm_ingredients(soup)
        instructions = []
        # Find the main container for instructions
        instructions_container = soup.find('div', class_='wprm-recipe-instructions-container')
        if instructions_container:
            instruction_groups = instructions_container.find_all('div', class_='wprm-recipe-instruction-group')
            for group in instruction_groups:
                # Find all instruction list items within the group
                instruction_steps = group.find_all('li', class_='wprm-recipe-instruction')
                for step in instruction_steps:
                    # Extract the instruction text
                    instruction_text = step.find('div', class_='wprm-recipe-instruction-text')
                    if instruction_text:
                        # If there are nested <span> tags, extract their text
                        span = instruction_text.find('span')
                        if span:
                            instructions.append(span.text.strip())
                        else:
                            instructions.append(instruction_text.text.strip())
    elif any(link in rec_url for link in wprm_sites):
        headers = {
            'User-Agent': UserAgent().random,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        }
        try:
            page = requests.get(rec_url, timeout=16, headers=headers)
            soup = BeautifulSoup(page.text, 'html.parser')
        except:
            page = None
            soup = BeautifulSoup('<html><body></body></html>', 'html.parser')
        photo_1 = soup.find('meta',attrs={"property": "og:image"})
        if photo_1:
            photo = photo_1['content']
        else:
            photo = ''
        # Assign Servings to integer variable if it is listed on page
        servings = get_wprm_servings(soup)
        # Assign Nutrition Facts to integer variables if listed on page
        calories = get_wprm_calories(soup)
        carbs = get_wprm_carbs(soup)
        protein = get_wprm_protein(soup)
        fat = get_wprm_fat(soup)
        sugar = get_wprm_sugar(soup)
        cholesterol = get_wprm_cholesterol(soup)
        sodium = get_wprm_sodium(soup)
        fiber = get_wprm_fiber(soup)
        # Extract prep time, cook time, total time
        preptime = get_wprm_preptime(soup)
        cooktime = get_wprm_cooktime(soup)
        totaltime = get_wprm_totaltime(soup)
        # Extract description
        description = get_wprm_description(soup)
        # Extract ingredients and instructions
        ingredients = get_wprm_ingredients(soup)
        instructions = get_wprm_instructions(soup)
    # If website is not implemented we will display parse failure error on page
    else:
        page = None
        preptime = ''
        cooktime = ''
        totaltime = ''
        description = ''
        photo = ''
        servings = None
        calories = None
        carbs = None
        protein = None
        fat = None
        sugar = None
        cholesterol = None
        sodium = None
        fiber = None
        ingredients = []
        instructions = []
    if calories or carbs or protein or fat or sugar or cholesterol or sodium or fiber:
        nutrition = True
    else:
        nutrition = False
    # Populate responsecode variable which is used with Explore Recipe Detail Debug template
    if page:
        responsecode = page
    else:
        responsecode = None
    # Load recipe photo server side, compress it, base64 encode it, and assign to "photo_server" variable
    # This avoids the issue of resource blocking when trying to load images client side (cross-site)
    if photo:
        try:
            headers = {
                'User-Agent': UserAgent().random,
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Accept-Encoding': 'gzip, deflate',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
            }
            image_response = requests.get(photo, headers=headers)
            image_response.raise_for_status()  # Raise an exception for non-2xx status codes
            image_data = image_response.content

            # Open the image data with Pillow to detect format
            image_opened = Image.open(io.BytesIO(image_data))

            # Determine image format
            image_format = image_opened.format

            # Compress the image
            compressed_image_buffer = io.BytesIO()
            image_opened.save(compressed_image_buffer, format=image_format, optimize=True, quality=70)
            compressed_image_data = compressed_image_buffer.getvalue()

            base64_image = base64.b64encode(compressed_image_data).decode('utf-8')
            if image_format == 'JPEG':
                photo_server = f"data:image/jpeg;base64,{base64_image}"
            elif image_format == 'PNG':
                photo_server = f"data:image/png;base64,{base64_image}"
            else:
                raise ValueError("Unsupported image format")
        except:
            photo_server = None
    else:
        photo_server = None
    form = EmptyForm()
    # Save recipe to My Recipes
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
                    try:
                        test_photo_1 = Request(photo, headers={'User-Agent': 'Mozilla/5.0'})
                        test_photo_2 = urlopen(test_photo_1)
                        ext = test_photo_2.info()['Content-Type'].split("/")[-1]
                    except:
                        ext = None
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
                    headers = {
                        'User-Agent': UserAgent().random,
                        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                        'Accept-Language': 'en-US,en;q=0.5',
                        'Accept-Encoding': 'gzip, deflate',
                        'Connection': 'keep-alive',
                        'Upgrade-Insecure-Requests': '1',
                    }
                    r = requests.get(photo, headers=headers)
                    with open(app.config['UPLOAD_FOLDER'] + '/' + i_photo, 'wb') as outfile:
                        outfile.write(r.content)
                    img = Image.open(app.config['UPLOAD_FOLDER'] + '/' + i_photo)
                    img_width, img_height = img.size
                    # Resize landscape photos
                    if img_width > img_height:
                        if img_width > 1500:
                            basewidth = 1500
                            wpercent = (basewidth/float(img.size[0]))
                            hsize = int((float(img.size[1])*float(wpercent)))
                            img = img.resize((basewidth,hsize), Image.Resampling.LANCZOS)
                    # Resize portrait photos
                    else:
                        if img_height > 1500:
                            baseheight = 1500
                            hpercent = (baseheight/float(img.size[1]))
                            wsize = int((float(img.size[0])*float(hpercent)))
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
                    preptime = None
                try:
                    cooktime = int(cooktime)
                except:
                    cooktime = None
                try:
                    totaltime = int(totaltime)
                except:
                    totaltime = None
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
                recipe = Recipe(hex_id=hex_string, title=rec_title, category='Miscellaneous', photo=i_photo, description=i_description, url=rec_url,
                    servings=servings, prep_time=preptime, cook_time=cooktime, total_time=totaltime, ingredients=i_ingredients, 
                    instructions=i_instructions, favorite=0, public=0, user_id=current_user.id)
                db.session.add(recipe)
                db.session.commit()
                if calories or carbs or protein or fat or sugar or cholesterol or sodium or fiber:
                    curr_recipe = Recipe.query.filter_by(hex_id=hex_string).first()
                    new_nutrition = NutritionalInfo(recipe_id=curr_recipe.id, user_id=current_user.id, calories=calories, 
                        carbs=carbs, protein=protein, fat=fat, sugar=sugar, cholesterol=cholesterol, sodium=sodium, fiber=fiber)
                    db.session.add(new_nutrition)
                    db.session.commit()
                flash(_('The recipe has been saved to My Recipes.'))
            else:
                flash(_('The recipe is missing ingredients or instructions and cannot be imported.'))
        else:
            flash('Error: ' + _('This recipe is already saved in My Recipes.'))
    return render_template('explore-recipe-detail.html', title=_('Explore Recipe Detail'),
        mdescription=_('View the details for the selected Explore page recipe.'),
        rec_url=rec_url, rec_title=rec_title, preptime=preptime, cooktime=cooktime, totaltime=totaltime, description=description,
        photo=photo, ingredients=ingredients, instructions=instructions, form=form, calories=calories, carbs=carbs,
        protein=protein, fat=fat, sugar=sugar, cholesterol=cholesterol, sodium=sodium, fiber=fiber, nutrition=nutrition,
        servings=servings, photo_server=photo_server, responsecode=responsecode)
