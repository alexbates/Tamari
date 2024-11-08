from flask import render_template, flash, redirect, url_for, request, send_from_directory, jsonify, make_response, json
from flask_babel import _
from flask_jwt_extended import create_access_token, create_refresh_token
from flask_jwt_extended import jwt_required, get_jwt_identity
from app import app, db, limiter
from flask_login import current_user, login_user, logout_user, login_required
from app.models import User, Recipe, NutritionalInfo, Category, Shoplist, Listitem, MealRecipe
from app.account.routes import rate_limited_login
from werkzeug.urls import url_parse
import secrets, time, random, os, imghdr, requests, re, urllib.request, zipfile, io, base64
from datetime import datetime
from PIL import Image
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
            if app.config.get('REQUIRE_HEADERS', True):
                # Require app name to match
                if app_name is None or app_name.lower() != 'tamari':
                    return jsonify({"message": "app name is missing or incorrect"}), 401
                # Check if the provided app_key matches the one in the configuration
                if not secrets.compare_digest(app_key, app.config.get('APP_KEY')):
                    return jsonify({"message": "Invalid app_key"}), 401
            # Verify that JSON is valid (no double quotes or unrecognized keys)
            try:
                for key, value in data.items():
                    if isinstance(value, str) and '"' in value:
                        return jsonify(message=f"Invalid value in key '{key}': double quotes are not allowed"), 400
            except:
                return jsonify(message="Invalid JSON format"), 400
            allowed_keys = {'email', 'password'}
            if not set(data.keys()).issubset(allowed_keys):
                invalid_keys = set(data.keys()) - allowed_keys
                return jsonify(message=f"Unrecognized keys: {', '.join(invalid_keys)}"), 400
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
        if app.config.get('REQUIRE_HEADERS', True):
            # Require app name to match
            if app_name is None or app_name.lower() != 'tamari':
                return jsonify({"message": "app name is missing or incorrect"}), 401
            # Check if the provided app_key matches the one in the configuration
            if not secrets.compare_digest(app_key, app.config.get('APP_KEY')):
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
        if app.config.get('REQUIRE_HEADERS', True):
            # Require app name to match
            if app_name is None or app_name.lower() != 'tamari':
                return jsonify({"message": "app name is missing or incorrect"}), 401
            # Check if the provided app_key matches the one in the configuration
            if not secrets.compare_digest(app_key, app.config.get('APP_KEY')):
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
        if app.config.get('REQUIRE_HEADERS', True):
            # Require app name to match
            if app_name is None or app_name.lower() != 'tamari':
                return jsonify({"message": "app name is missing or incorrect"}), 401
            # Check if the provided app_key matches the one in the configuration
            if not secrets.compare_digest(app_key, app.config.get('APP_KEY')):
                return jsonify({"message": "Invalid app_key"}), 401
        # Get the identity of the user from the refresh token
        current_user = get_jwt_identity()
        user = User.query.filter_by(id=current_user).first_or_404()
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 1000, type=int)
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
        if app.config.get('REQUIRE_HEADERS', True):
            # Require app name to match
            if app_name is None or app_name.lower() != 'tamari':
                return jsonify({"message": "app name is missing or incorrect"}), 401
            # Check if the provided app_key matches the one in the configuration
            if not secrets.compare_digest(app_key, app.config.get('APP_KEY')):
                return jsonify({"message": "Invalid app_key"}), 401
        # Get the identity of the user from the refresh token
        current_user = get_jwt_identity()
        user = User.query.filter_by(id=current_user).first_or_404()
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 1000, type=int)
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
        
