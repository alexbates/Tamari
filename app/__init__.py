from flask import Flask
from config import Config
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_mail import Mail
from flask_moment import Moment
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import logging
from logging.handlers import SMTPHandler, RotatingFileHandler
from os.path import join, dirname, realpath
import os

UPLOAD_FOLDER = join(dirname(realpath(__file__)), 'appdata', 'recipe-photos')

app = Flask(__name__)
app.config.from_object(Config)
db = SQLAlchemy(app)
migrate = Migrate(app, db, directory='app/appdata/migrations', render_as_batch=True)
login = LoginManager(app)
login.login_view = 'account.login'
mail = Mail(app)
moment = Moment(app)
app.config['MAX_CONTENT_LENGTH'] = 350 * 1024 * 1024
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['UPLOAD_EXTENSIONS'] = ['.png', '.jpg', '.jpeg']

limiter = Limiter(
    get_remote_address,
    app=app,
    default_limits=[Config.DEFAULT_RATE_LIMIT],
    storage_uri="memory://"
)

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
