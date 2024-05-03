from flask import render_template, flash, redirect, url_for, request
from app import app, db
from app.explore.forms import ExploreSearchForm, EmptyForm
from flask_login import current_user, login_user, logout_user, login_required
from flask_paginate import Pagination
from app.models import User, Recipe, NutritionalInfo
from werkzeug.urls import url_parse
from PIL import Image
from urllib.parse import urlparse
from urllib.request import urlopen, Request
from bs4 import BeautifulSoup
import secrets, time, random, os, imghdr, requests, re, urllib.request
from app.explore import bp

@bp.route('/explore', methods=['GET', 'POST'])
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
        return redirect(url_for('explore.exploreSearch', query=form.search.data))
    return render_template('explore.html', title='Explore', rec_all=rec_all, rec_beef=rec_beef, rec_breakfast=rec_breakfast,
        rec_chicken=rec_chicken, rec_desserts=rec_desserts, rec_salads=rec_salads, rec_seafood=rec_seafood, rec_sides=rec_sides, form=form)

@bp.route('/explore/search')
@login_required
def exploreSearch():
    # the query, example is search?query=garlic+shrimp which translates to "garlic shrimp"
    query_string = request.args.get('query')
    # subset of all_recipes in which all parts of query string are present in title
    # it has 5 items per recipe: title, shortened url, full url, all_recipes count, recipes count
    recipes = []
    # 2D array of all recipes in explore-all-randomized.txt file
    # it has 4 items per recipe: title, shortened url, full url, all_recipes count
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
        # rec_count is number of recipes in recipes array
        rec_count = 1
        for recipe in all_recipes:
            is_good = True
            for item in query_items:
                if item not in recipe[0]:
                    is_good = False
            if is_good == True:
                new_rec = recipe
                # append 5th item (index of 4) to recipes, recipes count
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
        # make rec_first the recipe count (5th item of recipe) for first recipe on page
        rec_first = recipes_page[0]
        rec_first = rec_first[4]
        # make rec_last the recipe count (5th item of recipe) for last recipe on page
        rec_last = recipes_page[len(recipes_page)-1]
        rec_last = rec_last[4]
    # if no recipes on current page, set rec_first and rec_last to 0
    else:
        rec_first = 0
        rec_last = 0
    rec_count = len(recipes)
    pagination = Pagination(page=page, per_page=PER_PAGE, total=len(recipes), search=False, record_name='recipes')
    return render_template('explore-search.html', title='Explore Search', recipes=recipes_page, pagination=pagination, curr_page=curr_page, page=page,
        rec_first=rec_first, rec_last=rec_last, rec_count=rec_count, query_string=query_string)

@bp.route('/explore/group/<group>')
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

