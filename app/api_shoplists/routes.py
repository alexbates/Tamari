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
                    "id": list.hex_id,
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
       
@bp.route('/api/shopping-lists/add', methods=['POST'])
@limiter.limit(Config.DEFAULT_RATE_LIMIT)
@jwt_required()
# If provided token in Authorization header is an access_token, it will fail with 401 Unauthorized
def apiAddShoppingList():
    if app.config.get('API_ENABLED', True):
        data = request.get_json()
        app_name = request.headers.get('X-App-Name')
        app_key = request.headers.get('X-App-Key')
        # POST data looks like {"list":"Miscellaneous"}
        label = data.get('list')
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
        allowed_keys = {'list'}
        if not set(data.keys()).issubset(allowed_keys):
            invalid_keys = set(data.keys()) - allowed_keys
            return jsonify(message=f"Unrecognized keys: {', '.join(invalid_keys)}"), 400
        # Get the identity of the user from the authorization token
        current_user = get_jwt_identity()
        user = User.query.filter_by(id=current_user).first_or_404()
        if user:
            lists = user.shop_lists.order_by(Shoplist.label).all()
            lists_labels = []
            for list in lists:
                curr_list = list.label
                lists_labels.append(curr_list)
            if not label:
                return jsonify(message="Shopping list label is required"), 400
            if len(label) > 20:
                return jsonify(message="The shopping list must be less than 20 characters"), 400
            if len(label) < 3:
                return jsonify(message="The shopping list must be at least 3 characters"), 400
            if label in lists_labels:
                return jsonify(message="The shopping list you entered already exists"), 400
            if len(lists_labels) > 19:
                return jsonify(message="You are limited to 20 shopping lists"), 400
            dis_chars = {'<', '>', '{', '}', '/*', '*/', ';'}
            if any(char in dis_chars for char in label):
                return jsonify(message="Must not contain special characters"), 400
            hex_valid = 0
            while hex_valid == 0:
                hex_string = secrets.token_hex(4)
                hex_exist = Shoplist.query.filter_by(hex_id=hex_string).first()
                if hex_exist is None:
                    hex_valid = 1
            # Add new list to database
            sel_list = Shoplist(hex_id=hex_string, label=label, user_id=current_user)
            db.session.add(sel_list)
            db.session.commit()
            # Build response JSON
            response_data = {
                "message": "success",
                "id": hex_string
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
        
@bp.route('/api/shopping-lists/<hexid>/add', methods=['POST'])
@limiter.limit(Config.DEFAULT_RATE_LIMIT)
@jwt_required()
# If provided token in Authorization header is an access_token, it will fail with 401 Unauthorized
def apiAddListItem(hexid):
    if app.config.get('API_ENABLED', True):
        data = request.get_json()
        app_name = request.headers.get('X-App-Name')
        app_key = request.headers.get('X-App-Key')
        # POST data looks like {"item":"yellow squash"}
        label = data.get('item')
        rec_title = data.get('rec_title')
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
        allowed_keys = {'item', 'rec_title'}
        if not set(data.keys()).issubset(allowed_keys):
            invalid_keys = set(data.keys()) - allowed_keys
            return jsonify(message=f"Unrecognized keys: {', '.join(invalid_keys)}"), 400
        # Get the identity of the user from the authorization token
        current_user = get_jwt_identity()
        user = User.query.filter_by(id=current_user).first_or_404()
        if user:
            dis_chars = {'<', '>', '{', '}', '/*', '*/', ';'}
            if any(char in dis_chars for char in label):
                return jsonify(message="Must not contain special characters"), 400
            list = user.shop_lists.filter_by(hex_id=hexid).first()
            if list is None or list.user_id != current_user:
                return jsonify(message="The requested list either cannot be found or you do not have permission to view it."), 400
            try:
                items = list.list_items.order_by(Listitem.item).all()
            except:
                items = []
            items_labels = []
            for item in items:
                curr_item = item.item
                items_labels.append(curr_item)
            if not label:
                return jsonify(message="List item is required"), 400
            if len(label) > 100:
                return jsonify(message="The list item must be less than 100 characters"), 400
            if label in items_labels:
                return jsonify(message="The list item you entered already exists"), 400
            if len(items_labels) > 99:
                return jsonify(message="You are limited to 100 items per list"), 400
            hex_valid = 0
            while hex_valid == 0:
                hex_string = secrets.token_hex(4)
                hex_exist = Listitem.query.filter_by(hex_id=hex_string).first()
                if hex_exist is None:
                    hex_valid = 1
            # Add new list to database
            sel_item = Listitem(hex_id=hex_string, item=label, user_id=current_user, complete=0, list_id=list.id)
            db.session.add(sel_item)
            db.session.commit()
            # Build response JSON
            response_data = {
                "message": "success",
                "id": hex_string
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
        
@bp.route('/api/shopping-lists/item/<hexid>/mark', methods=['PUT'])
@limiter.limit(Config.DEFAULT_RATE_LIMIT)
@jwt_required()
# If provided token in Authorization header is an access_token, it will fail with 401 Unauthorized
def apiMarkItem(hexid):
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
            listitem = Listitem.query.filter_by(hex_id=hexid).first()
            list = Shoplist.query.filter_by(id=listitem.list_id).first()
            if listitem is None or listitem.user_id != current_user:
                return jsonify(message="The requested list item either cannot be found or you do not have permission to modify it."), 400
            try:
                if listitem.complete == 0:
                    listitem.complete = 1
                    db.session.commit()
                else:
                    listitem.complete = 0
                    db.session.commit()
                return jsonify(message="Success")
            except:
                return jsonify(message="Error")
        else:
            return jsonify(message="User not found"), 400
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
                    "id": item.hex_id,
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