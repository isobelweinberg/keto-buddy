import os

from dotenv import load_dotenv

basedir = os.path.abspath(os.path.dirname(__file__))

class Config:
    load_dotenv()

    SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(basedir, 'keto.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SECRET_KEY = os.environ.get('FLASK_SECRET_KEY')
