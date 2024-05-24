from flask import render_template, flash, redirect, url_for, request
from app import app, db, limiter
from flask_login import current_user, login_user, logout_user, login_required
from app.models import User, Recipe, Shoplist, Listitem, MealRecipe
from datetime import datetime
import secrets, time, random, requests, re, urllib.request
from app.mealplanner import bp
from config import Config

@bp.route('/meal-planner')
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
	month=month, query_string=query_string, query_string_full=query_string_full, query_count=query_count, compactmonth=compactmonth, mealsinmonth=mealsinmonth)

@bp.route('/remove-plan/<hexid>')
@login_required
@limiter.limit(Config.DEFAULT_RATE_LIMIT)
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
    if mealplan.date is not None:
        return redirect(url_for('mealplanner.mealPlanner', day=mealplan.date))
    else:
        return redirect(url_for('mealplanner.mealPlanner'))
