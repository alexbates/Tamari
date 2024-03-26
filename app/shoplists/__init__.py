from flask import Blueprint

bp = Blueprint('shoplists', __name__)

from app.shoplists import routes
