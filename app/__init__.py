from flask import Flask, request, jsonify
from config import Config
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_mail import Mail
from flask_moment import Moment
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_babel import Babel
from flask_jwt_extended import JWTManager
import logging
from logging.handlers import SMTPHandler, RotatingFileHandler
from os.path import join, dirname, realpath
import os, time, threading

UPLOAD_FOLDER = join(dirname(realpath(__file__)), 'appdata', 'recipe-photos')

def get_locale():
    return request.accept_languages.best_match(app.config['LANGUAGES'])

app = Flask(__name__)
app.config.from_object(Config)
db = SQLAlchemy(app)
migrate = Migrate(app, db, directory='app/appdata/migrations', render_as_batch=True)
login = LoginManager(app)
login.login_view = 'account.login'
mail = Mail(app)
moment = Moment(app)
babel = Babel(app, locale_selector=get_locale)
jwt = JWTManager(app)
app.config['MAX_CONTENT_LENGTH'] = 350 * 1024 * 1024
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['UPLOAD_EXTENSIONS'] = ['.png', '.jpg', '.jpeg']

limiter = Limiter(
    get_remote_address,
    app=app,
    default_limits=[Config.DEFAULT_RATE_LIMIT],
    storage_uri="memory://"
)

# Custom message for API routes when token is expired
@jwt.expired_token_loader
def custom_expired_token_callback(jwt_header, jwt_data):
    return jsonify({
        "msg": "Token is expired. Please refresh or re-authenticate."
    }), 401

# The following two functions are used to reconstruct Demo account data on an interval
from app.account.demo import reset_demo_account

def schedule_reset(interval):
    while True:
        time.sleep(interval)
        reset_demo_account()

def start_reset_scheduler():
    interval = 30 * 60  # reset demo every 30 minutes
    reset_thread = threading.Thread(target=schedule_reset, args=(interval,))
    reset_thread.daemon = True
    reset_thread.start()

start_reset_scheduler()

from app.account import bp as account_bp
app.register_blueprint(account_bp)

from app.errors import bp as errors_bp
app.register_blueprint(errors_bp)

from app.explore import bp as explore_bp
app.register_blueprint(explore_bp)

from app.mealplanner import bp as mealplanner_bp
app.register_blueprint(mealplanner_bp)

from app.myrecipes import bp as myrecipes_bp
app.register_blueprint(myrecipes_bp)

from app.shoplists import bp as shoplists_bp
app.register_blueprint(shoplists_bp)

from app.api_account import bp as api_account_bp
app.register_blueprint(api_account_bp)

from app.api_shoplists import bp as api_shoplists_bp
app.register_blueprint(api_shoplists_bp)

from app.api_mealplanner import bp as api_mealplanner_bp
app.register_blueprint(api_mealplanner_bp)

if not app.debug:
    if app.config['MAIL_SERVER']:
        auth = None
        if app.config['MAIL_USERNAME'] or app.config['MAIL_PASSWORD']:
            auth = (app.config['MAIL_USERNAME'], app.config['MAIL_PASSWORD'])
        secure = None
        if app.config['MAIL_USE_TLS']:
            secure = ()
        if app.config['ADMIN'] == '':
            mailsender = app.config['MAIL_USERNAME']
        else:
            mailsender = app.config['ADMIN']
        mail_handler = SMTPHandler(
            mailhost=(app.config['MAIL_SERVER'], app.config['MAIL_PORT']),
            fromaddr='no-reply@' + app.config['MAIL_SERVER'],
            toaddrs=mailsender, subject='Tamari Failure',
            credentials=auth, secure=secure)
        mail_handler.setLevel(logging.ERROR)
        app.logger.addHandler(mail_handler)
    if not os.path.exists('logs'):
        os.mkdir('logs')
    file_handler = RotatingFileHandler('logs/tamari.log', maxBytes=10240,
                                       backupCount=10)
    file_handler.setFormatter(logging.Formatter(
        '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'))
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)

    app.logger.setLevel(logging.INFO)
    app.logger.info('Tamari startup')

from app import models