@bp.route('/explore/recipe/<rec_group>/<recnum>', methods=['GET', 'POST'])
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
        calories_1 = soup.find('span',class_='wprm-nutrition-label-text-nutrition-container-calories')
        try:
            calories_2 = calories_1.find('span',class_='wprm-nutrition-label-text-nutrition-value')
        except:
            calories_2 = None
        if calories_2:
            calories = calories_2.get_text()
            try:
                calories = int(calories)
            except ValueError:
                calories = None
        else:
            calories = None
        carbs_1 = soup.find('span',class_='wprm-nutrition-label-text-nutrition-container-carbohydrates')
        try:
            carbs_2 = carbs_1.find('span',class_='wprm-nutrition-label-text-nutrition-value')
        except:
            carbs_2 = None
        if carbs_2:
            carbs = carbs_2.get_text()
            try:
                carbs = int(carbs)
            except ValueError:
                carbs = None
        else:
            carbs = None
        protein_1 = soup.find('span',class_='wprm-nutrition-label-text-nutrition-container-protein')
        try:
            protein_2 = protein_1.find('span',class_='wprm-nutrition-label-text-nutrition-value')
        except:
            protein_2 = None
        if protein_2:
            protein = protein_2.get_text()
            try:
                protein = int(protein)
            except ValueError:
                protein = None
        else:
            protein = None
        fat_1 = soup.find('span',class_='wprm-nutrition-label-text-nutrition-container-fat')
        try:
            fat_2 = fat_1.find('span',class_='wprm-nutrition-label-text-nutrition-value')
        except:
            fat_2 = None
        if fat_2:
            fat = fat_2.get_text()
            try:
                fat = int(fat)
            except ValueError:
                fat = None
        else:
            fat = None
        sugar_1 = soup.find('span',class_='wprm-nutrition-label-text-nutrition-container-sugar')
        try:
            sugar_2 = sugar_1.find('span',class_='wprm-nutrition-label-text-nutrition-value')
        except:
            sugar_2 = None
        if sugar_2:
            sugar = sugar_2.get_text()
            try:
                sugar = int(sugar)
            except ValueError:
                sugar = None
        else:
            sugar = None
        cholesterol_1 = soup.find('span',class_='wprm-nutrition-label-text-nutrition-container-cholesterol')
        try:
            cholesterol_2 = cholesterol_1.find('span',class_='wprm-nutrition-label-text-nutrition-value')
        except:
            cholesterol_2 = None
        if cholesterol_2:
            cholesterol = cholesterol_2.get_text()
            try:
                cholesterol = int(cholesterol)
            except ValueError:
                cholesterol = None
        else:
            cholesterol = None
        sodium_1 = soup.find('span',class_='wprm-nutrition-label-text-nutrition-container-sodium')
        try:
            sodium_2 = sodium_1.find('span',class_='wprm-nutrition-label-text-nutrition-value')
        except:
            sodium_2 = None
        if sodium_2:
            sodium = sodium_2.get_text()
            try:
                sodium = int(sodium)
            except ValueError:
                sodium = None
        else:
            sodium = None
        fiber_1 = soup.find('span',class_='wprm-nutrition-label-text-nutrition-container-fiber')
        try:
            fiber_2 = fiber_1.find('span',class_='wprm-nutrition-label-text-nutrition-value')
        except:
            fiber_2 = None
        if fiber_2:
            fiber = fiber_2.get_text()
            try:
                fiber = int(fiber)
            except ValueError:
                fiber = None
        else:
            fiber = None
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
        # Assign Servings to integer variable if it is listed on page
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
        # Assign Nutrition Facts to integer variables if listed on page
        calories_1 = soup.find('span',class_='wprm-nutrition-label-text-nutrition-container-calories')
        try:
            calories_2 = calories_1.find('span',class_='wprm-nutrition-label-text-nutrition-value')
        except:
            calories_2 = None
        if calories_2:
            calories = calories_2.get_text()
            try:
                calories = int(calories)
            except ValueError:
                calories = None
        else:
            calories = None
        carbs_1 = soup.find('span',class_='wprm-nutrition-label-text-nutrition-container-carbohydrates')
        try:
            carbs_2 = carbs_1.find('span',class_='wprm-nutrition-label-text-nutrition-value')
        except:
            carbs_2 = None
        if carbs_2:
            carbs = carbs_2.get_text()
            try:
                carbs = int(carbs)
            except ValueError:
                carbs = None
        else:
            carbs = None
        protein_1 = soup.find('span',class_='wprm-nutrition-label-text-nutrition-container-protein')
        try:
            protein_2 = protein_1.find('span',class_='wprm-nutrition-label-text-nutrition-value')
        except:
            protein_2 = None
        if protein_2:
            protein = protein_2.get_text()
            try:
                protein = int(protein)
            except ValueError:
                protein = None
        else:
            protein = None
        fat_1 = soup.find('span',class_='wprm-nutrition-label-text-nutrition-container-fat')
        try:
            fat_2 = fat_1.find('span',class_='wprm-nutrition-label-text-nutrition-value')
        except:
            fat_2 = None
        if fat_2:
            fat = fat_2.get_text()
            try:
                fat = int(fat)
            except ValueError:
                fat = None
        else:
            fat = None
        sugar_1 = soup.find('span',class_='wprm-nutrition-label-text-nutrition-container-sugar')
        try:
            sugar_2 = sugar_1.find('span',class_='wprm-nutrition-label-text-nutrition-value')
        except:
            sugar_2 = None
        if sugar_2:
            sugar = sugar_2.get_text()
            try:
                sugar = int(sugar)
            except ValueError:
                sugar = None
        else:
            sugar = None
        cholesterol_1 = soup.find('span',class_='wprm-nutrition-label-text-nutrition-container-cholesterol')
        try:
            cholesterol_2 = cholesterol_1.find('span',class_='wprm-nutrition-label-text-nutrition-value')
        except:
            cholesterol_2 = None
        if cholesterol_2:
            cholesterol = cholesterol_2.get_text()
            try:
                cholesterol = int(cholesterol)
            except ValueError:
                cholesterol = None
        else:
            cholesterol = None
        sodium_1 = soup.find('span',class_='wprm-nutrition-label-text-nutrition-container-sodium')
        try:
            sodium_2 = sodium_1.find('span',class_='wprm-nutrition-label-text-nutrition-value')
        except:
            sodium_2 = None
        if sodium_2:
            sodium = sodium_2.get_text()
            try:
                sodium = int(sodium)
            except ValueError:
                sodium = None
        else:
            sodium = None
        fiber_1 = soup.find('span',class_='wprm-nutrition-label-text-nutrition-container-fiber')
        try:
            fiber_2 = fiber_1.find('span',class_='wprm-nutrition-label-text-nutrition-value')
        except:
            fiber_2 = None
        if fiber_2:
            fiber = fiber_2.get_text()
            try:
                fiber = int(fiber)
            except ValueError:
                fiber = None
        else:
            fiber = None
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
        page = requests.get(rec_url)
        soup = BeautifulSoup(page.text, 'html.parser')
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
        # This site does lists Nutrition Facts as float (not int) with units in same span
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
                preptime = int(numbers[0])
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
                cooktime = int(numbers[0])
            except:
                cooktime = ''
        else:
            cooktime = ''
        if preptime and cooktime:
            totaltime = preptime + cooktime
        else:
            totaltime = ''
        # Extract description
        description_1 = soup.find('meta',attrs={"property": "og:description"})
        if description_1:
            description = description_1['content']
        else:
            description = ''
        # Extract ingredients and instructions
        ingredients = []
        ingredients_1 = soup.find_all('li',class_='tr-ingredient-checkbox-container')
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
    else:
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
                i_ingredients = i_ingredients[:4400]
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
                flash('The recipe has been saved to My Recipes.')
            else:
                flash('The recipe is missing ingredients or instructions and cannot be imported.')
        else:
            flash('Error: This recipe is already saved in My Recipes.')
    return render_template('explore-recipe-detail.html', title='Explore Recipe Detail', rec_url=rec_url, rec_title=rec_title, preptime=preptime,
        cooktime=cooktime, totaltime=totaltime, description=description, photo=photo, ingredients=ingredients, instructions=instructions, form=form,
        calories=calories, carbs=carbs, protein=protein, fat=fat, sugar=sugar, cholesterol=cholesterol, sodium=sodium, fiber=fiber, nutrition=nutrition, servings=servings)
