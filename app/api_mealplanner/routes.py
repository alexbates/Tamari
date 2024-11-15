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
from app.api_mealplanner import bp
from config import Config

@bp.route('/api/meal-planner/all', methods=['GET'])
@limiter.limit(Config.DEFAULT_RATE_LIMIT)
@jwt_required()
# If provided token in Authorization header is an access_token, it will fail with 401 Unauthorized
def apiMealPlannerAll():
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
        # Get the identity of the user from the authorization token
        current_user = get_jwt_identity()
        user = User.query.filter_by(id=current_user).first_or_404()
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 1000, type=int)
        sort = request.args.get('sort', 'desc', type=str).lower()
        valid_sort_options = ['desc', 'asc']
        if sort not in valid_sort_options:
            return jsonify({"message": "Specified sort option is not recognized"}), 400
        if user:
            plannedmeals = user.planned_meals.all()
            # Create 2D array to store recipe info, it will somewhat mirror plannedmeals
            # Structure of array:
            # 1 - Recipe title
            # 2 - Recipe category
            # 3 - Recipe hex_id
            # 4 - Meal date
            # 5 - Meal hex_id
            w2, h2 = 5, len(plannedmeals)
            recdetails = [[0 for x in range(w2)] for y in range(h2)]
            mealiteration = 0
            for meal in plannedmeals:
                recipe = Recipe.query.filter_by(id=meal.recipe_id).first()
                try:
                    recdetails[mealiteration][0] = recipe.title
                except:
                    recdetails[mealiteration][0] = "Unknown Recipe"
                try:
                    recdetails[mealiteration][1] = recipe.category
                except:
                    recdetails[mealiteration][1] = "Miscellaneous"
                try:
                    recdetails[mealiteration][2] = recipe.hex_id
                except:
                    recdetails[mealiteration][2] = "a3notfound"
                recdetails[mealiteration][3] = meal.date
                recdetails[mealiteration][4] = meal.hex_id
                mealiteration += 1
            # Prepare categories to be displayed as JSON
            mealplan_data = []
            for meal in recdetails:
                # If recipe is not found on query of Recipe table, don't add it to JSON
                if meal[2] == "a3notfound":
                    continue
                mealplan_info = {
                    "id": meal[4],
                    "date": meal[3],
                    "recipe_id": meal[2],
                    "recipe_title": meal[0],
                    "recipe_category": meal[1]
                }
                mealplan_data.append(mealplan_info)
            # Sort events by date, either descending (default) or ascending
            if sort == "asc":
                mealplan_data = sorted(mealplan_data, key=lambda mealplan: mealplan["date"])
            else:
                mealplan_data = sorted(mealplan_data, key=lambda mealplan: mealplan["date"], reverse=True)
            # Calculate the start and end indices for pagination
            start_index = (page - 1) * per_page
            end_index = start_index + per_page
            # Paginate the mealplan_data array
            mealplan_data = mealplan_data[start_index:end_index]
        else:
            # if user is not found, empty array will be used to create JSON response
            mealplan_data = []
        # Return response without key sorting
        response_json = json.dumps({"meals": mealplan_data}, sort_keys=False)
        response = make_response(response_json)
        response.headers['Content-Type'] = 'application/json'
        return response
    else:
        return jsonify({"message": "API is disabled"}), 503
        
@bp.route('/api/meal-planner/upcoming', methods=['GET'])
@limiter.limit(Config.DEFAULT_RATE_LIMIT)
@jwt_required()
# If provided token in Authorization header is an access_token, it will fail with 401 Unauthorized
def apiMealPlannerUpcoming():
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
        # Get the identity of the user from the authorization token
        current_user = get_jwt_identity()
        user = User.query.filter_by(id=current_user).first_or_404()
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 1000, type=int)
        sort = request.args.get('sort', 'desc', type=str).lower()
        valid_sort_options = ['desc', 'asc']
        if sort not in valid_sort_options:
            return jsonify({"message": "Specified sort option is not recognized"}), 400
        if user:
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
            # Structure of array:
            # 1 - Recipe title
            # 2 - Recipe category
            # 3 - Recipe hex_id
            # 4 - Meal date
            # 5 - Meal hex_id
            w2, h2 = 5, len(mealsinmonth)
            recdetails = [[0 for x in range(w2)] for y in range(h2)]
            mealiteration = 0
            for meal in mealsinmonth:
                recipe = Recipe.query.filter_by(id=meal.recipe_id).first()
                try:
                    recdetails[mealiteration][0] = recipe.title
                except:
                    recdetails[mealiteration][0] = "Unknown Recipe"
                try:
                    recdetails[mealiteration][1] = recipe.category
                except:
                    recdetails[mealiteration][1] = "Miscellaneous"
                try:
                    recdetails[mealiteration][2] = recipe.hex_id
                except:
                    recdetails[mealiteration][2] = "a3notfound"
                recdetails[mealiteration][3] = meal.date
                recdetails[mealiteration][4] = meal.hex_id
                mealiteration += 1
            # Prepare categories to be displayed as JSON
            mealplan_data = []
            for meal in recdetails:
                # If recipe is not found on query of Recipe table, don't add it to JSON
                if meal[2] == "a3notfound":
                    continue
                mealplan_info = {
                    "id": meal[4],
                    "date": meal[3],
                    "recipe_id": meal[2],
                    "recipe_title": meal[0],
                    "recipe_category": meal[1]
                }
                mealplan_data.append(mealplan_info)
            # Sort events by date, either descending (default) or ascending
            if sort == "asc":
                mealplan_data = sorted(mealplan_data, key=lambda mealplan: mealplan["date"])
            else:
                mealplan_data = sorted(mealplan_data, key=lambda mealplan: mealplan["date"], reverse=True)
            # Calculate the start and end indices for pagination
            start_index = (page - 1) * per_page
            end_index = start_index + per_page
            # Paginate the mealplan_data array
            mealplan_data = mealplan_data[start_index:end_index]
        else:
            # if user is not found, empty array will be used to create JSON response
            mealplan_data = []
        # Return response without key sorting
        response_json = json.dumps({"meals": mealplan_data}, sort_keys=False)
        response = make_response(response_json)
        response.headers['Content-Type'] = 'application/json'
        return response
    else:
        return jsonify({"message": "API is disabled"}), 503