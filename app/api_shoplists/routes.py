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
from app.api_shoplists import bp
from config import Config

@bp.route('/api/shopping-lists', methods=['GET'])
@limiter.limit(Config.DEFAULT_RATE_LIMIT)
@jwt_required()
# If provided token in Authorization header is an access_token, it will fail with 401 Unauthorized
def apiShoppingLists():
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
        if user:
            lists = user.shop_lists.order_by(Shoplist.label).all()
            # Prepare shopping lists to be displayed as JSON
            list_data = []
            for list in lists:
                list_length = list.list_items.count()
                list_info = {
                    "hex_id": list.hex_id,
                    "label": list.label,
                    "list_items": list_length
                }
                list_data.append(list_info)
        else:
            # if user is not found, empty array will be used to create JSON response
            list_data = []
        # Return response without key sorting
        response_json = json.dumps({"shopping_lists": list_data}, sort_keys=False)
        response = make_response(response_json)
        response.headers['Content-Type'] = 'application/json'
        return response
    else:
        return jsonify({"message": "API is disabled"}), 503
        
@bp.route('/api/shopping-lists/<hexid>', methods=['GET'])
@limiter.limit(Config.DEFAULT_RATE_LIMIT)
@jwt_required()
# If provided token in Authorization header is an access_token, it will fail with 401 Unauthorized
def apiShoppingListDetail(hexid):
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
        if user:
            list = user.shop_lists.filter_by(hex_id=hexid).first()
            if list is None:
                return jsonify(message="Shopping list does not exist or you do not have permission to view it."), 400
            items = list.list_items.order_by(Listitem.item).all()
            # Prepare shopping lists to be displayed as JSON
            item_data = []
            for item in items:
                item_info = {
                    "hex_id": item.hex_id,
                    "label": item.item.replace("\r", ""),
                    "recipe": item.rec_title,
                    "complete": item.complete
                }
                item_data.append(item_info)
        else:
            # if user is not found, empty array will be used to create JSON response
            item_data = []
        # Return response without key sorting
        response_json = json.dumps({"list_items": item_data}, sort_keys=False)
        response = make_response(response_json)
        response.headers['Content-Type'] = 'application/json'
        return response
    else:
        return jsonify({"message": "API is disabled"}), 503