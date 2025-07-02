import os

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_wtf.csrf import CSRFProtect
from dotenv import load_dotenv

from config import Config

db = SQLAlchemy()

load_dotenv()

def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = os.environ.get('FLASK_SECRET_KEY')
    CSRFProtect(app)
    app.config.from_object(Config)
    db.init_app(app)

    from .routes import main
    app.register_blueprint(main)

    return app