@bp.route('/api/my-recipes/categories', methods=['GET'])
@limiter.limit(Config.DEFAULT_RATE_LIMIT)
@jwt_required()
# If provided token in Authorization header is an access_token, it will fail with 401 Unauthorized
def apiCategories():
    if app.config.get('API_ENABLED', True):
        # Check if there is a request body (there should be none)
        if request.data:
            return jsonify({"message": "Request body is not allowed"}), 400
        app_name = request.headers.get('X-App-Name')
        app_key = request.headers.get('X-App-Key')
        if app.config.get('REQUIRE_HEADERS', True):
            # Require app name to match
            if app_name is None or app_name.lower() != 'tamari':
                return jsonify({"message": "app name is missing or incorrect"}), 401
            # Check if the provided app_key matches the one in the configuration
            if not secrets.compare_digest(app_key, app.config.get('APP_KEY')):
                return jsonify({"message": "Invalid app_key"}), 401
        # Get the identity of the user from the refresh token
        current_user = get_jwt_identity()
        user = User.query.filter_by(id=current_user).first_or_404()
        if user:
            # Paginate the queried recipes
            categories = user.categories.order_by(Category.label).all()
            # Prepare recipes to be displayed as JSON
            category_data = []
            for category in categories:
                recipes = user.recipes.filter_by(category=category.label).all()
                category_info = {
                    "hex_id": category.hex_id,
                    "label": category.label,
                    "recipes": len(recipes)
                }
                category_data.append(category_info)
        else:
            # if user is not found, empty array will be used to create JSON response
            category_data = []
        # Return response without key sorting
        response_json = json.dumps({"categories": category_data}, sort_keys=False)
        response = make_response(response_json)
        response.headers['Content-Type'] = 'application/json'
        return response
    else:
        return jsonify({"message": "API is disabled"}), 503
        
@bp.route('/api/my-recipes/categories/add', methods=['POST'])
@limiter.limit(Config.DEFAULT_RATE_LIMIT)
@jwt_required()
# If provided token in Authorization header is an access_token, it will fail with 401 Unauthorized
def apiCategoriesAdd():
    if app.config.get('API_ENABLED', True):
        data = request.get_json()
        app_name = request.headers.get('X-App-Name')
        app_key = request.headers.get('X-App-Key')
        # POST data looks like {"label":"Miscellaneous"}
        label = data.get('label')
        if app.config.get('REQUIRE_HEADERS', True):
            # Require app name to match
            if app_name is None or app_name.lower() != 'tamari':
                return jsonify({"message": "app name is missing or incorrect"}), 401
            # Check if the provided app_key matches the one in the configuration
            if not secrets.compare_digest(app_key, app.config.get('APP_KEY')):
                return jsonify({"message": "Invalid app_key"}), 401
        # Get the identity of the user from the refresh token
        current_user = get_jwt_identity()
        user = User.query.filter_by(id=current_user).first_or_404()
        if user:
            categories = user.categories.order_by(Category.label).all()
            cats = []
            for cat in categories:
                curr_cat = cat.label
                cats.append(curr_cat)
            if not label:
                return jsonify(message="Category label is required"), 400
            if len(cats) > 39:
                return jsonify(message="You are limited to 40 categories"), 400
            if label in cats:
                return jsonify(message="The provided category already exists"), 400
            if len(label) > 20:
                return jsonify(message="The category must be less than 20 characters"), 400
            if len(label) < 3:
                return jsonify(message="The category must be at least 3 characters"), 400
            dis_chars = {'<', '>', '^', '{', '}', '/', '*', ';', '!', '@', '#', '$', '%', '&', '(', ')'}
            if any(char in dis_chars for char in label):
                return jsonify(message="Must not contain special characters"), 400
            hex_valid = 0
            while hex_valid == 0:
                hex_string = secrets.token_hex(4)
                hex_exist = Category.query.filter_by(hex_id=hex_string).first()
                if hex_exist is None:
                    hex_valid = 1
            category = Category(hex_id=hex_string, label=label, user=current_user)
            db.session.add(category)
            db.session.commit()
            return jsonify(message="success"), 200
        else:
            return jsonify(message="User not found"), 400
    else:
        return jsonify({"message": "API is disabled"}), 503
        
