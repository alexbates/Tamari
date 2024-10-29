from flask import render_template, flash, redirect, url_for, request, send_from_directory, jsonify, make_response, json
from flask_babel import _
from flask_jwt_extended import create_access_token, create_refresh_token
from flask_jwt_extended import jwt_required, get_jwt_identity
from app import app, db, limiter
from flask_login import current_user, login_user, logout_user, login_required
from app.models import User, Recipe, NutritionalInfo, Category, Shoplist, Listitem, MealRecipe
from app.account.routes import rate_limited_login
from werkzeug.urls import url_parse
import secrets, time, random, os, imghdr, requests, re, urllib.request, zipfile
from datetime import datetime
from app.api import bp
from config import Config

@bp.route('/api/user/authenticate', methods=['POST'])
@limiter.limit(Config.DEFAULT_RATE_LIMIT)
def apiAuthenticate():
    if app.config.get('API_ENABLED', True):
        # Call rate limited function to effectively impose rate limit on login attempts
        if rate_limited_login():
            # Add delay to slow the rate at which login requests can be made
            time.sleep(0.5)
            data = request.get_json()
            # Validate that 'email' and 'password' fields are present and not empty
            if not data or not data.get('email') or not data.get('password'):
                return jsonify({"message": "Email and password are required"}), 400
            app_name = request.headers.get('X-App-Name')
            app_key = request.headers.get('X-App-Key')
            email = data.get('email').lower()
            password = data.get('password')
            user = User.query.filter_by(email=email).first()
            # Require app name to match
            if app_name is None or app_name.lower() != 'tamari':
                return jsonify({"message": "app name is missing or incorrect"}), 401
            # Check if the provided app_key matches the one in the configuration
            if app_key != app.config.get('APP_KEY'):
                return jsonify({"message": "Invalid app_key"}), 401
            # Disallow API login for demo account
            if email == "demo@tamariapp.com":
                return jsonify({"message": "API access disallowed for demo account"}), 401
            # Check login
            if user is None or not user.check_password(password):
                return jsonify({"message": "Invalid username or password"}), 401
            # Create JWT access and refresh tokens
            access_token = create_access_token(
                identity=user.id,
                expires_delta=app.config.get('ACCESS_TOKEN_EXPIRES')
            )
            refresh_token = create_refresh_token(
                identity=user.id,
                expires_delta=app.config.get('REFRESH_TOKEN_EXPIRES')
            )
            # Return the tokens in JSON response
            return jsonify(message="success", access_token=access_token, refresh_token=refresh_token), 200
    else:
        return jsonify({"message": "API is disabled"}), 503

@bp.route('/api/user/refresh', methods=['POST'])
@limiter.limit(Config.DEFAULT_RATE_LIMIT)
@jwt_required(refresh=True)
# If provided token in Authorization header is an access_token, it will fail with 401 Unauthorized
def apiRefresh():
    if app.config.get('API_ENABLED', True):
        # Check if there is a request body (there should be none)
        if request.data:
            return jsonify({"message": "Request body is not allowed"}), 400
        app_name = request.headers.get('X-App-Name')
        app_key = request.headers.get('X-App-Key')
        # Require app name to match
        if app_name is None or app_name.lower() != 'tamari':
            return jsonify({"message": "app name is missing or incorrect"}), 401
        # Check if the provided app_key matches the one in the configuration
        if app_key != app.config.get('APP_KEY'):
            return jsonify({"message": "Invalid app_key"}), 401
        # Get the identity of the user from the refresh token
        current_user = get_jwt_identity()
        # Create a new access token
        new_access_token = create_access_token(
            identity=current_user,
            expires_delta=app.config.get('ACCESS_TOKEN_EXPIRES')
        )
        # Return the new access token
        return jsonify({
            "message": "success",
            "access_token": new_access_token
        }), 200
    else:
        return jsonify({"message": "API is disabled"}), 503

