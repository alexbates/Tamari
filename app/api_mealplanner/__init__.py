from flask import Blueprint

bp = Blueprint('api_mealplanner', __name__)

from app.api_mealplanner import routes
