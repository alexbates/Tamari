from flask import Blueprint

bp = Blueprint('api-shoplists', __name__)

from app.api-shoplists import routes