@bp.route('/api/user/profile', methods=['GET'])
@limiter.limit(Config.DEFAULT_RATE_LIMIT)
@jwt_required()
# If provided token in Authorization header is an access_token, it will fail with 401 Unauthorized
def apiProfile():
    if app.config.get('API_ENABLED', True):
        # Check if there is a request body (there should be none)
        if request.data:
            return jsonify({"message": "Request body is not allowed"}), 400
        app_name = request.headers.get('X-App-Name')
        app_key = request.headers.get('X-App-Key')
        # Require app name to match
        if app_name is None or app_name.lower() != 'tamari':
            return jsonify({"message": "app name is missing or incorrect"}), 401
        # Check if the provided app_key matches the one in the configuration
        if app_key != app.config.get('APP_KEY'):
            return jsonify({"message": "Invalid app_key"}), 401
        # Get the identity of the user from the refresh token
        current_user = get_jwt_identity()
        user = User.query.filter_by(id=current_user).first_or_404()
        if user:
            # Update last visit time in database
            user.last_time = datetime.utcnow()
            db.session.commit()
            u_email = user.email
            u_reg_time = user.reg_time
            u_last_time = user.last_time
            recipes = user.recipes.order_by(Recipe.title)
            rec_count = 0
            for recipe in recipes:
                rec_count += 1
            favorites = user.recipes.order_by(Recipe.title).filter(Recipe.favorite == 1)
            fav_count = 0
            for recipe in favorites:
                fav_count += 1
            categories = user.categories.order_by(Category.label).all()
            cat_count = 0
            for category in categories:
                cat_count += 1
            lists = user.shop_lists.order_by(Shoplist.label).all()
            list_count = 0
            for list in lists:
                list_count += 1
            plannedmeals = user.planned_meals.all()
            meal_count = 0
            for meal in plannedmeals:
                meal_count += 1
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
            # Create array to store only compact dates, used to check if meal is from past year, month, and week
            compactyear = []
            for d in year:
                compactyear.append(d[0])
            compactmonth = []
            for d in month:
                compactmonth.append(d[0])
            compactweek = []
            for d in week:
                compactweek.append(d[0])
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
        else:
            u_email = None
            u_reg_time = None
            u_last_time = None
            rec_count = 0
            fav_count = 0
            cat_count = 0
            list_count = 0
            meal_count = 0
            mealsinyear = []
            mealsinmonth = []
            mealsinweek = []
            dayswithmeals = []
            dayswithmeals_m = []
            dayswithmeals_w = []
        # Build response JSON
        response_data = {
            "email": u_email,
            "register_time": u_reg_time,
            "last_visited": u_last_time,
            "my_recipes": {
                "recipes": rec_count,
                "favorites": fav_count,
                "categories": cat_count
            },
            "shopping_lists": list_count,
            "meal_planner": {
                "recipes_prepared": {
                    "total": meal_count,
                    "past_week": len(mealsinweek),
                    "past_month": len(mealsinmonth),
                    "past_year": len(mealsinyear)
                },
                "days_cooked": {
                    "past_week": len(dayswithmeals_w),
                    "past_month": len(dayswithmeals_m),
                    "past_year": len(dayswithmeals)
                }
            }
        }
        # Return response without key sorting
        response_json = json.dumps(response_data, sort_keys=False)
        response = make_response(response_json)
        response.headers['Content-Type'] = 'application/json'
        return response
    else:
        return jsonify({"message": "API is disabled"}), 503
        
@bp.route('/api/my-recipes/all', methods=['GET'])
@limiter.limit(Config.DEFAULT_RATE_LIMIT)
@jwt_required()
# If provided token in Authorization header is an access_token, it will fail with 401 Unauthorized
def apiAllRecipes():
    if app.config.get('API_ENABLED', True):
        # Check if there is a request body (there should be none)
        if request.data:
            return jsonify({"message": "Request body is not allowed"}), 400
        app_name = request.headers.get('X-App-Name')
        app_key = request.headers.get('X-App-Key')
        # Require app name to match
        if app_name is None or app_name.lower() != 'tamari':
            return jsonify({"message": "app name is missing or incorrect"}), 401
        # Check if the provided app_key matches the one in the configuration
        if app_key != app.config.get('APP_KEY'):
            return jsonify({"message": "Invalid app_key"}), 401
        # Get the identity of the user from the refresh token
        current_user = get_jwt_identity()
        user = User.query.filter_by(id=current_user).first_or_404()
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        sort = request.args.get('sort', 'title', type=str).lower()
        valid_sort_options = ['title', 'title_desc', 'category', 'category_desc', 'time_created', 'time_created_desc']
        if sort not in valid_sort_options:
            return jsonify({"message": "Specified sort option is not recognized"}), 400
        # these optional query parameters default to True
        category = request.args.get('category', 'True', type=str).lower() == 'true'
        photo = request.args.get('photo', 'True', type=str).lower() == 'true'
        # these optional query parameters default to False
        prep_times = request.args.get('prep_times', 'False', type=str).lower() == 'true'
        time_created = request.args.get('time_created', 'False', type=str).lower() == 'true'
        calories = request.args.get('calories', 'False', type=str).lower() == 'true'
        if user:
            if sort == 'title':
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
            elif sort == 'title_desc':
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
                ).outerjoin(NutritionalInfo, Recipe.id == NutritionalInfo.recipe_id).filter(Recipe.user_id == user.id).order_by(Recipe.title.desc())
            elif sort == 'category':
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
                ).outerjoin(NutritionalInfo, Recipe.id == NutritionalInfo.recipe_id).filter(Recipe.user_id == user.id).order_by(Recipe.category)
            elif sort == 'category_desc':
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
                ).outerjoin(NutritionalInfo, Recipe.id == NutritionalInfo.recipe_id).filter(Recipe.user_id == user.id).order_by(Recipe.category.desc())
            elif sort == 'time_created':
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
            # Prepare recipes to be displayed as JSON
            recipe_data = []
            for recipe in recipes.items:
                recipe_info = {
                    "hex_id": recipe.hex_id,
                    "title": recipe.title
                }
                # Include optional data if specified by query parameters
                if category:
                    recipe_info["category"] = recipe.category
                if photo:
                    recipe_info["photo"] = recipe.photo
                if prep_times:
                    recipe_info["prep_time"] = recipe.prep_time
                    recipe_info["cook_time"] = recipe.cook_time
                    recipe_info["total_time"] = recipe.total_time
                if time_created:
                    recipe_info["time_created"] = recipe.time_created
                if calories:
                    recipe_info["calories"] = recipe.calories
                recipe_data.append(recipe_info)
        else:
            # if user is not found, empty array will be used to create JSON response
            recipe_data = []
        # Return response without key sorting
        response_json = json.dumps({"recipes": recipe_data}, sort_keys=False)
        response = make_response(response_json)
        response.headers['Content-Type'] = 'application/json'
        return response
    else:
        return jsonify({"message": "API is disabled"}), 503
        