@bp.route('/api/my-recipes/categories/remove/<catid>', methods=['DELETE'])
@limiter.limit(Config.DEFAULT_RATE_LIMIT)
@jwt_required()
# If provided token in Authorization header is an access_token, it will fail with 401 Unauthorized
def apiCategoriesRemove(catid):
    if app.config.get('API_ENABLED', True):
        # Check if there is a request body (there should be none)
        if request.data:
            return jsonify({"message": "Request body is not allowed"}), 400
        app_name = request.headers.get('X-App-Name')
        app_key = request.headers.get('X-App-Key')
        if app.config.get('REQUIRE_HEADERS', True):
            # Require app name to match
            if app_name is None or app_name.lower() != 'tamari':
                return jsonify({"message": "app name is missing or incorrect"}), 401
            # Check if the provided app_key matches the one in the configuration
            if not secrets.compare_digest(app_key, app.config.get('APP_KEY')):
                return jsonify({"message": "Invalid app_key"}), 401
        # Get the identity of the user from the refresh token
        current_user = get_jwt_identity()
        user = User.query.filter_by(id=current_user).first_or_404()
        if user:
            category = Category.query.filter_by(hex_id=catid, user_id=current_user).first()
            recipes = user.recipes.all()
            if category is None or category.user_id != current_user.id:
                return jsonify(message="Category does not exist or you do not have permission to remove it."), 400
            if category.label == 'Miscellaneous':
                return jsonify(message="Miscellaneous cannot be deleted because it is the default category."), 400
            for recipe in recipes:
                if recipe.category == category.label:
                    recipe.category = 'Miscellaneous'
            db.session.delete(category)
            db.session.commit()
            return jsonify(message="success"), 200
        else:
            return jsonify(message="User not found"), 400
    else:
        return jsonify({"message": "API is disabled"}), 503
     
# Used to validate base64 encoded photos uploaded by users to RecipeAdd and RecipeEdit API routes
def validate_image(stream):
    header = stream.read(512)
    stream.seek(0)
    format = imghdr.what(None, header)
    if not format:
        return None
    return '.' + format     
    
