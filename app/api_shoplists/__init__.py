from flask import Blueprint

bp = Blueprint('api_shoplists', __name__)

from app.api_shoplists import routes
