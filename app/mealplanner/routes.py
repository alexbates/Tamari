from flask import render_template, flash, redirect, url_for, request
from flask_babel import _
from app import app, db, limiter
from flask_login import current_user, login_user, logout_user, login_required
from app.models import User, Recipe, Shoplist, Listitem, MealRecipe
from datetime import datetime
import secrets, time, random, requests, re, urllib.request
from app.mealplanner import bp
from config import Config

@bp.route('/meal-planner/upcoming')
@login_required
@limiter.limit(Config.DEFAULT_RATE_LIMIT)
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
    # Create array that contains all items from "plannedmeals" except those outside 30 day window
    mealsinmonth = []
    for meal in plannedmeals:
        if meal.date in compactmonth:
            mealsinmonth.append(meal)
    # Create 2D array in the same format as "month" that only contains days with meals
    month_with_meals = [d for d in month if d[0] in [meal.date for meal in mealsinmonth]]
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
    return render_template('meal-planner-upcoming.html', title=_('Meal Planner (Upcoming)'),
        mdescription=_('View recipes planned over the next 30 days in Meal Planner Upcoming.'), plannedmeals=plannedmeals, recdetails=recdetails, 
        dayswithmeals=dayswithmeals, month=month, query_string=query_string, query_string_full=query_string_full, query_count=query_count, 
        compactmonth=compactmonth, mealsinmonth=mealsinmonth, month_with_meals=month_with_meals)

@bp.route('/meal-planner/completed')
@login_required
@limiter.limit(Config.DEFAULT_RATE_LIMIT)
def mealPlannerCompleted():
    user = User.query.filter_by(email=current_user.email).first_or_404()
    plannedmeals = user.planned_meals.order_by(MealRecipe.date.desc()).all()
    # Create 2D arrays to hold compact date and full date for past year, past month, and past week
    w, year_h, month_h, week_h = 2, 365, 30, 7
    year = [[0 for x in range(w)] for y in range(year_h)]
    month = [[0 for x in range(w)] for y in range(month_h)]
    week = [[0 for x in range(w)] for y in range(week_h)]
    curr_dt = datetime.now()
    year_timestamp = int(time.mktime(curr_dt.timetuple()))
    month_timestamp = int(time.mktime(curr_dt.timetuple()))
    week_timestamp = int(time.mktime(curr_dt.timetuple()))
    days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    for d in year:
        year_timestamp -= 86400
        date = datetime.fromtimestamp(year_timestamp)
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
    for d in month:
        month_timestamp -= 86400
        date = datetime.fromtimestamp(month_timestamp)
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
    for d in week:
        week_timestamp -= 86400
        date = datetime.fromtimestamp(week_timestamp)
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
    # Create array to store only compact dates, used to check if meal is from past year
    compactyear = []
    for d in year:
        compactyear.append(d[0])
    compactmonth = []
    for d in month:
        compactmonth.append(d[0])
    compactweek = []
    for d in week:
        compactweek.append(d[0])
    # Get page number from URL query string
    page = request.args.get('page', 1, type=int)
    # per_page variable is used for paginating the recipes object
    per_page = app.config['MEAL_PLANS_PER_PAGE']
    # Calculate the start and end indices for pagination
    start_index = (page - 1) * per_page
    end_index = start_index + per_page
    # Paginate the sorted_events array
    plannedmeals_paginated = plannedmeals[start_index:end_index]
    # Create next and previous URLs for pagination
    next_url = url_for('mealplanner.mealPlannerCompleted', page=page + 1) if end_index < len(plannedmeals) else None
    prev_url = url_for('mealplanner.mealPlannerCompleted', page=page - 1) if start_index > 0 else None
    # Create array that contains all items from "plannedmeals" except those outside 1year/1month/1week window
    mealsinyear = []
    for meal in plannedmeals:
        if meal.date in compactyear:
            mealsinyear.append(meal)
    mealsinmonth = []
    for meal in plannedmeals:
        if meal.date in compactmonth:
            mealsinmonth.append(meal)
    mealsinweek = []
    for meal in plannedmeals:
        if meal.date in compactweek:
            mealsinweek.append(meal)
    # Create 2D array to store recipe info, it will somewhat mirror plannedmeals_paginated
    w2, h2 = 3, len(plannedmeals)
    recdetails = [[0 for x in range(w2)] for y in range(h2)]
    mealiteration = 0
    for meal in plannedmeals:
        recipe = Recipe.query.filter_by(id=meal.recipe_id).first_or_404()
        recdetails[mealiteration][0] = recipe.title
        recdetails[mealiteration][1] = recipe.category
        recdetails[mealiteration][2] = recipe.hex_id
        mealiteration += 1
    # Create arrays to store dates that meals are planned for, used by template to count meals for stats
    dayswithmeals = []
    for meal in mealsinyear:
        if meal.date not in dayswithmeals:
            dayswithmeals.append(meal.date)
    dayswithmeals_m = []
    for meal in mealsinmonth:
        if meal.date not in dayswithmeals_m:
            dayswithmeals_m.append(meal.date)
    dayswithmeals_w = []
    for meal in mealsinweek:
        if meal.date not in dayswithmeals_w:
            dayswithmeals_w.append(meal.date)
    # Array to store dates for template on current page
    dayspaginated = []
    for meal in plannedmeals_paginated:
        if meal.date not in dayspaginated:
            dayspaginated.append(meal)
    return render_template('meal-planner-completed.html', title=_('Meal Planner (Completed)'),
        mdescription=_('View Recipes that have been completed in the Meal Planner.'), plannedmeals=plannedmeals, recdetails=recdetails,
        dayswithmeals=dayswithmeals, dayswithmeals_m=dayswithmeals_m, dayswithmeals_w=dayswithmeals_w, year=year, month=month,
        week=week, compactyear=compactyear, compactmonth=compactmonth, compactweek=compactweek, mealsinyear=mealsinyear,
        mealsinmonth=mealsinmonth, mealsinweek=mealsinweek, plannedmeals_paginated=plannedmeals_paginated,
        next_url=next_url, prev_url=prev_url, dayspaginated=dayspaginated)

@bp.route('/remove-plan/<hexid>')
@login_required
@limiter.limit(Config.DEFAULT_RATE_LIMIT)
def removePlan(hexid):
    mealplan = MealRecipe.query.filter_by(hex_id=hexid).first()
    if mealplan is None:
        flash('Error: ' + _('meal plan does not exist or you lack permission to remove it.'))
    else:
        if mealplan.user_id == current_user.id:
            db.session.delete(mealplan)
            db.session.commit()
            flash(_('The meal plan has been deleted.'))
        else:
            flash('Error: ' + _('meal plan does not exist or you lack permission to remove it.'))
    if mealplan.date is not None:
        return redirect(url_for('mealplanner.mealPlanner', day=mealplan.date))
    else:
        return redirect(url_for('mealplanner.mealPlanner'))
