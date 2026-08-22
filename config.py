import os
from datetime import timedelta
from secretkeys import getSecret
basedir = os.path.abspath(os.path.dirname(__file__))

class Config(object):
    SECRET_KEY = getSecret('SECRET_KEY')
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'sqlite:///' + os.path.join(basedir, 'app/appdata/app.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    LANGUAGES = ['en', 'es', 'de', 'zh', 'fr', 'ru', 'ja']
    # Debug Mode
    # Disabled by default, this is only for development, change False to True to enable
    DEBUG_MODE = os.environ.get('DEBUG_MODE', 'False') == 'True'
    # Reverse Proxy Support
    # Disabled by default, change False to True to enable
    # Only enable when users are accessing Tamari through a reverse proxy, instead of directly
    # When enabled, Tamari trusts the client IP address provided by reverse proxy (making rate limiting possible)
    # Do not enable if users can connect directly to Gunicorn, because they could spoof their IP address
    USE_PROXY_FIX = os.environ.get('USE_PROXY_FIX', 'False') == 'True'
    # Public URL
    # Optional, but required if using email verification or password reset emails
    # Must include http:// or https://, such as https://tamari.example.com
    PUBLIC_URL = os.environ.get('PUBLIC_URL')
    # XSS Protection for cookies, leave these as default
    SESSION_COOKIE_HTTPONLY = True
    REMEMBER_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    REMEMBER_COOKIE_SAMESITE = 'Lax'
    # Secure Cookie Support
    # Disable by default, change False to True to enable
    # If using a reverse proxy and hosting Tamari on HTTPS such as https://tamari.example.com 
    # If this is not enabled and you visit http://tamari.example.com, cookies may be sent over HTTP (a security risk)
    # This is an optional hardening step
    SECURE_COOKIES = os.environ.get('SECURE_COOKIES', 'False') == 'True'
    SESSION_COOKIE_SECURE = SECURE_COOKIES
    REMEMBER_COOKIE_SECURE = SECURE_COOKIES
    # Mail server settings
    MAIL_SERVER = os.environ.get('MAIL_SERVER')
    MAIL_PORT = int(os.environ.get('MAIL_PORT') or 25)
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS') is not None
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    # ADMIN is the sender email if mail is configured via environment variables
    # If this is left blank, Tamari will use MAIL_USERNAME as the sender email
    # Example: ADMIN = 'default@tamariapp.com'
    ADMIN = ''
    # Register page, optionally disable new registrations
    # To disable registration, change "('REG_DISABLED', 'False')" to "('REG_DISABLED', 'True')"
    # or set environment variable with Docker run command
    REGISTRATION_DISABLED = os.environ.get('REG_DISABLED', 'False') == 'True'
    # Registration Email Verification (not required by default, sends email link to set password)
    # To enable email verification, change "('REGISTRATION_VERIFICATION_REQUIRED', 'False')" to 
    # "('REGISTRATION_VERIFICATION_REQUIRED', 'True')"
    REGISTRATION_VERIFICATION_REQUIRED = os.environ.get('REGISTRATION_VERIFICATION_REQUIRED', 'False') == 'True'
    # For My Recipes > All Recipes and My Recipes > Favorites
    MAIN_RECIPES_PER_PAGE = 100
    ADV_SEARCH_RECIPES_PER_PAGE = 50
    CAT_RECIPES_PER_PAGE = 50
    EXPLORE_RECIPES_PER_PAGE = 32
    # For Meal Planner (Completed)
    MEAL_PLANS_PER_PAGE = 50
    # For Account History page event pagination
    ACCOUNT_EVENTS_PER_PAGE = 30
    # For dynamic loading of images
    # Distance from viewport that image will start to load in My Recipes
    DYNAMIC_ROOT_MARGIN = '120px'
    # Rate Limit Settings
    # Enabled by default
    # If you wish to disable rate limiting, set all equal to None - for example, DEFAULT_RATE_LIMIT = None
    # Note that rate limit will be multiplied by the number of gunicorn worker threads (usually 4)
    # This issue can be mitigated by used a shared storage backend like redis (configure in __init__.py)
    # Enabled examples: '1000 per minute', '25 per 10 minutes', '3 per 10 minutes', '5 per minute'
    DEFAULT_RATE_LIMIT = '1000 per minute'
    LOGIN_RATE_LIMIT = '10 per 10 minutes'
    REGISTRATION_RATE_LIMIT = '3 per 10 minutes'
    DEBUG_RATE_LIMIT = '5 per minute'
    PDF_RATE_LIMIT = '5 per minute'
    PDF_MAX_REQUEST_SIZE = 1024 * 1024
    # API CONFIGURATION (disabled by default)
    API_ENABLED = os.environ.get('API_ENABLED', 'False') == 'True'
    APP_KEY = getSecret('APP_KEY')
    # If True, X-App-Name header must have value 'tamari' and X-App-Key must equal APP_KEY
    # Default is False if env variable not set, can change ", 'False')" to ", 'True')"
    REQUIRE_HEADERS = os.environ.get('REQUIRE_HEADERS', 'False') == 'True'
    JWT_SECRET_KEY = getSecret('JWT_SECRET_KEY')
    ACCESS_TOKEN_EXPIRES = timedelta(hours=24)
    REFRESH_TOKEN_EXPIRES = timedelta(days=60)