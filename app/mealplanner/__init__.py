from flask import Blueprint

bp = Blueprint('mealplanner', __name__)

from app.mealplanner import routes
