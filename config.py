import os

from dotenv import load_dotenv

basedir = os.path.abspath(os.path.dirname(__file__))

class Config:
    load_dotenv()

    db_uri = os.environ.get('DATABASE_URL')

    if db_uri and db_uri.startswith("postgres://"):
        db_uri = db_uri.replace("postgres://", "postgresql://", 1)

    SQLALCHEMY_DATABASE_URI = db_uri or 'sqlite:///' + os.path.join(basedir, 'keto.db')

    # SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(basedir, 'keto.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SECRET_KEY = os.environ.get('FLASK_SECRET_KEY')
