from flask import Blueprint

bp = Blueprint('api_account', __name__)

from app.api_account import routes
