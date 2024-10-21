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
from app.api import bp
from config import Config

@bp.route('/api/user/authenticate', methods=['POST'])
@limiter.limit(Config.DEFAULT_RATE_LIMIT)
def apiAuthenticate():
    if app.config.get('API_ENABLED', True):
        # Call rate limited function to effectively impose rate limit on login attempts
        if rate_limited_login():
            data = request.get_json()
            app_name = data.get('app_name')
            app_key = data.get('app_key')
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
