from flask import render_template, flash, redirect, url_for, request, send_from_directory, jsonify, make_response
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
            if app_name.lower() != 'tamari':
                return jsonify({"message": "app_name not recognized"}), 401
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
            access_token = create_access_token(identity=user.id)
            refresh_token = create_refresh_token(identity=user.id)
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
        if app_name.lower() != 'tamari':
            return jsonify({"message": "app_name not recognized"}), 401
        # Check if the provided app_key matches the one in the configuration
        if app_key != app.config.get('APP_KEY'):
            return jsonify({"message": "Invalid app_key"}), 401
        # Get the identity of the user from the refresh token
        current_user = get_jwt_identity()
        # Create a new access token
        new_access_token = create_access_token(identity=current_user)
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
        if app_name.lower() != 'tamari':
            return jsonify({"message": "app_name not recognized"}), 401
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
        else:
            u_email = None
            u_reg_time = None
            u_last_time = None
            rec_count = 0
        # Build response JSON
        response_data = {
            "email": u_email,
            "register_time": u_reg_time,
            "last_visited": u_last_time,
            "recipes": rec_count
        }
        # Return response without key sorting
        response_json = json.dumps(response_data, sort_keys=False)
        response = make_response(response_json)
        response.headers['Content-Type'] = 'application/json'
        return response
    else:
        return jsonify({"message": "API is disabled"}), 503