@bp.route('/api/my-recipes/favorites', methods=['GET'])
@limiter.limit(Config.DEFAULT_RATE_LIMIT)
@jwt_required()
# If provided token in Authorization header is an access_token, it will fail with 401 Unauthorized
def apiFavorites():
    if app.config.get('API_ENABLED', True):
        # Check if there is a request body (there should be none)
        if request.data:
            return jsonify({"message": "Request body is not allowed"}), 400
        app_name = request.headers.get('X-App-Name')
        app_key = request.headers.get('X-App-Key')
        # Require app name to match
        if app_name is None or app_name.lower() != 'tamari':
            return jsonify({"message": "app name is missing or incorrect"}), 401
        # Check if the provided app_key matches the one in the configuration
        if app_key != app.config.get('APP_KEY'):
            return jsonify({"message": "Invalid app_key"}), 401
        # Get the identity of the user from the refresh token
        current_user = get_jwt_identity()
        user = User.query.filter_by(id=current_user).first_or_404()
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        sort = request.args.get('sort', 'title', type=str).lower()
        valid_sort_options = ['title', 'title_desc', 'category', 'category_desc', 'time_created', 'time_created_desc']
        if sort not in valid_sort_options:
            return jsonify({"message": "Specified sort option is not recognized"}), 400
        # these optional query parameters default to True
        category = request.args.get('category', 'True', type=str).lower() == 'true'
        photo = request.args.get('photo', 'True', type=str).lower() == 'true'
        # these optional query parameters default to False
        prep_times = request.args.get('prep_times', 'False', type=str).lower() == 'true'
        time_created = request.args.get('time_created', 'False', type=str).lower() == 'true'
        calories = request.args.get('calories', 'False', type=str).lower() == 'true'
        if user:
            if sort == 'title':
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
                ).outerjoin(NutritionalInfo, Recipe.id == NutritionalInfo.recipe_id).filter(Recipe.user_id == user.id, Recipe.favorite == 1).order_by(Recipe.title)
            elif sort == 'title_desc':
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
                ).outerjoin(NutritionalInfo, Recipe.id == NutritionalInfo.recipe_id).filter(Recipe.user_id == user.id, Recipe.favorite == 1).order_by(Recipe.title.desc())
            elif sort == 'category':
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
                ).outerjoin(NutritionalInfo, Recipe.id == NutritionalInfo.recipe_id).filter(Recipe.user_id == user.id, Recipe.favorite == 1).order_by(Recipe.category)
            elif sort == 'category_desc':
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
                ).outerjoin(NutritionalInfo, Recipe.id == NutritionalInfo.recipe_id).filter(Recipe.user_id == user.id, Recipe.favorite == 1).order_by(Recipe.category.desc())
            elif sort == 'time_created':
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
            # Prepare recipes to be displayed as JSON
            recipe_data = []
            for recipe in recipes.items:
                recipe_info = {
                    "hex_id": recipe.hex_id,
                    "title": recipe.title
                }
                # Include optional data if specified by query parameters
                if category:
                    recipe_info["category"] = recipe.category
                if photo:
                    recipe_info["photo"] = recipe.photo
                if prep_times:
                    recipe_info["prep_time"] = recipe.prep_time
                    recipe_info["cook_time"] = recipe.cook_time
                    recipe_info["total_time"] = recipe.total_time
                if time_created:
                    recipe_info["time_created"] = recipe.time_created
                if calories:
                    recipe_info["calories"] = recipe.calories
                recipe_data.append(recipe_info)
        else:
            # if user is not found, empty array will be used to create JSON response
            recipe_data = []
        # Return response without key sorting
        response_json = json.dumps({"recipes": recipe_data}, sort_keys=False)
        response = make_response(response_json)
        response.headers['Content-Type'] = 'application/json'
        return response
    else:
        return jsonify({"message": "API is disabled"}), 503