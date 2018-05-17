import os
import base64
from dotenv import load_dotenv

basedir = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(basedir, '.env'))

class Config(object):
    # loads secret key from system with string fallback
    SECRET_KEY = os.environ.get('SECRET_KEY')

    # loads database location from system or uses sqlite default file
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'sqlite:///' + os.path.join(basedir, 'app.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Use below lines to read email variables from system

    MAIL_SERVER = os.environ.get('MAIL_SERVER')
    MAIL_PORT = int(os.environ.get('MAIL_PORT') or 25)
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS') is not None
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')

    # Manual email settings
    ADMINS = ['skalappservice@gmail.com']

    # max posts per page for pagination
    POSTS_PER_PAGE = 15

    # supported languages
    LANGUAGES = ['en', 'es', 'fr']