@bp.route('/api/my-recipes/recipe/add', methods=['POST'])
@limiter.limit(Config.DEFAULT_RATE_LIMIT)
@jwt_required()
# If provided token in Authorization header is an access_token, it will fail with 401 Unauthorized
def apiRecipeAdd():
    if app.config.get('API_ENABLED', True):
        data = request.get_json()
        app_name = request.headers.get('X-App-Name')
        app_key = request.headers.get('X-App-Key')
        title = data.get('title')
        category = data.get('category')
        photo = data.get('photo')
        description = data.get('description')
        url = data.get('url')
        servings = data.get('servings')
        prep_time = data.get('prep_time')
        cook_time = data.get('cook_time')
        total_time = data.get('total_time')
        ingredients = data.get('ingredients')
        instructions = data.get('instructions')
        if app.config.get('REQUIRE_HEADERS', True):
            # Require app name to match
            if app_name is None or app_name.lower() != 'tamari':
                return jsonify({"message": "app name is missing or incorrect"}), 401
            # Check if the provided app_key matches the one in the configuration
            if not secrets.compare_digest(app_key, app.config.get('APP_KEY')):
                return jsonify({"message": "Invalid app_key"}), 401
        # Verify that JSON is valid (no double quotes or unrecognized keys)
        try:
            for key, value in data.items():
                if isinstance(value, str) and '"' in value:
                    return jsonify(message=f"Invalid value in key '{key}': double quotes are not allowed"), 400
        except:
            return jsonify(message="Invalid JSON format"), 400
        allowed_keys = {'title', 'category', 'photo', 'description', 'url', 'servings',
            'prep_time', 'cook_time', 'total_time', 'ingredients', 'instructions'}
        if not set(data.keys()).issubset(allowed_keys):
            invalid_keys = set(data.keys()) - allowed_keys
            return jsonify(message=f"Unrecognized keys: {', '.join(invalid_keys)}"), 400
        # Get the identity of the user from the refresh token
        current_user = get_jwt_identity()
        user = User.query.filter_by(id=current_user).first_or_404()
        if user:
            hex_valid = 0
            while hex_valid == 0:
                hex_string = secrets.token_hex(4)
                hex_exist = Recipe.query.filter_by(hex_id=hex_string).first()
                if hex_exist is None:
                    hex_valid = 1
            # List is used to validate submitted data
            dis_chars = {'<', '>', '{', '}', '/*', '*/', ';'}
            if not title:
                return jsonify(message="Title is required."), 400
            if len(title) > 80:
                return jsonify(message="Title must be 80 characters or less."), 400
            if any(char in dis_chars for char in title):
                return jsonify(message="Title may not include special characters."), 400
            categories = user.categories.order_by(Category.label).all()
            cats = []
            for cat in categories:
                curr_cat = cat.label
                cats.append(curr_cat)
            if "Miscellaneous" not in cats:
                cats.append("Miscallaneous")
            if not category:
                return jsonify(message="Category is required."), 400
            if category not in cats:
                return jsonify(message="Specified category not found."), 400
            if description and len(description) > 500:
                return jsonify(message="Description must be 500 characters or less."), 400
            if description and any(char in dis_chars for char in description):
                return jsonify(message="Description may not include special characters."), 400
            if url and len(url) > 200:
                return jsonify(message="URL must be 200 characters or less."), 400
            if url and any(char in dis_chars for char in url):
                return jsonify(message="URL may not include special characters."), 400
            if servings:
                try:
                    servings = int(servings)
                except:
                    return jsonify(message="Servings must be an integer."), 400
            if prep_time:
                try:
                    prep_time = int(prep_time)
                except:
                    return jsonify(message="Prep Time must be an integer."), 400
            if cook_time:
                try:
                    cook_time = int(cook_time)
                except:
                    return jsonify(message="Cook Time must be an integer."), 400
            if total_time:
                try:
                    total_time = int(total_time)
                except:
                    return jsonify(message="Total Time must be an integer."), 400
            if not ingredients:
                return jsonify(message="Ingredients are required."), 400
            if not isinstance(ingredients, list):
                return jsonify(message="Ingredients must be an array."), 400
            ingredients_length = 0
            ingredients_string = ""
            for ingredient in ingredients:
                ingredients_length += len(ingredient)
                ingredients_string += ingredient
                ingredients_string += "\r\n"
                if any(char in dis_chars for char in ingredient):
                    return jsonify(message="Ingredients may not include special characters."), 400
            if ingredients_length > 2200:
                return jsonify(message="Ingredients must be 2200 characters or less."), 400
            if ingredients_length < 1:
                return jsonify(message="Ingredients are required."), 400
            if not instructions:
                return jsonify(message="Instructions are required."), 400
            if not isinstance(instructions, list):
                return jsonify(message="Instructions must be an array."), 400
            instructions_length = 0
            instructions_string = ""
            for instruction in instructions:
                instructions_length += len(instruction)
                instructions_string += instruction
                instructions_string += "\r\n"
                if any(char in dis_chars for char in instruction):
                    return jsonify(message="Instructions may not include special characters."), 400
            if instructions_length > 6600:
                return jsonify(message="Instructions must be 6600 characters or less."), 400
            if instructions_length < 1:
                return jsonify(message="Instructions are required."), 400
            defaults = ['default01.png', 'default02.png', 'default03.png', 'default04.png', 'default05.png', 'default06.png',
                'default07.png', 'default08.png', 'default09.png', 'default10.png', 'default11.png', 'default12.png',
                'default13.png', 'default14.png', 'default15.png', 'default16.png', 'default17.png', 'default18.png',
                'default19.png', 'default20.png', 'default21.png', 'default22.png', 'default23.png', 'default24.png',
                'default25.png', 'default26.png', 'default27.png']
            if photo:
                try:
                    # Pre-validation of JSON photo value
                    match = re.match(r'data:image/(png|jpg|jpeg);base64,(.*)', photo)
                    if not match:
                        return jsonify(message="Invalid image format"), 400
                    # Base64 decode and validate image
                    image_data = base64.b64decode(match.group(2))
                    image_stream = io.BytesIO(image_data)
                    validated_extension = validate_image(image_stream)
                    if not validated_extension:
                        return jsonify(message="Invalid image data"), 400
                    image = Image.open(image_stream)
                    # Generate unique filename
                    file_extension = f".{match.group(1)}"
                    hex_valid2 = 0
                    while hex_valid2 == 0:
                        hex_string2 = secrets.token_hex(8)
                        hex_exist2 = Recipe.query.filter(Recipe.photo.contains(hex_string2)).first()
                        file_path = os.path.join(app.config['UPLOAD_FOLDER'], hex_string2 + file_extension)
                        if hex_exist2 is None and not os.path.exists(file_path):
                            hex_valid2 = 1
                    new_file = hex_string2 + file_extension
                    if file_extension not in app.config['UPLOAD_EXTENSIONS']:
                        return "Invalid image extension", 400
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
                except (base64.binascii.Error, IOError):
                    return jsonify(message="Error invalid image data"), 400
            else:
                new_file = random.choice(defaults)
            recipe = Recipe(hex_id=hex_string, title=title, category=category, photo=new_file,
                description=description, url=url, servings=servings, prep_time=prep_time, cook_time=cook_time,
                total_time=total_time, ingredients=ingredients_string, instructions=instructions_string, favorite=0,
                public=0, user_id=current_user)
            # Add recipe to database
            db.session.add(recipe)
            db.session.commit()
            return jsonify(message="Success")
        else:
            return jsonify(message="User not found"), 400
    else:
        return jsonify({"message": "API is disabled"}), 503
     
