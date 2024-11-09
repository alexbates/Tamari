from flask import Blueprint

bp = Blueprint('api_myrecipes', __name__)

from app.api_myrecipes import routes
