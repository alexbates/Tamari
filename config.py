import os
basedir = os.path.abspath(os.path.dirname(__file__))

class Config(object):
    SECRET_KEY = os.environ.get('SECRET_KEY') or '8AFD4E1BC23A6F927E5B'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'sqlite:///' + os.path.join(basedir, 'app/appdata/app.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    MAIL_SERVER = os.environ.get('MAIL_SERVER')
    MAIL_PORT = int(os.environ.get('MAIL_PORT') or 25)
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS') is not None
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    # ADMIN is the sender email if mail is configured via environment variables
    # If this is left blank, Tamari will use MAIL_USERNAME as the sender email
    # Example: ADMIN = 'default@tamariapp.com'
    ADMIN = ''
    # for my recipes > all recipes and my recipes > favorites
    MAIN_RECIPES_PER_PAGE = 100
    CAT_RECIPES_PER_PAGE = 50
    EXPLORE_RECIPES_PER_PAGE = 60
    # for dynamic loading of images, distance from viewport that image will start to load
    DYNAMIC_ROOT_MARGIN = '120px'