@bp.route('/api/my-recipes/recipe/<hexid>', methods=['GET'])
@limiter.limit(Config.DEFAULT_RATE_LIMIT)
@jwt_required()
# If provided token in Authorization header is an access_token, it will fail with 401 Unauthorized
def apiRecipeDetail(hexid):
    if app.config.get('API_ENABLED', True):
        # Check if there is a request body (there should be none)
        if request.data:
            return jsonify({"message": "Request body is not allowed"}), 400
        app_name = request.headers.get('X-App-Name')
        app_key = request.headers.get('X-App-Key')
        if app.config.get('REQUIRE_HEADERS', True):
            # Require app name to match
            if app_name is None or app_name.lower() != 'tamari':
                return jsonify({"message": "app name is missing or incorrect"}), 401
            # Check if the provided app_key matches the one in the configuration
            if not secrets.compare_digest(app_key, app.config.get('APP_KEY')):
                return jsonify({"message": "Invalid app_key"}), 401
        # Get the identity of the user from the refresh token
        current_user = get_jwt_identity()
        user = User.query.filter_by(id=current_user).first_or_404()
        if user:
            recipe = Recipe.query.filter_by(hex_id=hexid).first()
            # Verify that recipe belongs to current user or is public
            if not recipe:
                return jsonify(message="The requested recipe either cannot be found or you do not have permission to view it."), 404
            if recipe.user_id != current_user and recipe.public != 1:
                return jsonify(message="The requested recipe either cannot be found or you do not have permission to view it."), 404
            # Split ingredients and instructions into lists
            ingredients_list = [line.strip().replace('"', '') for line in recipe.ingredients.splitlines()]
            instructions_list = [line.strip().replace('"', '') for line in recipe.instructions.splitlines()]
            # Build response JSON
            if recipe.user_id != current_user:
                response_data = {
                    "id": recipe.hex_id,
                    "time_created": recipe.time_created,
                    "time_edited": recipe.time_edited,
                    "title": recipe.title,
                    "category": recipe.category,
                    "photo": recipe.photo,
                    "description": recipe.description,
                    "url": recipe.url,
                    "servings": recipe.servings,
                    "prep_time": recipe.prep_time,
                    "cook_time": recipe.cook_time,
                    "total_time": recipe.total_time,
                    "ingredients": ingredients_list,
                    "instructions": instructions_list
                }
            else:
                response_data = {
                    "id": recipe.hex_id,
                    "time_created": recipe.time_created,
                    "time_edited": recipe.time_edited,
                    "favorite": recipe.favorite,
                    "public": recipe.public,
                    "title": recipe.title,
                    "category": recipe.category,
                    "photo": recipe.photo,
                    "description": recipe.description,
                    "url": recipe.url,
                    "servings": recipe.servings,
                    "prep_time": recipe.prep_time,
                    "cook_time": recipe.cook_time,
                    "total_time": recipe.total_time,
                    "ingredients": ingredients_list,
                    "instructions": instructions_list
                }
            # Return response without key sorting
            response_json = json.dumps(response_data, sort_keys=False)
            response = make_response(response_json)
            response.headers['Content-Type'] = 'application/json'
            return response
        else:
            return jsonify(message="User not found"), 400
    else:
        return jsonify({"message": "API is disabled"}), 503
        