from flask import render_template, flash, redirect, url_for, request, jsonify, make_response, json
from flask_babel import _
from app import app, db, limiter
from flask_login import current_user, login_user, logout_user, login_required
from app.models import User, Recipe, Shoplist, Listitem, MealRecipe
from sqlalchemy import func, and_, or_
from datetime import datetime, timedelta, date
import secrets, time, random, requests, re, urllib.request, calendar
from app.mealplanner import bp
from config import Config

# The calendar page displays upcoming and completed recipes for the current month (month view)
# When viewing on a desktop, up to two recipes are listed for any given day
# If a day has more than two recipes, "N more recipes" message will be displayed
# at the bottom of the cell below the first two recipe titles.
# When viewing on mobile, instead of recipe titles, dots are displayed with the cell (up
# to 3 dots per cell, color of dots is user accent color)
# Previous and Next buttons allow switching between months
@bp.route('/meal-planner/calendar')
@login_required
@limiter.limit(Config.DEFAULT_RATE_LIMIT)
def mealPlannerCalendar():
    # Determine which month to show
    # optional ?year=YYYY&month=MM query; defaults to current month
    try:
        year  = int(request.args.get('year',  datetime.now().year))
        month = int(request.args.get('month', datetime.now().month))
    except ValueError:
        year, month = datetime.now().year, datetime.now().month

    first_of_month = date(year, month, 1)
    first_weekday_num, num_days_in_month = calendar.monthrange(year, month)

    # python weekday: Monday=0 … Sunday=6
    first_weekday = first_of_month.weekday()  # 0‑6
    days_back = (first_weekday + 1) % 7       # 0 if Sunday, 1 if Mon, etc.
    start_date = first_of_month - timedelta(days=days_back)

    last_of_month = date(year, month, num_days_in_month)
    last_weekday = last_of_month.weekday()    # 0‑6
    days_forward = (5 - last_weekday) % 7     # Saturday in same / next week
    end_date = last_of_month + timedelta(days=days_forward)

    # Gather all dates in the grid
    total_days = (end_date - start_date).days + 1
    grid_dates = [start_date + timedelta(days=i) for i in range(total_days)]

    # Fetch user's meal plans that fall inside the grid
    user = User.query.filter_by(email=current_user.email).first_or_404()
    date_strings_in_grid = {d.strftime("%Y-%m-%d") for d in grid_dates}
    plans_in_month = [p for p in user.planned_meals.all() if p.date in date_strings_in_grid]

    # Build a dict  { "YYYY-MM-DD": [Recipe, …] }
    plans_by_date = {}
    for plan in plans_in_month:
        plans_by_date.setdefault(plan.date, []).append(plan)

    # Assemble structures to feed the template
    calendar_days = []
    today_str = datetime.now().date().strftime("%Y-%m-%d")

    for d in grid_dates:
        iso = d.strftime("%Y-%m-%d")
        # First two recipe titles
        recipe_titles = []
        more_count = 0

        if iso in plans_by_date:
            # Fetch Recipe rows only once each
            for plan in plans_by_date[iso][:2]:
                r = Recipe.query.get(plan.recipe_id)
                recipe_titles.append(r.title if r else "Recipe")
            more_count = max(0, len(plans_by_date[iso]) - 2)
			
		# Calculate how many dots to show (up to 3)
        dot_count = min(3, len(recipe_titles) + more_count)

        calendar_days.append({
            "iso": iso,                         # "2025-04-15"
            "day": d.day,                       # 15
            "in_month": (d.month == month),     # True if belongs to current month
            "is_today": (iso == today_str),
            "titles": recipe_titles,            # up to 2 titles
            "more": more_count,                 # 0,1,2,or higher
			"dot_count": dot_count
        })

    month_label = f"{calendar.month_name[month]} {year}"
    prev_month = (first_of_month - timedelta(days=1))
    next_month = (last_of_month + timedelta(days=1))

    return render_template('meal-planner-calendar.html', title=_('Meal Planner Calendar'), 
        mdescription=_('View recipes planned for the current month.'), month_label=month_label, 
        calendar_days=calendar_days, prev_year=prev_month.year, prev_month=prev_month.month, next_year=next_month.year,
        next_month=next_month.month)

