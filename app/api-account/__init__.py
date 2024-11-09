from flask import Blueprint

bp = Blueprint('api-account', __name__)

from app.api-account import routes
