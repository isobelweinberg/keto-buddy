import os

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_wtf.csrf import CSRFProtect
from flask_login import LoginManager
from dotenv import load_dotenv

from config import Config

load_dotenv()

db = SQLAlchemy()
csrf = CSRFProtect()
login_manager = LoginManager()
login_manager.login_view = 'main.login'  # Redirect to login page if not authenticated
login_manager.login_message = "Please log in to access this page."
login_manager.login_message_category = "warning"

def create_app():
    app = Flask(__name__)

    app.config.from_object(Config)
    app.config['SECRET_KEY'] = os.environ.get('FLASK_SECRET_KEY')
    
    db.init_app(app)
    csrf.init_app(app)
    login_manager.init_app(app)

    from .routes import main
    app.register_blueprint(main)

    @login_manager.user_loader
    def load_user(user_id):
        from app.models import User
        return User.query.get(int(user_id))

    return app