# The purpose of this page is to view recipes for a specific day
# When clicking a day on the calendar, will be directed to this page
# This page has a form that allows adding meal plan by selecting a recipe
@bp.route('/meal-planner/calendar/details', methods=['GET','POST'])
@login_required
@limiter.limit(Config.DEFAULT_RATE_LIMIT)
def mealPlannerCalendarDetails():
    date_str = request.args.get('date')
    user = User.query.filter_by(email=current_user.email).first_or_404()
    if request.method == 'POST':
        hex_id = request.form.get('hex_id')
        recipe = Recipe.query.filter_by(hex_id=hex_id, user_id=user.id).first()
        if not recipe:
            # TO-DO: change this message
            flash(_('Invalid recipe selected.'))
        else:
            # TO-DO: implement Meal Plan adding logic, change message
            flash(_('Recipe added!'))
        return redirect(url_for('mealplanner.mealPlannerCalendarDetails', date=date_str))
    plannedmeals = user.planned_meals.filter_by(date=date_str).all()
    recdetails = []
    for meal in plannedmeals:
        recipe = Recipe.query.get_or_404(meal.recipe_id)
        recdetails.append({
            'title':    recipe.title,
            'category': recipe.category,
            'hex_id':   recipe.hex_id
        })
    # Format the date for display
    try:
        d = datetime.strptime(date_str, '%Y-%m-%d')
        full_date = f"{d.strftime('%A')}, {d.strftime('%B')} {d.day}, {d.year}"
    except:
        full_date = date_str or _('Invalid date')
    # Create 2D array that contains compact date and full date for Meal Planner scheduling
    w, h = 2, 365
    month = [[0 for x in range(w)] for y in range(h)]
    curr_dt = datetime.now()
    timestamp = int(time.mktime(curr_dt.timetuple()))
    days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    # Create array that is used for checking whether meal is past or future
    days365 = []
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
        days365.append(compactdate)
        timestamp += 86400
    return render_template('meal-planner-calendar-details.html', title=_('Meal Planner Calendar Details'),
        mdescription=_('View recipes planned for a specific day.'), plannedmeals=plannedmeals,
        full_date=full_date, recdetails=recdetails, date_str=date_str, days365=days365)

@bp.route('/meal-planner/list-all-recipes', methods=['GET'])
@login_required
@limiter.limit(Config.DEFAULT_RATE_LIMIT)
def mealPlannerListAllRecipes():
    user = User.query.filter_by(email=current_user.email).first_or_404()
    if user:
        recipes_query = db.session.query(
            Recipe.id,
            Recipe.title,
            Recipe.category,
            Recipe.hex_id
        ).filter(Recipe.user_id == user.id).order_by(func.lower(Recipe.title))
        # Prepare recipes to be displayed as JSON
        recipe_data = []
        for recipe in recipes_query.all():
            recipe_info = {
                "id": recipe.hex_id,
                "title": recipe.title
            }
            recipe_data.append(recipe_info)
    else:
        # if user is not found, empty array will be used to create JSON response
        recipe_data = []
    # Return response without key sorting
    response_json = json.dumps({"recipes": recipe_data}, sort_keys=False)
    response = make_response(response_json)
    response.headers['Content-Type'] = 'application/json'
    return response

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
    w, year_h, month_h, week_h, fiveyear_h = 2, 365, 30, 7, 1825
    fiveyear = [[0 for x in range(w)] for y in range(fiveyear_h)]
    year = [[0 for x in range(w)] for y in range(year_h)]
    month = [[0 for x in range(w)] for y in range(month_h)]
    week = [[0 for x in range(w)] for y in range(week_h)]
    curr_dt = datetime.now()
    fiveyear_timestamp = int(time.mktime(curr_dt.timetuple()))
    year_timestamp = int(time.mktime(curr_dt.timetuple()))
    month_timestamp = int(time.mktime(curr_dt.timetuple()))
    week_timestamp = int(time.mktime(curr_dt.timetuple()))
    days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    for d in fiveyear:
        fiveyear_timestamp -= 86400
        date = datetime.fromtimestamp(fiveyear_timestamp)
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
    # Create array to store only compact dates, used to check if meal is from past five years (or other criteria)
    compactfiveyear = []
    for d in fiveyear:
        compactfiveyear.append(d[0])
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
    mealsinfiveyear = []
    for meal in plannedmeals:
        if meal.date in compactfiveyear:
            mealsinfiveyear.append(meal)
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
            dayspaginated.append(meal.date)
    return render_template('meal-planner-completed.html', title=_('Meal Planner (Completed)'),
        mdescription=_('View Recipes that have been completed in the Meal Planner.'), plannedmeals=plannedmeals, recdetails=recdetails,
        dayswithmeals=dayswithmeals, dayswithmeals_m=dayswithmeals_m, dayswithmeals_w=dayswithmeals_w, year=year, month=month,
        week=week, compactyear=compactyear, compactmonth=compactmonth, compactweek=compactweek, mealsinyear=mealsinyear,
        mealsinmonth=mealsinmonth, mealsinweek=mealsinweek, plannedmeals_paginated=plannedmeals_paginated,
        next_url=next_url, prev_url=prev_url, dayspaginated=dayspaginated, compactfiveyear=compactfiveyear,
        mealsinfiveyear=mealsinfiveyear, fiveyear=fiveyear)

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
