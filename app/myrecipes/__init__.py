from flask import Blueprint

bp = Blueprint('myrecipes', __name__)

from app.myrecipes import routes
