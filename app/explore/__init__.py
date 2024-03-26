from flask import Blueprint

bp = Blueprint('explore', __name__)

from app.explore import routes
