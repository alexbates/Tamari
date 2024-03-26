from flask import Blueprint

bp = Blueprint('account', __name__)

from app.account import routes
